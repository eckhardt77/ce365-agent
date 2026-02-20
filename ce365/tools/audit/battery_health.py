"""
CE365 Agent - Battery Health Detail

Lade-Zyklen, Verschleiss, Design- vs aktuelle Kapazitaet
macOS: system_profiler SPPowerDataType
Windows: powercfg /batteryreport
"""

import platform
import psutil
from typing import Dict, Any
from ce365.tools.base import AuditTool
from ce365.core.command_runner import get_command_runner


def _run_cmd(cmd: list, timeout: int = 15) -> str:
    result = get_command_runner().run_sync(cmd, timeout=timeout)
    return result.stdout if result.success else ""


class BatteryHealthTool(AuditTool):
    """Detaillierte Akku-Gesundheit pruefen"""

    @property
    def name(self) -> str:
        return "check_battery_health"

    @property
    def description(self) -> str:
        return (
            "Prueft die detaillierte Akku-Gesundheit: Lade-Zyklen, Verschleiss, "
            "Design- vs aktuelle Kapazitaet, Zustand, Temperatur. "
            "Nutze dies bei: 1) Akku haelt nicht mehr lang, "
            "2) Schneller Entladung, 3) Laptop-Kauf-Beratung, "
            "4) Akku-Tausch Empfehlung. "
            "Nur fuer Laptops/MacBooks mit Akku."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    async def execute(self, **kwargs) -> str:
        # Erst pruefen ob ueberhaupt ein Akku vorhanden
        battery = psutil.sensors_battery()
        if battery is None:
            return "ℹ️  Kein Akku erkannt — dies ist vermutlich ein Desktop-Computer."

        os_type = platform.system()
        lines = ["🔋 AKKU-GESUNDHEIT (Detailliert)", "=" * 50, ""]

        # Basis-Info via psutil
        lines.append(f"Ladezustand: {battery.percent:.0f}%")
        if battery.power_plugged:
            lines.append("Stromversorgung: ⚡ Netzbetrieb")
        else:
            if battery.secsleft > 0:
                hours = battery.secsleft // 3600
                mins = (battery.secsleft % 3600) // 60
                lines.append(f"Stromversorgung: 🔋 Akku ({hours}h {mins}m verbleibend)")
            else:
                lines.append("Stromversorgung: 🔋 Akku")
        lines.append("")

        # Plattformspezifische Details
        if os_type == "Darwin":
            lines.extend(self._macos_details())
        elif os_type == "Windows":
            lines.extend(self._windows_details())

        return "\n".join(lines)

    def _macos_details(self) -> list:
        lines = []

        output = _run_cmd(["system_profiler", "SPPowerDataType"], timeout=10)
        if not output:
            lines.append("⚠️  Konnte Akku-Details nicht lesen")
            return lines

        # Wichtige Werte extrahieren
        info = {}
        for line in output.splitlines():
            stripped = line.strip()
            if ":" in stripped:
                key, _, value = stripped.partition(":")
                info[key.strip().lower()] = value.strip()

        # Lade-Zyklen
        cycle_count = info.get("cycle count", "")
        if cycle_count:
            try:
                cycles = int(cycle_count)
                lines.append(f"Lade-Zyklen: {cycles}")
                if cycles < 300:
                    lines.append(f"   ✅ Sehr gut (< 300)")
                elif cycles < 500:
                    lines.append(f"   🟢 Gut (< 500)")
                elif cycles < 800:
                    lines.append(f"   🟡 Mittel (< 800)")
                elif cycles < 1000:
                    lines.append(f"   🟠 Hoch — Akku-Tausch bald empfohlen")
                else:
                    lines.append(f"   🔴 Sehr hoch — Akku-Tausch empfohlen")
            except ValueError:
                lines.append(f"Lade-Zyklen: {cycle_count}")

        # Zustand
        condition = info.get("condition", "")
        if condition:
            if condition.lower() == "normal":
                lines.append(f"Zustand: ✅ {condition}")
            elif "replace" in condition.lower():
                lines.append(f"Zustand: 🔴 {condition} — Tausch empfohlen!")
            elif "service" in condition.lower():
                lines.append(f"Zustand: 🟠 {condition} — Service empfohlen")
            else:
                lines.append(f"Zustand: {condition}")

        # Kapazitaeten
        max_capacity = info.get("maximum capacity", "")
        if max_capacity:
            lines.append(f"Maximale Kapazitaet: {max_capacity}")

        design_capacity = info.get("design capacity", "")
        full_charge = info.get("full charge capacity (mah)", info.get("full charge capacity", ""))
        design_cap = info.get("design capacity (mah)", info.get("design capacity", ""))

        if full_charge and design_cap:
            try:
                full = int(full_charge.replace(" mAh", "").replace(",", ""))
                design = int(design_cap.replace(" mAh", "").replace(",", ""))
                if design > 0:
                    health_pct = (full / design) * 100
                    lines.append(f"Aktuelle Kapazitaet: {full} mAh")
                    lines.append(f"Design-Kapazitaet: {design} mAh")
                    lines.append(f"Gesundheit: {health_pct:.1f}%")

                    if health_pct >= 80:
                        lines.append(f"   ✅ Akku ist in gutem Zustand")
                    elif health_pct >= 60:
                        lines.append(f"   🟡 Akku zeigt Verschleiss")
                    else:
                        lines.append(f"   🔴 Akku stark verschlissen — Tausch empfohlen")
            except (ValueError, ZeroDivisionError):
                pass

        # Charging/Voltage
        voltage = info.get("voltage (mv)", "")
        if voltage:
            lines.append(f"Spannung: {voltage} mV")

        charging = info.get("charging", "")
        if charging:
            lines.append(f"Laedt: {'Ja' if charging.lower() == 'yes' else 'Nein'}")

        return lines

    def _windows_details(self) -> list:
        lines = []

        # PowerShell WMI Battery-Info
        ps_cmd = (
            "Get-WmiObject Win32_Battery 2>$null | "
            "ForEach-Object { "
            "\"$($_.DesignCapacity)|$($_.FullChargeCapacity)|"
            "$($_.EstimatedChargeRemaining)|$($_.BatteryStatus)|"
            "$($_.DesignVoltage)|$($_.Name)|$($_.Status)\" }"
        )
        output = _run_cmd(["powershell", "-Command", ps_cmd], timeout=10)

        if output:
            for line in output.splitlines():
                parts = line.strip().split("|")
                if len(parts) >= 5:
                    design_cap = parts[0].strip()
                    full_charge = parts[1].strip()
                    charge_remaining = parts[2].strip()
                    bat_status = parts[3].strip()
                    voltage = parts[4].strip()
                    name = parts[5].strip() if len(parts) > 5 else ""
                    status = parts[6].strip() if len(parts) > 6 else ""

                    if name:
                        lines.append(f"Akku: {name}")
                    if status:
                        if status.lower() == "ok":
                            lines.append(f"Status: ✅ {status}")
                        else:
                            lines.append(f"Status: ⚠️  {status}")

                    # Kapazitaetsvergleich
                    try:
                        design = int(design_cap) if design_cap else 0
                        full = int(full_charge) if full_charge else 0
                        if design > 0 and full > 0:
                            health_pct = (full / design) * 100
                            lines.append(f"Design-Kapazitaet: {design} mWh")
                            lines.append(f"Aktuelle Kapazitaet: {full} mWh")
                            lines.append(f"Gesundheit: {health_pct:.1f}%")

                            if health_pct >= 80:
                                lines.append(f"   ✅ Akku ist in gutem Zustand")
                            elif health_pct >= 60:
                                lines.append(f"   🟡 Akku zeigt Verschleiss")
                            else:
                                lines.append(f"   🔴 Akku stark verschlissen — Tausch empfohlen")
                    except (ValueError, ZeroDivisionError):
                        pass

                    if voltage:
                        lines.append(f"Spannung: {voltage} mV")
        else:
            lines.append("⚠️  Detaillierte Akku-Informationen nicht verfuegbar")
            lines.append("   Tipp: powercfg /batteryreport erstellt einen ausfuehrlichen Bericht")

        # Lade-Zyklen (Windows — ueber Battery Report)
        cycle_cmd = (
            "Get-WmiObject -Namespace 'root\\wmi' MSBatteryRuntime 2>$null | "
            "Select-Object -First 1 | "
            "ForEach-Object { $_.EstimatedRuntime }"
        )
        # Note: Windows hat keinen direkten Zugang zu Zyklen wie macOS
        # powercfg /batteryreport waere der beste Weg, aber erzeugt HTML
        lines.append("")
        lines.append("ℹ️  Fuer detaillierten Akku-Report (mit Zyklen):")
        lines.append("   powercfg /batteryreport")
        lines.append("   → Erstellt C:\\WINDOWS\\system32\\battery-report.html")

        return lines

"""
CE365 Agent - Disk Health (S.M.A.R.T.)

S.M.A.R.T. Status, Festplatten-Gesundheit, Bad Sectors
macOS: smartctl (via Homebrew) oder diskutil
Windows: wmic diskdrive, PowerShell Get-PhysicalDisk
"""

import platform
import subprocess
from typing import Dict, Any
from ce365.tools.base import AuditTool


def _run_cmd(cmd: list, timeout: int = 15) -> str:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.stdout.strip()
    except Exception:
        return ""


class DiskHealthTool(AuditTool):
    """S.M.A.R.T. Status und Festplatten-Gesundheit pruefen"""

    @property
    def name(self) -> str:
        return "check_disk_health"

    @property
    def description(self) -> str:
        return (
            "Prueft die Festplatten-Gesundheit via S.M.A.R.T. und System-Tools. "
            "Nutze dies bei: 1) Verdacht auf Festplatten-Defekt, 2) Langsame I/O, "
            "3) Regelmaessige Wartung, 4) S.M.A.R.T. Warnungen, "
            "5) Vor Daten-Migration. "
            "Zeigt: Gesundheitsstatus, Temperatur, Betriebsstunden, Fehler-Zaehler."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    async def execute(self, **kwargs) -> str:
        os_type = platform.system()
        lines = ["💿 FESTPLATTEN-GESUNDHEIT", "=" * 50, ""]

        if os_type == "Darwin":
            lines.extend(self._check_macos())
        elif os_type == "Windows":
            lines.extend(self._check_windows())
        else:
            lines.append("❌ Nicht unterstuetztes Betriebssystem")

        return "\n".join(lines)

    def _check_macos(self) -> list:
        lines = []

        # 1. diskutil info fuer alle Laufwerke
        list_output = _run_cmd(["diskutil", "list"], timeout=10)
        if list_output:
            # Nur physische Laufwerke extrahieren
            for line in list_output.splitlines():
                if "/dev/disk" in line and "physical" in line.lower():
                    disk_id = line.split()[0]  # z.B. /dev/disk0
                    lines.extend(self._check_macos_disk(disk_id))
                    lines.append("")

        # Fallback: Hauptlaufwerk pruefen
        if not lines:
            lines.extend(self._check_macos_disk("/dev/disk0"))

        # 2. smartctl wenn verfuegbar (Homebrew: brew install smartmontools)
        smartctl_output = _run_cmd(["smartctl", "-a", "/dev/disk0"], timeout=10)
        if smartctl_output and "SMART" in smartctl_output:
            lines.append("")
            lines.append("📊 S.M.A.R.T. Details (smartctl):")
            for line in smartctl_output.splitlines():
                stripped = line.strip()
                # Relevante S.M.A.R.T. Attribute
                if any(key in stripped.lower() for key in [
                    "overall-health", "health status", "temperature",
                    "power_on_hours", "power on hours", "reallocated",
                    "current_pending", "offline_uncorrectable",
                    "percentage used", "data units read", "data units written",
                    "media_wearout", "wear_leveling",
                ]):
                    lines.append(f"   {stripped}")
        elif not smartctl_output:
            lines.append("")
            lines.append("ℹ️  Fuer detaillierte S.M.A.R.T.-Daten: brew install smartmontools")

        return lines

    def _check_macos_disk(self, disk_id: str) -> list:
        lines = []
        info = _run_cmd(["diskutil", "info", disk_id], timeout=10)
        if not info:
            return [f"   ❌ Konnte {disk_id} nicht lesen"]

        disk_name = ""
        disk_size = ""
        disk_type = ""
        smart_status = ""

        for line in info.splitlines():
            stripped = line.strip()
            if stripped.startswith("Device / Media Name:"):
                disk_name = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("Disk Size:"):
                disk_size = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("Solid State:"):
                is_ssd = stripped.split(":", 1)[1].strip()
                disk_type = "SSD" if is_ssd.lower() == "yes" else "HDD"
            elif stripped.startswith("SMART Status:"):
                smart_status = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("Medium Type:"):
                disk_type = stripped.split(":", 1)[1].strip()

        header = f"💾 {disk_id}"
        if disk_name:
            header += f" — {disk_name}"
        if disk_type:
            header += f" [{disk_type}]"
        lines.append(header)

        if disk_size:
            lines.append(f"   Groesse: {disk_size}")

        if smart_status:
            if smart_status.lower() in ("verified", "ok"):
                lines.append(f"   S.M.A.R.T.: ✅ {smart_status}")
            elif "fail" in smart_status.lower():
                lines.append(f"   S.M.A.R.T.: ❌ {smart_status} — SOFORT BACKUP ERSTELLEN!")
            else:
                lines.append(f"   S.M.A.R.T.: ⚠️  {smart_status}")
        else:
            lines.append("   S.M.A.R.T.: Nicht verfuegbar")

        return lines

    def _check_windows(self) -> list:
        lines = []

        # 1. PowerShell Get-PhysicalDisk (Windows 10+)
        ps_cmd = (
            "Get-PhysicalDisk | Select-Object FriendlyName, MediaType, "
            "HealthStatus, OperationalStatus, Size | "
            "ForEach-Object { "
            "\"$($_.FriendlyName)|$($_.MediaType)|$($_.HealthStatus)|"
            "$($_.OperationalStatus)|$([math]::Round($_.Size/1GB, 1))\" }"
        )
        ps_output = _run_cmd(["powershell", "-Command", ps_cmd], timeout=15)

        if ps_output:
            for line in ps_output.splitlines():
                parts = line.strip().split("|")
                if len(parts) >= 4:
                    name = parts[0].strip()
                    media_type = parts[1].strip()
                    health = parts[2].strip()
                    op_status = parts[3].strip()
                    size = parts[4].strip() if len(parts) > 4 else ""

                    header = f"💾 {name}"
                    if media_type:
                        header += f" [{media_type}]"
                    if size:
                        header += f" — {size} GB"
                    lines.append(header)

                    if health.lower() == "healthy":
                        lines.append(f"   Zustand: ✅ {health}")
                    elif "warning" in health.lower():
                        lines.append(f"   Zustand: ⚠️  {health}")
                    else:
                        lines.append(f"   Zustand: ❌ {health} — SOFORT BACKUP ERSTELLEN!")

                    lines.append(f"   Status: {op_status}")
                    lines.append("")

        # 2. S.M.A.R.T. via WMI
        wmi_cmd = (
            "Get-WmiObject -Namespace 'root\\wmi' MSStorageDriver_FailurePredictStatus 2>$null | "
            "ForEach-Object { \"$($_.InstanceName)|$($_.PredictFailure)|$($_.Reason)\" }"
        )
        wmi_output = _run_cmd(["powershell", "-Command", wmi_cmd], timeout=10)

        if wmi_output:
            lines.append("📊 S.M.A.R.T. Failure Prediction:")
            for line in wmi_output.splitlines():
                parts = line.strip().split("|")
                if len(parts) >= 2:
                    instance = parts[0].strip()[:40]
                    predict_fail = parts[1].strip().lower()
                    if predict_fail == "true":
                        lines.append(f"   ❌ {instance} — AUSFALL VORHERGESAGT!")
                        lines.append(f"      → Sofort Backup erstellen und Laufwerk ersetzen!")
                    else:
                        lines.append(f"   ✅ {instance} — Kein Ausfall vorhergesagt")

        # 3. Disk-Fehler aus Event Log
        event_cmd = (
            "Get-EventLog -LogName System -Source disk -EntryType Error -Newest 5 2>$null | "
            "ForEach-Object { \"$($_.TimeGenerated)|$($_.Message)\" }"
        )
        event_output = _run_cmd(["powershell", "-Command", event_cmd], timeout=10)

        if event_output:
            lines.append("")
            lines.append("⚠️  Letzte Disk-Fehler im Event Log:")
            for line in event_output.splitlines()[:5]:
                parts = line.strip().split("|", 1)
                if len(parts) >= 2:
                    lines.append(f"   {parts[0].strip()}: {parts[1].strip()[:100]}")

        if not lines:
            lines.append("Keine Festplatten-Informationen verfuegbar.")

        return lines

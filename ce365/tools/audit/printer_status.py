"""
CE365 Agent - Printer Status

Drucker auflisten, Queue-Status, haengende Jobs
macOS: lpstat / CUPS
Windows: PowerShell Get-Printer / wmic printer
"""

import platform
import subprocess
from typing import Dict, Any
from ce365.tools.base import AuditTool


def _run_cmd(cmd: list, timeout: int = 15) -> str:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.stdout.strip() if result.returncode == 0 else ""
    except Exception:
        return ""


class PrinterStatusTool(AuditTool):
    """Drucker und Print-Queue Status pruefen"""

    @property
    def name(self) -> str:
        return "check_printer_status"

    @property
    def description(self) -> str:
        return (
            "Prueft Drucker-Status und Print-Queue. "
            "Nutze dies bei: 1) Drucker druckt nicht, 2) Haengende Druckauftraege, "
            "3) Drucker-Inventur, 4) Papierstau/Fehler diagnostizieren, "
            "5) Standard-Drucker pruefen."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "clear_queue": {
                    "type": "boolean",
                    "description": "Haengende Druckauftraege loeschen",
                    "default": False,
                },
            },
            "required": [],
        }

    async def execute(self, **kwargs) -> str:
        clear_queue = kwargs.get("clear_queue", False)
        os_type = platform.system()
        lines = ["🖨️  DRUCKER-STATUS", "=" * 50, ""]

        if os_type == "Darwin":
            lines.extend(self._check_macos(clear_queue))
        elif os_type == "Windows":
            lines.extend(self._check_windows(clear_queue))
        else:
            lines.append("❌ Nicht unterstuetztes Betriebssystem")

        return "\n".join(lines)

    def _check_macos(self, clear_queue: bool) -> list:
        lines = []

        # Drucker auflisten
        output = _run_cmd(["lpstat", "-p", "-d"], timeout=10)
        if not output:
            lines.append("Keine Drucker konfiguriert.")
            return lines

        for line in output.splitlines():
            stripped = line.strip()
            if stripped.startswith("printer"):
                parts = stripped.split()
                name = parts[1] if len(parts) > 1 else "?"
                if "idle" in stripped.lower():
                    lines.append(f"   🟢 {name} — Bereit")
                elif "disabled" in stripped.lower():
                    lines.append(f"   🔴 {name} — Deaktiviert")
                elif "printing" in stripped.lower():
                    lines.append(f"   🟡 {name} — Druckt gerade")
                else:
                    lines.append(f"   ⚪ {name} — {stripped}")
            elif "system default" in stripped.lower():
                lines.append(f"   ⭐ Standard: {stripped.split(':')[-1].strip()}")

        # Print Queue
        lines.append("")
        lines.append("📋 Druckauftraege:")
        queue_output = _run_cmd(["lpstat", "-o"], timeout=5)
        if queue_output:
            job_count = 0
            for line in queue_output.splitlines():
                stripped = line.strip()
                if stripped:
                    lines.append(f"   📄 {stripped}")
                    job_count += 1

            if clear_queue and job_count > 0:
                lines.append("")
                _run_cmd(["cancel", "-a"], timeout=10)
                lines.append("   ✅ Alle Druckauftraege geloescht")
        else:
            lines.append("   Keine Auftraege in der Warteschlange")

        return lines

    def _check_windows(self, clear_queue: bool) -> list:
        lines = []

        # PowerShell Get-Printer
        ps_cmd = (
            "Get-Printer 2>$null | "
            "ForEach-Object { \"$($_.Name)|$($_.PrinterStatus)|$($_.PortName)|$($_.DriverName)|$($_.Shared)\" }"
        )
        output = _run_cmd(["powershell", "-Command", ps_cmd], timeout=15)

        if output:
            for line in output.splitlines():
                parts = line.strip().split("|")
                if len(parts) >= 2:
                    name = parts[0].strip()
                    status = parts[1].strip()
                    port = parts[2].strip() if len(parts) > 2 else ""
                    driver = parts[3].strip() if len(parts) > 3 else ""
                    shared = parts[4].strip() if len(parts) > 4 else ""

                    if status.lower() in ("normal", "0"):
                        icon = "🟢"
                        status_text = "Bereit"
                    elif "error" in status.lower():
                        icon = "🔴"
                        status_text = "Fehler"
                    elif "offline" in status.lower():
                        icon = "🔴"
                        status_text = "Offline"
                    else:
                        icon = "🟡"
                        status_text = status

                    lines.append(f"   {icon} {name} — {status_text}")
                    details = []
                    if port:
                        details.append(f"Port: {port}")
                    if driver:
                        details.append(f"Treiber: {driver}")
                    if shared and shared.lower() == "true":
                        details.append("Freigegeben")
                    if details:
                        lines.append(f"      {' | '.join(details)}")
        else:
            # Fallback: wmic
            wmic_output = _run_cmd(["wmic", "printer", "get", "name,status", "/value"], timeout=15)
            if wmic_output:
                for line in wmic_output.splitlines():
                    stripped = line.strip()
                    if stripped.startswith("Name="):
                        lines.append(f"   🖨️  {stripped.split('=', 1)[1]}")
            else:
                lines.append("Keine Drucker gefunden.")

        # Print Queue
        lines.append("")
        lines.append("📋 Druckauftraege:")
        queue_cmd = (
            "Get-PrintJob -PrinterName * 2>$null | "
            "ForEach-Object { \"$($_.PrinterName)|$($_.DocumentName)|$($_.JobStatus)|$($_.Size)\" }"
        )
        queue_output = _run_cmd(["powershell", "-Command", queue_cmd], timeout=10)

        if queue_output:
            job_count = 0
            for line in queue_output.splitlines():
                parts = line.strip().split("|")
                if len(parts) >= 3:
                    printer = parts[0].strip()
                    doc = parts[1].strip()
                    status = parts[2].strip()
                    lines.append(f"   📄 [{printer}] {doc} — {status}")
                    job_count += 1

            if clear_queue and job_count > 0:
                lines.append("")
                _run_cmd(["powershell", "-Command",
                          "Get-Printer | ForEach-Object { Get-PrintJob -PrinterName $_.Name 2>$null | Remove-PrintJob }"],
                         timeout=15)
                lines.append("   ✅ Alle Druckauftraege geloescht")
        else:
            lines.append("   Keine Auftraege in der Warteschlange")

        return lines

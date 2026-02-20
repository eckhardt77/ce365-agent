"""
CE365 Agent - Disk Optimize / Defrag

HDD Defragmentierung, SSD TRIM/Optimierung
Windows: defrag.exe
macOS: diskutil/tmutil (macOS optimiert automatisch)
"""

import platform
from typing import Dict, Any
from ce365.tools.base import RepairTool
from ce365.core.command_runner import get_command_runner


def _run_cmd(cmd: list, timeout: int = 30) -> str:
    result = get_command_runner().run_sync(cmd, timeout=timeout)
    return result.output


class OptimizeDriveTool(RepairTool):
    """Laufwerk optimieren (Defrag fuer HDD, TRIM fuer SSD)"""

    @property
    def name(self) -> str:
        return "optimize_drive"

    @property
    def description(self) -> str:
        return (
            "Optimiert Laufwerke: Defragmentierung fuer HDD, TRIM fuer SSD. "
            "Nutze dies bei: 1) Langsame Festplatten-Performance, "
            "2) Fragmentierte Dateien, 3) Regelmaessige Wartung, "
            "4) Nach vielen Datei-Operationen. "
            "Windows: defrag.exe | macOS: Automatische Optimierung. "
            "Erfordert GO REPAIR!"
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "drive": {
                    "type": "string",
                    "description": "Laufwerk (Windows: C:, D: | macOS: /)",
                    "default": "",
                },
                "analyze_only": {
                    "type": "boolean",
                    "description": "Nur analysieren ohne Optimierung",
                    "default": False,
                },
            },
            "required": [],
        }

    async def execute(self, **kwargs) -> str:
        os_type = platform.system()
        drive = kwargs.get("drive", "")
        analyze_only = kwargs.get("analyze_only", False)

        if os_type == "Windows":
            if not drive:
                drive = "C:"
            return self._optimize_windows(drive, analyze_only)
        elif os_type == "Darwin":
            return self._optimize_macos(analyze_only)
        else:
            return "❌ Nicht unterstuetztes Betriebssystem"

    def _optimize_windows(self, drive: str, analyze_only: bool) -> str:
        lines = ["💿 LAUFWERK-OPTIMIERUNG", "=" * 50, ""]

        drive = drive.strip().upper()
        if len(drive) != 2 or not drive[0].isalpha() or drive[1] != ":":
            return f"❌ Ungueltiges Laufwerk: '{drive}'"

        if analyze_only:
            # Nur Analyse
            lines.append(f"🔍 Analyse von {drive}")
            lines.append("")

            output = _run_cmd(["defrag", drive, "/A", "/V"], timeout=120)
            if output:
                for line in output.splitlines():
                    stripped = line.strip()
                    if stripped:
                        lines.append(f"   {stripped}")
            else:
                lines.append("   ❌ Analyse fehlgeschlagen (Admin-Rechte erforderlich)")
        else:
            # Optimierung
            lines.append(f"🔧 Optimiere {drive}")
            lines.append("⏱️  Dies kann einige Minuten dauern...")
            lines.append("")

            # /O = Optimale Optimierung (TRIM fuer SSD, Defrag fuer HDD)
            output = _run_cmd(["defrag", drive, "/O", "/V"], timeout=3600)
            if output:
                for line in output.splitlines():
                    stripped = line.strip()
                    if stripped:
                        lines.append(f"   {stripped}")
                lines.append("")
                lines.append("✅ Optimierung abgeschlossen")
            else:
                lines.append("   ❌ Optimierung fehlgeschlagen (Admin-Rechte erforderlich)")

        return "\n".join(lines)

    def _optimize_macos(self, analyze_only: bool) -> str:
        lines = ["💿 LAUFWERK-OPTIMIERUNG (macOS)", "=" * 50, ""]

        lines.append("ℹ️  macOS optimiert APFS/SSD-Laufwerke automatisch.")
        lines.append("   TRIM ist standardmaessig aktiviert fuer Apple SSDs.")
        lines.append("")

        # APFS Container Status
        output = _run_cmd(["diskutil", "apfs", "list"], timeout=10)
        if output:
            lines.append("📊 APFS Container Status:")
            for line in output.splitlines()[:20]:
                stripped = line.strip()
                if stripped and any(key in stripped for key in [
                    "Container", "Volume", "Capacity", "Free Space",
                    "FileVault", "Encryption",
                ]):
                    lines.append(f"   {stripped}")

        # Purgeable Space (automatisch freigebbarer Speicher)
        purge_output = _run_cmd(["diskutil", "info", "/"], timeout=10)
        if purge_output:
            for line in purge_output.splitlines():
                if "Purgeable" in line or "Container Free Space" in line:
                    lines.append(f"   {line.strip()}")

        lines.append("")
        if analyze_only:
            lines.append("✅ Analyse abgeschlossen — macOS pflegt SSDs automatisch.")
        else:
            lines.append("✅ macOS verwaltet SSD-Optimierung (TRIM) automatisch.")
            lines.append("   Keine manuelle Defragmentierung noetig/empfohlen fuer SSDs.")

        return "\n".join(lines)

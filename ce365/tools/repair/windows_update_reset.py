"""
CE365 Agent - Windows Update Reset

Setzt Windows Update Komponenten komplett zurueck:
- Stoppt WU-Dienste
- Loescht Cache/Download-Ordner
- Re-registriert DLLs
- Startet Dienste neu
"""

import platform
import subprocess
from typing import Dict, Any
from ce365.tools.base import RepairTool


def _run_cmd(cmd: list, timeout: int = 30) -> tuple:
    """Gibt (success, output) zurueck"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.returncode == 0, result.stdout.strip() or result.stderr.strip()
    except Exception as e:
        return False, str(e)


class ResetWindowsUpdateTool(RepairTool):
    """Windows Update Komponenten komplett zuruecksetzen"""

    @property
    def name(self) -> str:
        return "reset_windows_update"

    @property
    def description(self) -> str:
        return (
            "Setzt Windows Update Komponenten komplett zurueck. "
            "Nutze dies bei: 1) Windows Update bleibt haengen, "
            "2) Update-Fehler (0x80070002, 0x80244019, etc.), "
            "3) Update-Download bricht ab, 4) Update-Installation schlaegt fehl, "
            "5) Windows Update findet keine Updates. "
            "Stoppt Dienste, loescht Cache, re-registriert DLLs, startet Dienste. "
            "Nur fuer Windows, erfordert GO REPAIR + Admin-Rechte!"
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    async def execute(self, **kwargs) -> str:
        if platform.system() != "Windows":
            return "❌ Dieses Tool ist nur fuer Windows verfuegbar"

        lines = ["🔧 WINDOWS UPDATE RESET", "=" * 50, ""]
        lines.append("Setze Windows Update Komponenten zurueck...")
        lines.append("")

        # Phase 1: Dienste stoppen
        lines.append("Phase 1/4: Dienste stoppen")
        services = ["wuauserv", "cryptSvc", "bits", "msiserver"]
        for svc in services:
            success, _ = _run_cmd(["net", "stop", svc], timeout=30)
            icon = "✅" if success else "⚠️"
            lines.append(f"   {icon} {svc} gestoppt")

        lines.append("")

        # Phase 2: Cache loeschen
        lines.append("Phase 2/4: Cache loeschen")
        import os
        import shutil

        cache_dirs = [
            os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "SoftwareDistribution"),
            os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "System32", "catroot2"),
        ]

        for cache_dir in cache_dirs:
            dir_name = os.path.basename(cache_dir)
            backup_dir = cache_dir + ".bak"
            try:
                if os.path.exists(cache_dir):
                    # Umbenennen statt loeschen (sicherer)
                    if os.path.exists(backup_dir):
                        shutil.rmtree(backup_dir, ignore_errors=True)
                    os.rename(cache_dir, backup_dir)
                    lines.append(f"   ✅ {dir_name} → {dir_name}.bak")
                else:
                    lines.append(f"   ℹ️  {dir_name} existiert nicht")
            except PermissionError:
                lines.append(f"   ❌ {dir_name} — Keine Berechtigung (Admin erforderlich)")
            except Exception as e:
                lines.append(f"   ❌ {dir_name} — {e}")

        lines.append("")

        # Phase 3: DLLs re-registrieren
        lines.append("Phase 3/4: Windows Update DLLs re-registrieren")
        dlls = [
            "atl.dll", "urlmon.dll", "mshtml.dll", "shdocvw.dll",
            "browseui.dll", "jscript.dll", "vbscript.dll", "scrrun.dll",
            "msxml.dll", "msxml3.dll", "msxml6.dll", "actxprxy.dll",
            "softpub.dll", "wintrust.dll", "dssenh.dll", "rsaenh.dll",
            "gpkcsp.dll", "sccbase.dll", "slbcsp.dll", "cryptdlg.dll",
            "oleaut32.dll", "ole32.dll", "shell32.dll", "initpki.dll",
            "wuapi.dll", "wuaueng.dll", "wuaueng1.dll", "wucltui.dll",
            "wups.dll", "wups2.dll", "wuweb.dll", "qmgr.dll",
            "qmgrprxy.dll", "wucltux.dll", "muweb.dll", "wuwebv.dll",
        ]

        registered = 0
        for dll in dlls:
            success, _ = _run_cmd(["regsvr32", "/s", dll], timeout=5)
            if success:
                registered += 1

        lines.append(f"   ✅ {registered}/{len(dlls)} DLLs registriert")
        lines.append("")

        # Phase 4: Dienste starten
        lines.append("Phase 4/4: Dienste starten")
        for svc in services:
            success, _ = _run_cmd(["net", "start", svc], timeout=30)
            icon = "✅" if success else "❌"
            lines.append(f"   {icon} {svc} gestartet")

        lines.append("")
        lines.append("✅ Windows Update Reset abgeschlossen!")
        lines.append("")
        lines.append("Naechste Schritte:")
        lines.append("  1. Windows Update erneut ausfuehren")
        lines.append("  2. Bei weiterem Fehler: DISM + SFC ausfuehren")
        lines.append("  3. Computer neu starten")

        return "\n".join(lines)

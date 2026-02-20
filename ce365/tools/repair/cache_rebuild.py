"""
CE365 Agent - Cache Rebuild Tools

Thumbnail/Icon-Cache, Font-Cache, System-Caches neu aufbauen
macOS + Windows
"""

import platform
import os
import shutil
from pathlib import Path
from typing import Dict, Any
from ce365.tools.base import RepairTool
from ce365.core.command_runner import get_command_runner


def _run_cmd(cmd: list, timeout: int = 30) -> tuple:
    """(success, output)"""
    result = get_command_runner().run_sync(cmd, timeout=timeout)
    return result.success, result.output


class RebuildCacheTool(RepairTool):
    """System-Caches neu aufbauen (Thumbnails, Icons, Fonts)"""

    @property
    def name(self) -> str:
        return "rebuild_system_cache"

    @property
    def description(self) -> str:
        return (
            "Baut System-Caches neu auf: Thumbnail/Icon-Cache, Font-Cache, "
            "System-Caches. "
            "Nutze dies bei: 1) Fehlende/falsche Datei-Vorschaubilder, "
            "2) Falsche/kaputte Icons, 3) Schriftarten werden nicht angezeigt, "
            "4) Explorer/Finder zeigt falsche Thumbnails, "
            "5) Nach Font-Installation fehlen Schriften. "
            "Erfordert GO REPAIR! Neustart kann noetig sein."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "cache_type": {
                    "type": "string",
                    "enum": ["all", "thumbnails", "icons", "fonts"],
                    "description": "Welcher Cache neu aufgebaut werden soll",
                    "default": "all",
                },
            },
            "required": [],
        }

    async def execute(self, **kwargs) -> str:
        cache_type = kwargs.get("cache_type", "all")
        os_type = platform.system()
        lines = ["🔄 CACHE-REBUILD", "=" * 50, ""]

        if os_type == "Windows":
            lines.extend(self._rebuild_windows(cache_type))
        elif os_type == "Darwin":
            lines.extend(self._rebuild_macos(cache_type))
        else:
            lines.append("❌ Nicht unterstuetztes Betriebssystem")

        return "\n".join(lines)

    def _rebuild_windows(self, cache_type: str) -> list:
        lines = []

        if cache_type in ("all", "thumbnails", "icons"):
            lines.append("🖼️  Thumbnail/Icon-Cache:")

            # Explorer beenden (sanft)
            _run_cmd(["taskkill", "/f", "/im", "explorer.exe"], timeout=10)

            # Thumbnail Cache loeschen
            local_app = Path(os.environ.get("LOCALAPPDATA", ""))
            explorer_cache = local_app / "Microsoft" / "Windows" / "Explorer"

            deleted = 0
            if explorer_cache.exists():
                for f in explorer_cache.glob("thumbcache_*.db"):
                    try:
                        f.unlink()
                        deleted += 1
                    except:
                        pass
                for f in explorer_cache.glob("iconcache_*.db"):
                    try:
                        f.unlink()
                        deleted += 1
                    except:
                        pass

            if deleted:
                lines.append(f"   ✅ {deleted} Cache-Dateien geloescht")
            else:
                lines.append("   ℹ️  Keine Cache-Dateien gefunden")

            # Icon-Cache per ie4uinit
            _run_cmd(["ie4uinit.exe", "-ClearIconCache"], timeout=10)
            lines.append("   ✅ Icon-Cache zurueckgesetzt")

            # Explorer neu starten
            subprocess.Popen(["explorer.exe"])
            lines.append("   ✅ Explorer neu gestartet")
            lines.append("")

        if cache_type in ("all", "fonts"):
            lines.append("🔤 Font-Cache:")

            # Font Cache Service stoppen
            success, _ = _run_cmd(["net", "stop", "FontCache"], timeout=15)
            success3, _ = _run_cmd(["net", "stop", "FontCache3.0.0.0"], timeout=15)

            # Font Cache Dateien loeschen
            win_dir = Path(os.environ.get("SystemRoot", "C:\\Windows"))
            font_caches = [
                win_dir / "ServiceProfiles" / "LocalService" / "AppData" / "Local" / "FontCache",
                win_dir / "System32" / "FNTCACHE.DAT",
            ]

            for cache_path in font_caches:
                try:
                    if cache_path.is_dir():
                        shutil.rmtree(cache_path, ignore_errors=True)
                        lines.append(f"   ✅ {cache_path.name} geloescht")
                    elif cache_path.is_file():
                        cache_path.unlink()
                        lines.append(f"   ✅ {cache_path.name} geloescht")
                except:
                    lines.append(f"   ⚠️  {cache_path.name} konnte nicht geloescht werden")

            # Font Cache Service starten
            _run_cmd(["net", "start", "FontCache"], timeout=15)
            _run_cmd(["net", "start", "FontCache3.0.0.0"], timeout=15)
            lines.append("   ✅ Font-Cache Service neu gestartet")
            lines.append("")

        lines.append("⚠️  Ein Neustart wird empfohlen, damit alle Caches neu aufgebaut werden.")

        return lines

    def _rebuild_macos(self, cache_type: str) -> list:
        lines = []

        if cache_type in ("all", "thumbnails", "icons"):
            lines.append("🖼️  Thumbnail/Icon-Cache:")

            # Finder-Icon-Cache
            success, _ = _run_cmd([
                "find", "/private/var/folders", "-name",
                "com.apple.iconservices", "-exec", "rm", "-rf", "{}", "+"
            ], timeout=15)

            # QuickLook Cache
            success_ql, _ = _run_cmd(["qlmanage", "-r", "cache"], timeout=10)
            if success_ql:
                lines.append("   ✅ QuickLook-Cache zurueckgesetzt")

            # LaunchServices-Datenbank neu aufbauen
            success_ls, _ = _run_cmd([
                "/System/Library/Frameworks/CoreServices.framework/Frameworks/"
                "LaunchServices.framework/Support/lsregister",
                "-kill", "-r", "-domain", "local", "-domain", "system", "-domain", "user"
            ], timeout=30)
            if success_ls:
                lines.append("   ✅ LaunchServices-Datenbank neu aufgebaut")
            else:
                lines.append("   ⚠️  LaunchServices konnte nicht zurueckgesetzt werden")

            # Finder neu starten
            _run_cmd(["killall", "Finder"], timeout=5)
            lines.append("   ✅ Finder neu gestartet")
            lines.append("")

        if cache_type in ("all", "fonts"):
            lines.append("🔤 Font-Cache:")

            # macOS Font-Cache
            success, _ = _run_cmd(["atsutil", "databases", "-remove"], timeout=15)
            if success:
                lines.append("   ✅ Font-Datenbank entfernt (wird beim naechsten Start neu aufgebaut)")
            else:
                lines.append("   ⚠️  Font-Datenbank konnte nicht entfernt werden")

            # Font Server neu starten
            success, _ = _run_cmd(["atsutil", "server", "-shutdown"], timeout=10)
            lines.append("   ✅ Font-Server neu gestartet")
            lines.append("")

        lines.append("ℹ️  Ein Neustart wird empfohlen fuer vollstaendigen Cache-Rebuild.")

        return lines

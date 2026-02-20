"""
CE365 Agent - Browser Cache Cleanup

Chrome, Firefox, Edge, Safari Caches bereinigen
Plattformuebergreifend: macOS + Windows
"""

import os
import platform
import shutil
from pathlib import Path
from typing import Dict, Any
from ce365.tools.base import RepairTool


def _get_browser_cache_paths() -> dict:
    """Gibt alle Browser-Cache-Pfade zurueck (plattformspezifisch)"""
    home = Path.home()
    os_type = platform.system()
    browsers = {}

    if os_type == "Darwin":
        browsers["Chrome"] = [
            home / "Library/Caches/Google/Chrome/Default/Cache",
            home / "Library/Caches/Google/Chrome/Default/Code Cache",
            home / "Library/Caches/Google/Chrome/Default/Service Worker",
        ]
        browsers["Firefox"] = [
            home / "Library/Caches/Firefox/Profiles",
        ]
        browsers["Edge"] = [
            home / "Library/Caches/Microsoft Edge/Default/Cache",
            home / "Library/Caches/Microsoft Edge/Default/Code Cache",
        ]
        browsers["Safari"] = [
            home / "Library/Caches/com.apple.Safari",
            home / "Library/Caches/com.apple.WebKit.WebProcess",
        ]

    elif os_type == "Windows":
        local = Path(os.environ.get("LOCALAPPDATA", home / "AppData/Local"))
        browsers["Chrome"] = [
            local / "Google/Chrome/User Data/Default/Cache",
            local / "Google/Chrome/User Data/Default/Code Cache",
            local / "Google/Chrome/User Data/Default/Service Worker",
        ]
        browsers["Firefox"] = [
            local / "Mozilla/Firefox/Profiles",
        ]
        browsers["Edge"] = [
            local / "Microsoft/Edge/User Data/Default/Cache",
            local / "Microsoft/Edge/User Data/Default/Code Cache",
        ]
        # Safari nicht auf Windows

    return browsers


def _get_dir_size(path: Path) -> int:
    """Berechnet Verzeichnisgroesse in Bytes"""
    total = 0
    try:
        for f in path.rglob("*"):
            if f.is_file():
                try:
                    total += f.stat().st_size
                except (OSError, PermissionError):
                    pass
    except (OSError, PermissionError):
        pass
    return total


def _format_size(bytes_val: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_val < 1024:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f} TB"


class BrowserCacheCleanupTool(RepairTool):
    """Browser-Caches bereinigen (Chrome, Firefox, Edge, Safari)"""

    @property
    def name(self) -> str:
        return "clear_browser_cache"

    @property
    def description(self) -> str:
        return (
            "Bereinigt Browser-Caches (Chrome, Firefox, Edge, Safari). "
            "Nutze dies bei: 1) Browser ist langsam, 2) Webseiten laden fehlerhaft, "
            "3) Speicherplatz freigeben, 4) SSL/Cookie-Probleme, "
            "5) 'Loeschen Sie Ihren Cache' Empfehlungen. "
            "WICHTIG: Alle Browser-Fenster muessen vorher geschlossen sein! "
            "Erfordert GO REPAIR!"
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "browser": {
                    "type": "string",
                    "enum": ["all", "chrome", "firefox", "edge", "safari"],
                    "description": "Welcher Browser bereinigt werden soll (Standard: all)",
                    "default": "all",
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "Nur anzeigen was geloescht wuerde (ohne zu loeschen)",
                    "default": False,
                },
            },
            "required": [],
        }

    async def execute(self, **kwargs) -> str:
        browser_filter = kwargs.get("browser", "all").lower()
        dry_run = kwargs.get("dry_run", False)

        all_paths = _get_browser_cache_paths()
        lines = []

        if dry_run:
            lines.append("🔍 BROWSER-CACHE ANALYSE (Dry Run)")
        else:
            lines.append("🧹 BROWSER-CACHE BEREINIGUNG")
        lines.append("=" * 50)
        lines.append("")

        total_freed = 0

        for browser_name, paths in all_paths.items():
            if browser_filter != "all" and browser_filter != browser_name.lower():
                continue

            browser_total = 0
            browser_paths_exist = False

            for cache_path in paths:
                if cache_path.exists():
                    browser_paths_exist = True
                    size = _get_dir_size(cache_path)
                    browser_total += size

            if not browser_paths_exist:
                lines.append(f"  {browser_name}: Nicht installiert oder kein Cache")
                continue

            if browser_total == 0:
                lines.append(f"  {browser_name}: Cache ist bereits leer")
                continue

            if dry_run:
                lines.append(f"  {browser_name}: {_format_size(browser_total)} wuerden geloescht")
                total_freed += browser_total
            else:
                # Cache loeschen
                freed = 0
                errors = []
                for cache_path in paths:
                    if cache_path.exists():
                        try:
                            if cache_path.is_dir():
                                size = _get_dir_size(cache_path)
                                shutil.rmtree(cache_path, ignore_errors=True)
                                freed += size
                            elif cache_path.is_file():
                                size = cache_path.stat().st_size
                                cache_path.unlink()
                                freed += size
                        except PermissionError:
                            errors.append(f"Keine Berechtigung: {cache_path.name}")
                        except Exception as e:
                            errors.append(str(e))

                if freed > 0:
                    lines.append(f"  ✅ {browser_name}: {_format_size(freed)} geloescht")
                    total_freed += freed
                else:
                    lines.append(f"  ⚠️  {browser_name}: Konnte nicht bereinigt werden")

                if errors:
                    for err in errors[:2]:
                        lines.append(f"     ⚠️  {err}")

                if errors and "Keine Berechtigung" in str(errors):
                    lines.append(f"     → Ist {browser_name} noch geoeffnet?")

        lines.append("")
        if dry_run:
            lines.append(f"📊 Gesamt freizugeben: {_format_size(total_freed)}")
            lines.append("   Erneut ohne dry_run=true ausfuehren um zu loeschen.")
        else:
            lines.append(f"📊 Gesamt freigegeben: {_format_size(total_freed)}")

        return "\n".join(lines)

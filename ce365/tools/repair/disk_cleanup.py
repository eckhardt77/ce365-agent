"""
CE365 Agent - Disk Cleanup Tools

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
Licensed under MIT License

Disk-Speicher freigeben:
- Windows: Temp-Dateien, Downloads, Recycle Bin
- macOS: Caches, Logs, Trash
"""

import platform
import subprocess
import os
import shutil
from pathlib import Path
from typing import Dict, Any
from ce365.tools.base import RepairTool


class DiskCleanupTool(RepairTool):
    """
    Bereinigt temporäre Dateien und gibt Speicher frei

    Windows: Temp, Downloads (älter als 30 Tage), Recycle Bin
    macOS: User Caches, System Logs, Trash
    """

    @property
    def name(self) -> str:
        return "cleanup_disk"

    @property
    def description(self) -> str:
        return (
            "Bereinigt temporäre Dateien und gibt Disk-Speicher frei. "
            "Nutze dies bei: 1) Wenig Speicherplatz, 2) Langsames System, "
            "3) Nach großen Installationen. "
            "Löscht: Temp-Dateien, alte Downloads, Caches, Logs. "
            "WICHTIG: Erfordert GO REPAIR Freigabe!"
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "include_downloads": {
                    "type": "boolean",
                    "description": "Downloads-Ordner bereinigen (nur Dateien älter als 30 Tage)",
                    "default": False
                },
                "include_trash": {
                    "type": "boolean",
                    "description": "Papierkorb/Trash leeren",
                    "default": True
                }
            },
            "required": []
        }

    async def execute(self, **kwargs) -> str:
        """
        Führt Disk Cleanup durch

        Args:
            include_downloads: Downloads bereinigen (default: False)
            include_trash: Papierkorb leeren (default: True)

        Returns:
            Bericht mit freigegebenem Speicher
        """
        include_downloads = kwargs.get("include_downloads", False)
        include_trash = kwargs.get("include_trash", True)

        os_type = platform.system()

        if os_type == "Windows":
            return self._cleanup_windows(include_downloads, include_trash)
        elif os_type == "Darwin":
            return self._cleanup_macos(include_downloads, include_trash)
        else:
            return f"❌ Nicht unterstütztes OS: {os_type}"

    def _cleanup_windows(self, include_downloads: bool, include_trash: bool) -> str:
        """Windows Disk Cleanup"""
        try:
            freed_bytes = 0
            cleaned_items = []

            # 1. Windows Temp
            temp_path = Path(os.environ.get('TEMP', 'C:\\Windows\\Temp'))
            if temp_path.exists():
                size = self._cleanup_directory(temp_path, days_old=7)
                freed_bytes += size
                if size > 0:
                    cleaned_items.append(f"Windows Temp: {self._format_size(size)}")

            # 2. User Temp
            user_temp = Path(os.environ.get('LOCALAPPDATA', '')) / 'Temp'
            if user_temp.exists():
                size = self._cleanup_directory(user_temp, days_old=7)
                freed_bytes += size
                if size > 0:
                    cleaned_items.append(f"User Temp: {self._format_size(size)}")

            # 3. Downloads (optional, nur alte Dateien)
            if include_downloads:
                downloads = Path.home() / 'Downloads'
                if downloads.exists():
                    size = self._cleanup_directory(downloads, days_old=30)
                    freed_bytes += size
                    if size > 0:
                        cleaned_items.append(f"Downloads (>30 Tage): {self._format_size(size)}")

            # 4. Recycle Bin (optional)
            if include_trash:
                # PowerShell Recycle Bin leeren
                try:
                    subprocess.run(
                        ["powershell", "-Command", "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"],
                        capture_output=True,
                        timeout=30
                    )
                    cleaned_items.append("Papierkorb geleert")
                except:
                    pass

            # Ergebnis
            output = [
                "🧹 Disk Cleanup abgeschlossen",
                "",
                f"✓ Freigegebener Speicher: {self._format_size(freed_bytes)}",
                ""
            ]

            if cleaned_items:
                output.append("Bereinigte Bereiche:")
                output.extend([f"  • {item}" for item in cleaned_items])
            else:
                output.append("ℹ️  Keine Dateien zum Bereinigen gefunden")

            return "\n".join(output)

        except Exception as e:
            return f"❌ Fehler beim Disk Cleanup: {str(e)}"

    def _cleanup_macos(self, include_downloads: bool, include_trash: bool) -> str:
        """macOS Disk Cleanup"""
        try:
            freed_bytes = 0
            cleaned_items = []

            # 1. User Caches
            user_cache = Path.home() / 'Library' / 'Caches'
            if user_cache.exists():
                size = self._cleanup_directory(user_cache, days_old=30, pattern='*')
                freed_bytes += size
                if size > 0:
                    cleaned_items.append(f"User Caches: {self._format_size(size)}")

            # 2. User Logs
            user_logs = Path.home() / 'Library' / 'Logs'
            if user_logs.exists():
                size = self._cleanup_directory(user_logs, days_old=30)
                freed_bytes += size
                if size > 0:
                    cleaned_items.append(f"User Logs: {self._format_size(size)}")

            # 3. Downloads (optional)
            if include_downloads:
                downloads = Path.home() / 'Downloads'
                if downloads.exists():
                    size = self._cleanup_directory(downloads, days_old=30)
                    freed_bytes += size
                    if size > 0:
                        cleaned_items.append(f"Downloads (>30 Tage): {self._format_size(size)}")

            # 4. Trash (optional)
            if include_trash:
                try:
                    trash_dir = Path.home() / '.Trash'
                    if trash_dir.exists():
                        import shutil
                        for item in trash_dir.iterdir():
                            try:
                                if item.is_dir():
                                    shutil.rmtree(item)
                                else:
                                    item.unlink()
                            except Exception:
                                pass
                    cleaned_items.append("Papierkorb geleert")
                except Exception:
                    pass

            # Ergebnis
            output = [
                "🧹 Disk Cleanup abgeschlossen",
                "",
                f"✓ Freigegebener Speicher: {self._format_size(freed_bytes)}",
                ""
            ]

            if cleaned_items:
                output.append("Bereinigte Bereiche:")
                output.extend([f"  • {item}" for item in cleaned_items])
            else:
                output.append("ℹ️  Keine Dateien zum Bereinigen gefunden")

            return "\n".join(output)

        except Exception as e:
            return f"❌ Fehler beim Disk Cleanup: {str(e)}"

    def _cleanup_directory(self, directory: Path, days_old: int = 7, pattern: str = '*') -> int:
        """
        Bereinigt Verzeichnis von alten Dateien

        Args:
            directory: Zu bereinigendes Verzeichnis
            days_old: Dateien älter als X Tage löschen
            pattern: Datei-Pattern (z.B. '*.tmp')

        Returns:
            Freigegebene Bytes
        """
        import time
        freed_bytes = 0
        cutoff_time = time.time() - (days_old * 86400)

        try:
            for item in directory.glob(pattern):
                try:
                    # Nur alte Dateien
                    if item.stat().st_mtime < cutoff_time:
                        if item.is_file():
                            size = item.stat().st_size
                            item.unlink()
                            freed_bytes += size
                        elif item.is_dir():
                            size = sum(f.stat().st_size for f in item.rglob('*') if f.is_file())
                            shutil.rmtree(item)
                            freed_bytes += size
                except (PermissionError, OSError):
                    # Skip Dateien ohne Permissions
                    continue

        except Exception:
            pass

        return freed_bytes

    def _format_size(self, bytes_value: int) -> str:
        """Formatiert Bytes zu lesbarer Größe"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} TB"

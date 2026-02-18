"""
CE365 Agent - Backup Status Check Tools

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
Licensed under Source Available License

Backup-Status prüfen:
- Windows: Windows Backup, System Restore Points
- macOS: Time Machine, APFS Snapshots
"""

import platform
import subprocess
from datetime import datetime
from typing import Dict, Any
from ce365.tools.base import AuditTool


class CheckBackupStatusTool(AuditTool):
    """
    Prüft Backup-Status des Systems

    Windows: Windows Backup + Restore Points
    macOS: Time Machine + Snapshots
    """

    @property
    def name(self) -> str:
        return "check_backup_status"

    @property
    def description(self) -> str:
        return (
            "Prüft ob ein funktionierendes Backup-System konfiguriert ist. "
            "Nutze dies bei: 1) Vor Reparaturen, 2) Regelmäßige Checks, "
            "3) Nach System-Setup. "
            "Zeigt: Backup-Status, letztes Backup, Restore Points (Windows) / Time Machine (macOS)."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": []
        }

    async def execute(self, **kwargs) -> str:
        """
        Prüft Backup-Status

        Returns:
            Backup-Status Report
        """
        os_type = platform.system()

        if os_type == "Windows":
            return self._check_windows_backup()
        elif os_type == "Darwin":
            return self._check_macos_backup()
        else:
            return f"❌ Nicht unterstütztes OS: {os_type}"

    def _check_windows_backup(self) -> str:
        """Windows Backup & Restore Points prüfen"""
        try:
            output = [
                "🛡️  Windows Backup Status",
                ""
            ]

            # 1. Windows Backup Status (wbadmin)
            try:
                result = subprocess.run(
                    ["wbadmin", "get", "status"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if "No backup is currently running" in result.stdout:
                    output.append("📦 Windows Backup:")
                    output.append("   ⚠️  Kein aktives Backup läuft")

                    # Prüfe ob überhaupt konfiguriert
                    versions_result = subprocess.run(
                        ["wbadmin", "get", "versions"],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )

                    if "No backups found" in versions_result.stdout or "ERROR" in versions_result.stdout:
                        output.append("   ❌ Windows Backup ist NICHT konfiguriert")
                    else:
                        output.append("   ✓ Windows Backup ist konfiguriert")
                        # Parse letzte Backup-Zeit
                        for line in versions_result.stdout.split("\n"):
                            if "Version" in line or "Time" in line:
                                output.append(f"   {line.strip()}")

            except Exception as e:
                output.append("📦 Windows Backup:")
                output.append(f"   ⚠️  Status konnte nicht ermittelt werden: {str(e)}")

            output.append("")

            # 2. System Restore Points
            try:
                ps_cmd = """
                Get-ComputerRestorePoint |
                Select-Object -First 5 CreationTime, Description, SequenceNumber |
                Format-List
                """

                result = subprocess.run(
                    ["powershell", "-Command", ps_cmd],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0 and result.stdout.strip():
                    output.append("💾 System Restore Points:")
                    restore_points = result.stdout.strip()

                    if restore_points:
                        # Parse Restore Points
                        lines = restore_points.split("\n")
                        count = 0
                        for line in lines:
                            if line.strip():
                                output.append(f"   {line.strip()}")
                                if "CreationTime" in line:
                                    count += 1

                        output.append("")
                        output.append(f"   ✓ {count} Restore Point(s) vorhanden")
                    else:
                        output.append("   ❌ Keine Restore Points gefunden")
                else:
                    output.append("💾 System Restore Points:")
                    output.append("   ❌ Keine Restore Points vorhanden")

            except Exception as e:
                output.append("💾 System Restore Points:")
                output.append(f"   ⚠️  Konnte nicht geprüft werden: {str(e)}")

            output.append("")

            # Zusammenfassung & Empfehlung
            output.append("─" * 50)
            output.append("💡 Empfehlung:")
            output.append("   • Windows Backup konfigurieren (Settings → Backup)")
            output.append("   • Regelmäßige Restore Points erstellen")
            output.append("   • Tool: create_restore_point")

            return "\n".join(output)

        except Exception as e:
            return f"❌ Fehler beim Backup-Check: {str(e)}"

    def _check_macos_backup(self) -> str:
        """macOS Time Machine & Snapshots prüfen"""
        try:
            output = [
                "🛡️  macOS Backup Status",
                ""
            ]

            # 1. Time Machine Status
            try:
                result = subprocess.run(
                    ["tmutil", "status"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                output.append("⏰ Time Machine Status:")

                tm_output = result.stdout

                if "Running = 1" in tm_output:
                    output.append("   ✓ Backup läuft gerade")
                elif "Running = 0" in tm_output:
                    output.append("   ℹ️  Kein aktives Backup")

                # Parse weitere Infos
                for line in tm_output.split("\n"):
                    if "Percent" in line or "Progress" in line:
                        output.append(f"   {line.strip()}")

            except Exception as e:
                output.append("⏰ Time Machine Status:")
                output.append(f"   ⚠️  Konnte nicht ermittelt werden: {str(e)}")

            output.append("")

            # 2. Letztes Backup
            try:
                result = subprocess.run(
                    ["tmutil", "latestbackup"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0 and result.stdout.strip():
                    latest = result.stdout.strip()
                    output.append("📅 Letztes Backup:")
                    output.append(f"   {latest}")

                    # Parse Datum aus Pfad (Format: YYYY-MM-DD-HHMMSS)
                    import re
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2}-\d{6})', latest)
                    if date_match:
                        date_str = date_match.group(1)
                        try:
                            backup_date = datetime.strptime(date_str, "%Y-%m-%d-%H%M%S")
                            days_ago = (datetime.now() - backup_date).days

                            if days_ago == 0:
                                output.append("   ✓ Heute erstellt")
                            elif days_ago == 1:
                                output.append("   ✓ Gestern erstellt")
                            elif days_ago <= 7:
                                output.append(f"   ✓ Vor {days_ago} Tagen erstellt")
                            else:
                                output.append(f"   ⚠️  Vor {days_ago} Tagen erstellt (veraltet!)")
                        except:
                            pass
                else:
                    output.append("📅 Letztes Backup:")
                    output.append("   ❌ Kein Backup gefunden")

            except Exception as e:
                output.append("📅 Letztes Backup:")
                output.append(f"   ⚠️  Konnte nicht ermittelt werden")

            output.append("")

            # 3. Time Machine Destination
            try:
                result = subprocess.run(
                    ["tmutil", "destinationinfo"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0 and result.stdout.strip():
                    output.append("💿 Backup-Ziel:")
                    dest_output = result.stdout.strip()

                    for line in dest_output.split("\n"):
                        if "Name" in line or "Mount Point" in line or "ID" in line[:5]:
                            output.append(f"   {line.strip()}")
                else:
                    output.append("💿 Backup-Ziel:")
                    output.append("   ❌ Time Machine ist nicht konfiguriert")

            except Exception as e:
                output.append("💿 Backup-Ziel:")
                output.append("   ⚠️  Konnte nicht ermittelt werden")

            output.append("")

            # Zusammenfassung & Empfehlung
            output.append("─" * 50)
            output.append("💡 Empfehlung:")
            output.append("   • Time Machine in System Settings konfigurieren")
            output.append("   • Externe Festplatte als Backup-Ziel")
            output.append("   • Tool: trigger_time_machine_backup")

            return "\n".join(output)

        except Exception as e:
            return f"❌ Fehler beim Backup-Check: {str(e)}"

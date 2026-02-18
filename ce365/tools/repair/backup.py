"""
CE365 Agent - Backup Creation Tools

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
Licensed under Source Available License

Backup erstellen:
- Windows: System Restore Points, Windows Backup
- macOS: Time Machine Backup triggern
"""

import platform
import subprocess
from typing import Dict, Any
from ce365.tools.base import RepairTool
from ce365.tools.sanitize import validate_description


class CreateRestorePointTool(RepairTool):
    """
    Erstellt Windows System Restore Point

    Erstellt Wiederherstellungspunkt VOR Reparaturen
    """

    @property
    def name(self) -> str:
        return "create_restore_point"

    @property
    def description(self) -> str:
        return (
            "Erstellt einen Windows System Restore Point. "
            "Nutze dies bei: 1) VOR Reparaturen, 2) VOR System-Änderungen, "
            "3) VOR Software-Installation. "
            "Nur für Windows, erfordert GO REPAIR!"
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "Beschreibung des Restore Points (Standard: CE365 Restore Point)",
                    "default": "CE365 Restore Point"
                }
            },
            "required": []
        }

    async def execute(self, **kwargs) -> str:
        """
        Erstellt Restore Point

        Args:
            description: Beschreibung (default: "CE365 Restore Point")

        Returns:
            Erfolg oder Fehler
        """
        os_type = platform.system()

        if os_type != "Windows":
            return "❌ Dieses Tool ist nur für Windows verfügbar"

        description = validate_description(kwargs.get("description", "CE365 Restore Point"))

        try:
            output = [
                "💾 Erstelle System Restore Point...",
                ""
            ]

            # PowerShell Checkpoint-Computer
            ps_cmd = f'Checkpoint-Computer -Description "{description}" -RestorePointType "MODIFY_SETTINGS"'

            result = subprocess.run(
                ["powershell", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=120  # 2 Minuten
            )

            if result.returncode == 0:
                output.append(f"✅ Restore Point erfolgreich erstellt")
                output.append("")
                output.append(f"Beschreibung: {description}")
                output.append(f"Zeitstempel: {self._get_timestamp()}")
                output.append("")
                output.append("💡 Wiederherstellung:")
                output.append("   System → System Protection → System Restore")
                output.append("   oder: rstrui.exe")

            else:
                error_msg = result.stderr or result.stdout
                output.append("❌ Fehler beim Erstellen des Restore Points:")
                output.append("")
                output.append(error_msg[:500])
                output.append("")
                output.append("Mögliche Ursachen:")
                output.append("• System Protection ist deaktiviert")
                output.append("• Nicht genug Speicherplatz")
                output.append("• Bereits ein Restore Point in letzter Stunde erstellt")

            return "\n".join(output)

        except subprocess.TimeoutExpired:
            return "❌ Timeout beim Erstellen des Restore Points (>2 Minuten)"
        except Exception as e:
            return f"❌ Fehler: {str(e)}"

    def _get_timestamp(self) -> str:
        """Aktueller Timestamp"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class TriggerTimeMachineBackupTool(RepairTool):
    """
    Startet macOS Time Machine Backup

    Manuelles Backup anstoßen
    """

    @property
    def name(self) -> str:
        return "trigger_time_machine_backup"

    @property
    def description(self) -> str:
        return (
            "Startet ein manuelles Time Machine Backup (macOS). "
            "Nutze dies bei: 1) VOR Reparaturen, 2) VOR System-Änderungen, "
            "3) Regelmäßige Backups. "
            "ACHTUNG: Kann 10-60 Minuten dauern! "
            "Nur für macOS, erfordert GO REPAIR!"
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "wait": {
                    "type": "boolean",
                    "description": "Warten bis Backup abgeschlossen (Standard: false)",
                    "default": False
                }
            },
            "required": []
        }

    async def execute(self, **kwargs) -> str:
        """
        Triggert Time Machine Backup

        Args:
            wait: Warten bis fertig (default: False)

        Returns:
            Status
        """
        os_type = platform.system()

        if os_type != "Darwin":
            return "❌ Dieses Tool ist nur für macOS verfügbar"

        wait = kwargs.get("wait", False)

        try:
            output = [
                "⏰ Starte Time Machine Backup...",
                ""
            ]

            # tmutil startbackup
            cmd = ["tmutil", "startbackup"]

            if wait:
                cmd.append("-b")  # block (wait)
                output.append("⏱️  Warte auf Backup-Abschluss (kann 10-60 Minuten dauern)...")
                output.append("")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600 if wait else 30  # 60 Min wenn wait, sonst 30s
            )

            if result.returncode == 0:
                if wait:
                    output.append("✅ Time Machine Backup erfolgreich abgeschlossen")
                else:
                    output.append("✅ Time Machine Backup gestartet")
                    output.append("")
                    output.append("ℹ️  Backup läuft im Hintergrund")
                    output.append("   Überprüfe Status mit: check_backup_status")

                output.append("")
                output.append(f"Zeitstempel: {self._get_timestamp()}")

            else:
                error_msg = result.stderr or result.stdout
                output.append("❌ Fehler beim Starten des Backups:")
                output.append("")
                output.append(error_msg[:500])
                output.append("")
                output.append("Mögliche Ursachen:")
                output.append("• Time Machine ist nicht konfiguriert")
                output.append("• Backup-Laufwerk nicht verbunden")
                output.append("• Bereits ein Backup läuft")

            return "\n".join(output)

        except subprocess.TimeoutExpired:
            return (
                "❌ Timeout beim Time Machine Backup\n\n"
                "Das Backup dauert sehr lange.\n"
                "Überprüfe den Status in System Settings → Time Machine."
            )
        except Exception as e:
            return f"❌ Fehler: {str(e)}"

    def _get_timestamp(self) -> str:
        """Aktueller Timestamp"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

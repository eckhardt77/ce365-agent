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
            return f"❌ Fehler beim TM-Backup: {str(e)}"

    def _get_timestamp(self) -> str:
        """Aktueller Timestamp"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class StopBackupTool(RepairTool):
    """
    Stoppt ein laufendes Backup

    macOS: Time Machine Backup stoppen
    Windows: Windows Backup Job stoppen
    """

    @property
    def name(self) -> str:
        return "stop_backup"

    @property
    def description(self) -> str:
        return (
            "Stoppt ein aktuell laufendes Backup. "
            "Nutze dies bei: 1) Backup dauert zu lange, "
            "2) Festplatte wird voll, "
            "3) System wird durch Backup verlangsamt. "
            "macOS: Time Machine stoppen. Windows: wbadmin Job stoppen. "
            "Erfordert GO REPAIR!"
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": []
        }

    async def execute(self, **kwargs) -> str:
        os_type = platform.system()
        if os_type == "Darwin":
            return self._stop_macos()
        elif os_type == "Windows":
            return self._stop_windows()
        else:
            return f"❌ Nicht unterstütztes OS: {os_type}"

    def _stop_macos(self) -> str:
        try:
            output = [
                "⏹️  Stoppe Time Machine Backup...",
                ""
            ]

            # Prüfe ob Backup läuft
            status_result = subprocess.run(
                ["tmutil", "status"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if "Running = 0" in status_result.stdout:
                return "ℹ️  Kein aktives Time Machine Backup läuft — nichts zu stoppen."

            result = subprocess.run(
                ["tmutil", "stopbackup"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                output.append("✅ Time Machine Backup wurde gestoppt")
                output.append("")
                output.append("ℹ️  Das nächste automatische Backup startet planmäßig.")
                output.append("   Manuell starten: trigger_backup")
            else:
                error_msg = result.stderr or result.stdout
                output.append("❌ Backup konnte nicht gestoppt werden:")
                output.append(f"   {error_msg[:300]}")

            return "\n".join(output)

        except Exception as e:
            return f"❌ Fehler: {str(e)}"

    def _stop_windows(self) -> str:
        try:
            output = [
                "⏹️  Stoppe Windows Backup...",
                ""
            ]

            # Prüfe ob Backup läuft
            status_result = subprocess.run(
                ["wbadmin", "get", "status"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if "No backup is currently running" in status_result.stdout:
                return "ℹ️  Kein aktives Windows Backup läuft — nichts zu stoppen."

            result = subprocess.run(
                ["wbadmin", "stop", "job"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                output.append("✅ Windows Backup wurde gestoppt")
                output.append("")
                output.append("ℹ️  Das nächste geplante Backup startet automatisch.")
                output.append("   Manuell starten: trigger_backup")
            else:
                error_msg = result.stderr or result.stdout
                output.append("❌ Backup konnte nicht gestoppt werden:")
                output.append(f"   {error_msg[:300]}")

            return "\n".join(output)

        except Exception as e:
            return f"❌ Fehler: {str(e)}"


class ManageBackupExclusionsTool(RepairTool):
    """
    Verwaltet Backup-Ausschlüsse (Pfade ein-/ausschließen)

    macOS: Time Machine Exclusions (tmutil)
    Windows: File History Exclusions (PowerShell)
    """

    @property
    def name(self) -> str:
        return "manage_backup_exclusions"

    @property
    def description(self) -> str:
        return (
            "Verwaltet Backup-Ausschlüsse — Pfade prüfen, hinzufügen oder entfernen. "
            "Nutze dies bei: 1) Prüfen ob ein Ordner vom Backup ausgeschlossen ist, "
            "2) Große Ordner (node_modules, VMs, Temp) vom Backup ausschließen, "
            "3) Versehentlich ausgeschlossene Pfade wieder einschließen. "
            "macOS: Time Machine Exclusions. Windows: File History Exclusions. "
            "Erfordert GO REPAIR!"
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["check", "add", "remove"],
                    "description": "Aktion: check (prüfen), add (ausschließen), remove (wieder einschließen)"
                },
                "path": {
                    "type": "string",
                    "description": "Pfad zum Prüfen/Ausschließen/Einschließen"
                }
            },
            "required": ["action", "path"]
        }

    async def execute(self, **kwargs) -> str:
        action = kwargs.get("action", "check")
        path = kwargs.get("path", "")

        if not path:
            return "❌ Kein Pfad angegeben"

        from ce365.tools.sanitize import validate_file_path
        try:
            path = validate_file_path(path)
        except ValueError as e:
            return f"❌ Ungültiger Pfad: {str(e)}"

        os_type = platform.system()
        if os_type == "Darwin":
            return self._manage_macos(action, path)
        elif os_type == "Windows":
            return self._manage_windows(action, path)
        else:
            return f"❌ Nicht unterstütztes OS: {os_type}"

    def _manage_macos(self, action: str, path: str) -> str:
        try:
            if action == "check":
                result = subprocess.run(
                    ["tmutil", "isexcluded", path],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0:
                    output_text = result.stdout.strip()
                    if "[Excluded]" in output_text:
                        return f"🚫 Pfad ist von Time Machine AUSGESCHLOSSEN:\n   {path}"
                    else:
                        return f"✅ Pfad wird von Time Machine gesichert:\n   {path}"
                else:
                    return f"⚠️  Status konnte nicht ermittelt werden: {result.stderr[:200]}"

            elif action == "add":
                result = subprocess.run(
                    ["tmutil", "addexclusion", path],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0:
                    return (
                        f"✅ Pfad wurde von Time Machine ausgeschlossen:\n"
                        f"   {path}\n\n"
                        f"ℹ️  Dieser Ordner wird beim nächsten Backup nicht mehr gesichert."
                    )
                else:
                    return f"❌ Fehler beim Ausschließen: {result.stderr[:300]}"

            elif action == "remove":
                result = subprocess.run(
                    ["tmutil", "removeexclusion", path],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0:
                    return (
                        f"✅ Pfad wird wieder von Time Machine gesichert:\n"
                        f"   {path}\n\n"
                        f"ℹ️  Dieser Ordner wird beim nächsten Backup wieder eingeschlossen."
                    )
                else:
                    return f"❌ Fehler beim Einschließen: {result.stderr[:300]}"

            else:
                return f"❌ Unbekannte Aktion: {action}. Erlaubt: check, add, remove"

        except Exception as e:
            return f"❌ Fehler: {str(e)}"

    def _manage_windows(self, action: str, path: str) -> str:
        from ce365.tools.sanitize import sanitize_powershell_string
        safe_path = sanitize_powershell_string(path)

        try:
            if action == "check":
                # File History Exclusions aus Registry prüfen
                ps_cmd = (
                    "Get-ItemProperty -Path "
                    "'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced' "
                    "-Name 'FileHistoryExclude' -ErrorAction SilentlyContinue | "
                    "Select-Object -ExpandProperty FileHistoryExclude"
                )
                result = subprocess.run(
                    ["powershell", "-Command", ps_cmd],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0 and result.stdout.strip():
                    exclusions = result.stdout.strip()
                    if safe_path.lower() in exclusions.lower():
                        return f"🚫 Pfad ist vom Backup AUSGESCHLOSSEN:\n   {path}"
                    else:
                        return (
                            f"✅ Pfad ist nicht explizit ausgeschlossen:\n   {path}\n\n"
                            f"Aktuelle Ausschlüsse:\n{exclusions[:500]}"
                        )
                else:
                    return (
                        f"ℹ️  Keine expliziten Backup-Ausschlüsse konfiguriert.\n"
                        f"   Pfad wird gesichert (sofern Backup aktiv): {path}\n\n"
                        f"💡 Ausschlüsse können auch in Settings → Backup verwaltet werden."
                    )

            elif action == "add":
                ps_cmd = (
                    f"$p = '{safe_path}'; "
                    "$key = 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\FileHistory\\Configuration'; "
                    "if (Test-Path $key) { "
                    "  $existing = (Get-ItemProperty $key -Name 'ExcludeFolders' -ErrorAction SilentlyContinue).ExcludeFolders; "
                    "  if ($existing) { $new = $existing + '|' + $p } else { $new = $p }; "
                    "  Set-ItemProperty $key -Name 'ExcludeFolders' -Value $new; "
                    "  Write-Output 'OK' "
                    "} else { Write-Output 'NO_FILE_HISTORY' }"
                )
                result = subprocess.run(
                    ["powershell", "-Command", ps_cmd],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if "OK" in result.stdout:
                    return (
                        f"✅ Pfad wurde vom Backup ausgeschlossen:\n"
                        f"   {path}\n\n"
                        f"ℹ️  Dieser Ordner wird beim nächsten Backup nicht mehr gesichert."
                    )
                elif "NO_FILE_HISTORY" in result.stdout:
                    return (
                        f"⚠️  File History ist nicht konfiguriert.\n\n"
                        f"Ausschlüsse können erst verwaltet werden, wenn File History aktiv ist.\n"
                        f"Aktivierung: Settings → Update & Security → Backup → Add a drive"
                    )
                else:
                    return f"❌ Fehler: {result.stderr[:300]}"

            elif action == "remove":
                ps_cmd = (
                    f"$p = '{safe_path}'; "
                    "$key = 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\FileHistory\\Configuration'; "
                    "if (Test-Path $key) { "
                    "  $existing = (Get-ItemProperty $key -Name 'ExcludeFolders' -ErrorAction SilentlyContinue).ExcludeFolders; "
                    "  if ($existing) { "
                    "    $new = ($existing -split '\\|' | Where-Object { $_ -ne $p }) -join '|'; "
                    "    Set-ItemProperty $key -Name 'ExcludeFolders' -Value $new; "
                    "    Write-Output 'OK' "
                    "  } else { Write-Output 'EMPTY' } "
                    "} else { Write-Output 'NO_FILE_HISTORY' }"
                )
                result = subprocess.run(
                    ["powershell", "-Command", ps_cmd],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if "OK" in result.stdout:
                    return (
                        f"✅ Pfad wird wieder vom Backup gesichert:\n"
                        f"   {path}\n\n"
                        f"ℹ️  Dieser Ordner wird beim nächsten Backup wieder eingeschlossen."
                    )
                elif "EMPTY" in result.stdout:
                    return f"ℹ️  Pfad war nicht ausgeschlossen: {path}"
                elif "NO_FILE_HISTORY" in result.stdout:
                    return "⚠️  File History ist nicht konfiguriert."
                else:
                    return f"❌ Fehler: {result.stderr[:300]}"

            else:
                return f"❌ Unbekannte Aktion: {action}. Erlaubt: check, add, remove"

        except Exception as e:
            return f"❌ Fehler: {str(e)}"


class ManageSnapshotsTool(RepairTool):
    """
    Verwaltet lokale Snapshots / Shadow Copies

    macOS: APFS Snapshots (tmutil)
    Windows: Volume Shadow Copies (vssadmin)
    """

    @property
    def name(self) -> str:
        return "manage_snapshots"

    @property
    def description(self) -> str:
        return (
            "Verwaltet lokale Snapshots — löschen oder ausdünnen um Speicher freizugeben. "
            "Nutze dies bei: 1) Speicherplatz freigeben durch Löschen alter Snapshots, "
            "2) Einzelnen Snapshot/Shadow Copy gezielt löschen, "
            "3) Automatisch Snapshots ausdünnen. "
            "Listet immer zuerst aktuelle Snapshots auf. "
            "macOS: APFS Snapshots. Windows: Volume Shadow Copies. "
            "Erfordert GO REPAIR!"
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["delete", "thin"],
                    "description": "Aktion: delete (einzelnen Snapshot löschen), thin (Snapshots ausdünnen / ältesten löschen)"
                },
                "snapshot_date": {
                    "type": "string",
                    "description": "macOS: Datum des Snapshots (YYYY-MM-DD-HHMMSS). Windows: Shadow Copy ID. Nur für action=delete."
                },
                "purge_amount_gb": {
                    "type": "number",
                    "description": "Menge in GB die freigemacht werden soll (macOS). Für Windows wird der älteste Shadow Copy gelöscht. Standard: 10",
                    "default": 10
                }
            },
            "required": ["action"]
        }

    async def execute(self, **kwargs) -> str:
        os_type = platform.system()
        if os_type == "Darwin":
            return self._manage_macos(kwargs)
        elif os_type == "Windows":
            return self._manage_windows(kwargs)
        else:
            return f"❌ Nicht unterstütztes OS: {os_type}"

    def _manage_macos(self, kwargs) -> str:
        action = kwargs.get("action", "")

        try:
            output = [
                "📸 Lokale APFS Snapshots",
                ""
            ]

            # Immer zuerst aktuelle Snapshots zeigen
            try:
                result = subprocess.run(
                    ["tmutil", "listlocalsnapshots", "/"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0 and result.stdout.strip():
                    snapshots = [
                        line.strip() for line in result.stdout.strip().split("\n")
                        if line.strip()
                    ]
                    output.append(f"Aktuelle Snapshots: {len(snapshots)}")
                    for snap in snapshots[:15]:
                        output.append(f"   • {snap}")
                    if len(snapshots) > 15:
                        output.append(f"   ... und {len(snapshots) - 15} weitere")
                else:
                    output.append("Keine lokalen Snapshots vorhanden")
                    return "\n".join(output)

            except Exception as e:
                output.append(f"⚠️  Snapshots konnten nicht aufgelistet werden: {str(e)}")

            output.append("")

            if action == "delete":
                snapshot_date = kwargs.get("snapshot_date", "")
                if not snapshot_date:
                    output.append("❌ Kein Snapshot-Datum angegeben")
                    output.append("   Bitte snapshot_date im Format YYYY-MM-DD-HHMMSS angeben")
                    return "\n".join(output)

                import re
                if not re.match(r'^\d{4}-\d{2}-\d{2}-\d{6}$', snapshot_date):
                    return f"❌ Ungültiges Datum-Format: {snapshot_date}. Erwartet: YYYY-MM-DD-HHMMSS"

                output.append(f"🗑️  Lösche Snapshot: {snapshot_date}...")
                result = subprocess.run(
                    ["tmutil", "deletelocalsnapshots", snapshot_date],
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                if result.returncode == 0:
                    output.append(f"   ✅ Snapshot {snapshot_date} wurde gelöscht")
                else:
                    error = result.stderr.strip() or result.stdout.strip()
                    output.append(f"   ❌ Fehler: {error[:300]}")

            elif action == "thin":
                purge_gb = kwargs.get("purge_amount_gb", 10)
                try:
                    purge_gb = float(purge_gb)
                    if purge_gb <= 0 or purge_gb > 500:
                        return "❌ purge_amount_gb muss zwischen 1 und 500 liegen"
                except (TypeError, ValueError):
                    purge_gb = 10

                purge_bytes = int(purge_gb * 1_000_000_000)

                output.append(f"🔄 Dünne Snapshots aus (Ziel: {purge_gb:.0f} GB freimachen)...")
                result = subprocess.run(
                    ["tmutil", "thinlocalsnapshots", "/", str(purge_bytes)],
                    capture_output=True,
                    text=True,
                    timeout=120
                )

                if result.returncode == 0:
                    output.append("   ✅ Snapshots wurden ausgedünnt")
                    if result.stdout.strip():
                        output.append(f"   {result.stdout.strip()[:300]}")
                else:
                    error = result.stderr.strip() or result.stdout.strip()
                    output.append(f"   ❌ Fehler: {error[:300]}")

            else:
                output.append(f"❌ Unbekannte Aktion: {action}. Erlaubt: delete, thin")

            return "\n".join(output)

        except Exception as e:
            return f"❌ Fehler: {str(e)}"

    def _manage_windows(self, kwargs) -> str:
        action = kwargs.get("action", "")

        try:
            output = [
                "📸 Volume Shadow Copies",
                ""
            ]

            # Immer zuerst aktuelle Shadow Copies zeigen
            try:
                result = subprocess.run(
                    ["vssadmin", "list", "shadows"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0 and result.stdout.strip():
                    vss_output = result.stdout.strip()
                    if "No items found" in vss_output:
                        output.append("Keine Shadow Copies vorhanden")
                        return "\n".join(output)

                    shadow_count = vss_output.count("Shadow Copy ID")
                    output.append(f"Aktuelle Shadow Copies: {shadow_count}")
                    output.append("")

                    for line in vss_output.split("\n"):
                        line = line.strip()
                        if line and ("Shadow Copy ID" in line or "Creation Time" in line
                                     or "Shadow Copy Volume" in line):
                            output.append(f"   {line}")
                else:
                    output.append("Keine Shadow Copies vorhanden")
                    return "\n".join(output)

            except Exception as e:
                output.append(f"⚠️  Shadow Copies konnten nicht aufgelistet werden: {str(e)}")

            output.append("")

            if action == "delete":
                shadow_id = kwargs.get("snapshot_date", "")
                if not shadow_id:
                    output.append("❌ Keine Shadow Copy ID angegeben")
                    output.append("   Bitte snapshot_date mit der Shadow Copy ID füllen")
                    return "\n".join(output)

                # ID validieren (GUID-Format)
                import re
                if not re.match(
                    r'^\{?[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\}?$',
                    shadow_id
                ):
                    return f"❌ Ungültige Shadow Copy ID: {shadow_id}"

                output.append(f"🗑️  Lösche Shadow Copy: {shadow_id}...")
                result = subprocess.run(
                    ["vssadmin", "delete", "shadows", f"/Shadow={shadow_id}", "/Quiet"],
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                if result.returncode == 0:
                    output.append("   ✅ Shadow Copy wurde gelöscht")
                else:
                    error = result.stderr.strip() or result.stdout.strip()
                    output.append(f"   ❌ Fehler: {error[:300]}")

            elif action == "thin":
                output.append("🔄 Lösche älteste Shadow Copy...")
                result = subprocess.run(
                    ["vssadmin", "delete", "shadows", "/for=C:", "/oldest", "/Quiet"],
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                if result.returncode == 0:
                    output.append("   ✅ Älteste Shadow Copy wurde gelöscht")
                else:
                    error = result.stderr.strip() or result.stdout.strip()
                    output.append(f"   ❌ Fehler: {error[:300]}")

                # Speicher-Info anzeigen
                try:
                    storage_result = subprocess.run(
                        ["vssadmin", "list", "shadowstorage"],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    if storage_result.returncode == 0:
                        output.append("")
                        output.append("📊 Shadow Storage:")
                        for line in storage_result.stdout.split("\n"):
                            line = line.strip()
                            if line and ("Used" in line or "Allocated" in line or "Maximum" in line):
                                output.append(f"   {line}")
                except Exception:
                    pass

            else:
                output.append(f"❌ Unbekannte Aktion: {action}. Erlaubt: delete, thin")

            return "\n".join(output)

        except Exception as e:
            return f"❌ Fehler: {str(e)}"

"""
CE365 Agent - Backup Status Check Tools

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
Licensed under Source Available License

Backup-Status prüfen:
- Windows: Windows Backup, System Restore Points
- macOS: Time Machine, APFS Snapshots
"""

import platform
import re
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
            return f"❌ Fehler beim Windows-Backup-Check: {str(e)}"

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


class ListBackupsTool(AuditTool):
    """
    Listet alle Backups und Snapshots auf

    macOS: Time Machine Backups + APFS Snapshots
    Windows: Windows Backup Versionen + Shadow Copies
    """

    @property
    def name(self) -> str:
        return "list_backups"

    @property
    def description(self) -> str:
        return (
            "Listet alle vorhandenen Backups und Snapshots auf. "
            "Nutze dies bei: 1) Übersicht über vorhandene Backups, "
            "2) Prüfen wie viele Backups/Restore Points existieren, "
            "3) Ältestes/neuestes Backup ermitteln. "
            "macOS: Time Machine + APFS Snapshots. "
            "Windows: Windows Backup Versionen + Volume Shadow Copies."
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
            return self._list_macos()
        elif os_type == "Windows":
            return self._list_windows()
        else:
            return f"❌ Nicht unterstütztes OS: {os_type}"

    def _list_macos(self) -> str:
        try:
            output = [
                "📋 Time Machine Backups",
                ""
            ]

            # 1. Alle Backups auflisten
            try:
                result = subprocess.run(
                    ["tmutil", "listbackups"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0 and result.stdout.strip():
                    backups = result.stdout.strip().split("\n")
                    output.append(f"💾 Gefundene Backups: {len(backups)}")
                    output.append("")

                    if len(backups) > 10:
                        output.append("   Älteste 3:")
                        for b in backups[:3]:
                            output.append(f"   • {b}")
                        output.append(f"   ... ({len(backups) - 6} weitere) ...")
                        output.append("   Neueste 3:")
                        for b in backups[-3:]:
                            output.append(f"   • {b}")
                    else:
                        for b in backups:
                            output.append(f"   • {b}")

                    # Alter des ältesten/neuesten Backups
                    date_pattern = r'(\d{4}-\d{2}-\d{2}-\d{6})'
                    oldest_match = re.search(date_pattern, backups[0])
                    newest_match = re.search(date_pattern, backups[-1])

                    output.append("")
                    if oldest_match:
                        try:
                            oldest_date = datetime.strptime(oldest_match.group(1), "%Y-%m-%d-%H%M%S")
                            days_old = (datetime.now() - oldest_date).days
                            output.append(f"   📅 Ältestes Backup: vor {days_old} Tagen")
                        except ValueError:
                            pass
                    if newest_match:
                        try:
                            newest_date = datetime.strptime(newest_match.group(1), "%Y-%m-%d-%H%M%S")
                            days_new = (datetime.now() - newest_date).days
                            if days_new == 0:
                                output.append("   📅 Neuestes Backup: heute")
                            elif days_new == 1:
                                output.append("   📅 Neuestes Backup: gestern")
                            else:
                                output.append(f"   📅 Neuestes Backup: vor {days_new} Tagen")
                        except ValueError:
                            pass
                else:
                    output.append("💾 Keine Time Machine Backups gefunden")
                    if result.stderr.strip():
                        output.append(f"   ℹ️  {result.stderr.strip()[:200]}")

            except subprocess.TimeoutExpired:
                output.append("💾 Timeout beim Auflisten der Backups")
            except Exception as e:
                output.append(f"💾 Fehler: {str(e)}")

            output.append("")

            # 2. Lokale APFS Snapshots
            try:
                result = subprocess.run(
                    ["tmutil", "listlocalsnapshots", "/"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0 and result.stdout.strip():
                    snapshots = [
                        line for line in result.stdout.strip().split("\n")
                        if line.strip()
                    ]
                    output.append(f"📸 Lokale APFS Snapshots: {len(snapshots)}")
                    for snap in snapshots[:10]:
                        output.append(f"   • {snap}")
                    if len(snapshots) > 10:
                        output.append(f"   ... und {len(snapshots) - 10} weitere")
                else:
                    output.append("📸 Keine lokalen Snapshots gefunden")

            except Exception as e:
                output.append(f"📸 Snapshots konnten nicht ermittelt werden: {str(e)}")

            output.append("")
            output.append("─" * 50)
            output.append("💡 Weitere Tools:")
            output.append("   • verify_backup — Backup-Integrität prüfen")
            output.append("   • manage_snapshots — Snapshots verwalten/löschen")

            return "\n".join(output)

        except Exception as e:
            return f"❌ Fehler: {str(e)}"

    def _list_windows(self) -> str:
        try:
            output = [
                "📋 Windows Backup Übersicht",
                ""
            ]

            # 1. Windows Backup Versionen (wbadmin)
            try:
                result = subprocess.run(
                    ["wbadmin", "get", "versions"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0 and result.stdout.strip():
                    versions = result.stdout.strip()
                    if "No backups found" in versions or "ERROR" in versions:
                        output.append("💾 Windows Backup:")
                        output.append("   ❌ Keine Backup-Versionen gefunden")
                    else:
                        output.append("💾 Windows Backup Versionen:")
                        count = 0
                        for line in versions.split("\n"):
                            line = line.strip()
                            if line and ("Version" in line or "Time" in line or "Location" in line):
                                output.append(f"   {line}")
                                if "Version" in line:
                                    count += 1
                        output.append("")
                        output.append(f"   ✓ {count} Backup-Version(en) gefunden")
                else:
                    output.append("💾 Windows Backup:")
                    output.append("   ❌ Keine Backups vorhanden oder wbadmin nicht verfügbar")

            except Exception as e:
                output.append(f"💾 Windows Backup: ⚠️  {str(e)}")

            output.append("")

            # 2. Volume Shadow Copies
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
                        output.append("📸 Volume Shadow Copies:")
                        output.append("   Keine Shadow Copies vorhanden")
                    else:
                        shadow_count = vss_output.count("Shadow Copy ID")
                        output.append(f"📸 Volume Shadow Copies: {shadow_count}")
                        output.append("")
                        # Zeige die letzten Einträge
                        lines = vss_output.split("\n")
                        shown = 0
                        for line in lines:
                            line = line.strip()
                            if line and ("Creation Time" in line or "Shadow Copy Volume" in line
                                         or "Shadow Copy ID" in line):
                                output.append(f"   {line}")
                                if "Creation Time" in line:
                                    shown += 1
                                if shown >= 5:
                                    if shadow_count > 5:
                                        output.append(f"   ... und {shadow_count - 5} weitere")
                                    break
                else:
                    output.append("📸 Volume Shadow Copies:")
                    output.append("   ⚠️  Konnte nicht ermittelt werden")

            except Exception as e:
                output.append(f"📸 Shadow Copies: ⚠️  {str(e)}")

            output.append("")
            output.append("─" * 50)
            output.append("💡 Weitere Tools:")
            output.append("   • verify_backup — Backup-Integrität prüfen")
            output.append("   • manage_snapshots — Shadow Copies verwalten")

            return "\n".join(output)

        except Exception as e:
            return f"❌ Fehler: {str(e)}"


class VerifyBackupTool(AuditTool):
    """
    Verifiziert die Integrität des letzten Backups

    macOS: Time Machine Checksum-Verifizierung + Backup-Größe
    Windows: Windows Backup Inhalt prüfen + Shadow Copy Status
    """

    @property
    def name(self) -> str:
        return "verify_backup"

    @property
    def description(self) -> str:
        return (
            "Prüft die Integrität des letzten Backups. "
            "Nutze dies bei: 1) Verdacht auf defektes Backup, "
            "2) Nach Festplattenproblemen, "
            "3) Regelmäßige Backup-Verifizierung. "
            "macOS: Checksum-Verifikation + Backup-Größe. "
            "Windows: Backup-Inhalt + Shadow Copy Speicher."
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
            return self._verify_macos()
        elif os_type == "Windows":
            return self._verify_windows()
        else:
            return f"❌ Nicht unterstütztes OS: {os_type}"

    def _verify_macos(self) -> str:
        try:
            output = [
                "🔍 Time Machine Backup Verifizierung",
                ""
            ]

            # Letztes Backup ermitteln
            result = subprocess.run(
                ["tmutil", "latestbackup"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0 or not result.stdout.strip():
                return (
                    "❌ Kein Time Machine Backup gefunden\n\n"
                    "Time Machine ist nicht konfiguriert oder es wurde noch kein Backup erstellt."
                )

            latest_backup = result.stdout.strip()
            output.append(f"📦 Letztes Backup: {latest_backup}")
            output.append("")

            # 1. Checksum-Verifizierung
            output.append("🔐 Checksum-Verifizierung...")
            try:
                result = subprocess.run(
                    ["tmutil", "verifychecksums", latest_backup],
                    capture_output=True,
                    text=True,
                    timeout=300
                )

                if result.returncode == 0:
                    output.append("   ✅ Checksums sind gültig — Backup ist intakt")
                    if result.stdout.strip():
                        for line in result.stdout.strip().split("\n")[:5]:
                            output.append(f"   {line.strip()}")
                else:
                    output.append("   ⚠️  Checksum-Verifizierung fehlgeschlagen")
                    error = result.stderr.strip() or result.stdout.strip()
                    if error:
                        output.append(f"   {error[:300]}")

            except subprocess.TimeoutExpired:
                output.append("   ⏱️  Timeout — Verifizierung dauert zu lange (>5 Min)")
                output.append("   Tipp: Manuell ausführen: tmutil verifychecksums <backup-pfad>")
            except Exception as e:
                output.append(f"   ⚠️  Fehler: {str(e)}")

            output.append("")

            # 2. Einzigartige Größe
            output.append("📊 Einzigartige Backup-Größe...")
            try:
                result = subprocess.run(
                    ["tmutil", "uniquesize", latest_backup],
                    capture_output=True,
                    text=True,
                    timeout=120
                )

                if result.returncode == 0 and result.stdout.strip():
                    output.append(f"   {result.stdout.strip()}")
                else:
                    output.append("   ℹ️  Größe konnte nicht ermittelt werden")
                    if result.stderr.strip():
                        output.append(f"   {result.stderr.strip()[:200]}")

            except subprocess.TimeoutExpired:
                output.append("   ⏱️  Timeout bei Größenberechnung")
            except Exception as e:
                output.append(f"   ⚠️  Fehler: {str(e)}")

            output.append("")
            output.append("─" * 50)
            output.append("💡 Bei Problemen:")
            output.append("   • Backup-Laufwerk auf Fehler prüfen (Festplattendienstprogramm)")
            output.append("   • Neues Backup erstellen: trigger_backup")

            return "\n".join(output)

        except Exception as e:
            return f"❌ Fehler bei der Backup-Verifizierung: {str(e)}"

    def _verify_windows(self) -> str:
        try:
            output = [
                "🔍 Windows Backup Verifizierung",
                ""
            ]

            # 1. Letzte Backup-Version ermitteln
            try:
                result = subprocess.run(
                    ["wbadmin", "get", "versions"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode != 0 or "No backups found" in result.stdout:
                    return (
                        "❌ Kein Windows Backup gefunden\n\n"
                        "Windows Backup ist nicht konfiguriert oder es wurde noch kein Backup erstellt."
                    )

                # Letzte Version-ID extrahieren
                version_id = None
                for line in result.stdout.split("\n"):
                    if "Version identifier" in line:
                        version_id = line.split(":")[-1].strip()

                if not version_id:
                    output.append("⚠️  Keine Backup-Version gefunden")
                    return "\n".join(output)

                output.append(f"📦 Letzte Backup-Version: {version_id}")
                output.append("")

            except Exception as e:
                return f"❌ Fehler beim Ermitteln der Backup-Version: {str(e)}"

            # 2. Backup-Inhalt prüfen
            output.append("🔐 Prüfe Backup-Inhalt...")
            try:
                result = subprocess.run(
                    ["wbadmin", "get", "items", f"-version:{version_id}"],
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                if result.returncode == 0 and result.stdout.strip():
                    items_output = result.stdout.strip()
                    item_count = items_output.count("Item")
                    output.append(f"   ✅ Backup-Inhalt lesbar ({item_count} Element(e))")

                    for line in items_output.split("\n")[:10]:
                        line = line.strip()
                        if line and ("Volume" in line or "Application" in line or "Item" in line):
                            output.append(f"   {line}")
                else:
                    output.append("   ⚠️  Backup-Inhalt konnte nicht gelesen werden")
                    if result.stderr.strip():
                        output.append(f"   {result.stderr.strip()[:200]}")

            except subprocess.TimeoutExpired:
                output.append("   ⏱️  Timeout bei Inhaltsprüfung")
            except Exception as e:
                output.append(f"   ⚠️  Fehler: {str(e)}")

            output.append("")

            # 3. Shadow Copy Speicher prüfen
            output.append("📊 Shadow Copy Speicher...")
            try:
                result = subprocess.run(
                    ["vssadmin", "list", "shadowstorage"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0 and result.stdout.strip():
                    for line in result.stdout.strip().split("\n"):
                        line = line.strip()
                        if line and ("Used" in line or "Allocated" in line or "Maximum" in line):
                            output.append(f"   {line}")
                else:
                    output.append("   ℹ️  Shadow Storage konnte nicht ermittelt werden")

            except Exception as e:
                output.append(f"   ⚠️  Fehler: {str(e)}")

            output.append("")
            output.append("─" * 50)
            output.append("💡 Bei Problemen:")
            output.append("   • chkdsk /f auf dem Backup-Laufwerk ausführen")
            output.append("   • Neues Backup erstellen: trigger_backup")

            return "\n".join(output)

        except Exception as e:
            return f"❌ Fehler bei der Backup-Verifizierung: {str(e)}"

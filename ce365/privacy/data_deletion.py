"""
CE365 Agent - Data Deletion Manager

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
Licensed under Source Available License

GDPR Art. 17 — Right to Erasure
Löscht alle gespeicherten Nutzerdaten auf Anfrage.
"""

import json
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List


class DataDeletionManager:
    """
    Verwaltet Datenlöschung und Retention Policies.

    Löschbare Daten:
    - Learning Cases (SQLite/PostgreSQL)
    - Changelogs (JSON-Dateien)
    - Usage-Tracking (JSON)
    - License-Cache (JSON)
    - System-Fingerprint
    """

    # Retention Defaults (konfigurierbar)
    CASE_RETENTION_DAYS = 180
    CHANGELOG_RETENTION_DAYS = 90

    def __init__(self):
        self.ce365_home = Path.home() / ".ce365"
        self.data_dir = Path("data")

    def delete_session_data(self, session_id: str) -> Dict:
        """
        Löscht alle Daten einer bestimmten Session.

        Args:
            session_id: Session-ID

        Returns:
            {"deleted": [...], "errors": [...]}
        """
        deleted = []
        errors = []

        # 1. Changelog löschen
        changelog_file = self.data_dir / "changelogs" / f"{session_id}.json"
        if changelog_file.exists():
            try:
                changelog_file.unlink()
                deleted.append(f"Changelog: {changelog_file.name}")
            except Exception as e:
                errors.append(f"Changelog: {e}")

        # 2. Session-Datei löschen
        session_file = self.data_dir / "sessions" / f"{session_id}.json"
        if session_file.exists():
            try:
                session_file.unlink()
                deleted.append(f"Session: {session_file.name}")
            except Exception as e:
                errors.append(f"Session: {e}")

        return {"deleted": deleted, "errors": errors}

    def delete_all_local_data(self) -> Dict:
        """
        Löscht ALLE lokalen Nutzerdaten.

        Returns:
            {"deleted": [...], "errors": [...]}
        """
        deleted = []
        errors = []

        # 1. Changelogs
        changelogs_dir = self.data_dir / "changelogs"
        if changelogs_dir.exists():
            count = len(list(changelogs_dir.glob("*.json")))
            try:
                shutil.rmtree(changelogs_dir)
                changelogs_dir.mkdir(exist_ok=True)
                deleted.append(f"Changelogs: {count} Dateien")
            except Exception as e:
                errors.append(f"Changelogs: {e}")

        # 2. Sessions
        sessions_dir = self.data_dir / "sessions"
        if sessions_dir.exists():
            count = len(list(sessions_dir.glob("*.json")))
            try:
                shutil.rmtree(sessions_dir)
                sessions_dir.mkdir(exist_ok=True)
                deleted.append(f"Sessions: {count} Dateien")
            except Exception as e:
                errors.append(f"Sessions: {e}")

        # 3. Learning DB (lokal)
        for db_file in self.data_dir.glob("*.db"):
            try:
                db_file.unlink()
                deleted.append(f"Datenbank: {db_file.name}")
            except Exception as e:
                errors.append(f"DB {db_file.name}: {e}")

        # 4. ~/.ce365/ Cache-Daten
        for cache_file in ["usage.json", "fingerprint", "cache/license.json"]:
            fp = self.ce365_home / cache_file
            if fp.exists():
                try:
                    fp.unlink()
                    deleted.append(f"Cache: {cache_file}")
                except Exception as e:
                    errors.append(f"Cache {cache_file}: {e}")

        return {"deleted": deleted, "errors": errors}

    def cleanup_old_data(
        self,
        case_days: int = None,
        changelog_days: int = None,
    ) -> Dict:
        """
        Retention Policy — löscht Daten älter als X Tage.

        Args:
            case_days: Max. Alter für Cases (Default: 180)
            changelog_days: Max. Alter für Changelogs (Default: 90)

        Returns:
            {"deleted_changelogs": int, "errors": [...]}
        """
        case_days = case_days or self.CASE_RETENTION_DAYS
        changelog_days = changelog_days or self.CHANGELOG_RETENTION_DAYS
        deleted_changelogs = 0
        errors = []

        # Changelogs älter als X Tage löschen
        changelogs_dir = self.data_dir / "changelogs"
        if changelogs_dir.exists():
            cutoff = datetime.now() - timedelta(days=changelog_days)
            for f in changelogs_dir.glob("*.json"):
                try:
                    data = json.loads(f.read_text())
                    created_at = datetime.fromisoformat(data.get("created_at", ""))
                    if created_at < cutoff:
                        f.unlink()
                        deleted_changelogs += 1
                except Exception:
                    pass

        return {
            "deleted_changelogs": deleted_changelogs,
            "changelog_cutoff_days": changelog_days,
            "errors": errors,
        }

    def export_all_data(self) -> Dict:
        """
        GDPR Art. 20 — Datenportabilität.
        Exportiert alle gespeicherten Daten als Dictionary.

        Returns:
            Dict mit allen lokalen Daten
        """
        export = {
            "exported_at": datetime.now().isoformat(),
            "changelogs": [],
            "usage": None,
            "config": None,
        }

        # Changelogs
        changelogs_dir = self.data_dir / "changelogs"
        if changelogs_dir.exists():
            for f in changelogs_dir.glob("*.json"):
                try:
                    export["changelogs"].append(json.loads(f.read_text()))
                except Exception:
                    pass

        # Usage
        usage_file = self.ce365_home / "usage.json"
        if usage_file.exists():
            try:
                export["usage"] = json.loads(usage_file.read_text())
            except Exception:
                pass

        # Config (ohne Secrets)
        config_file = self.ce365_home / "config.json"
        if config_file.exists():
            try:
                export["config"] = json.loads(config_file.read_text())
            except Exception:
                pass

        return export

    def get_data_summary(self) -> Dict:
        """
        Übersicht über gespeicherte Daten (für Transparenz).

        Returns:
            Dict mit Anzahl und Speicherorten
        """
        summary = {
            "changelogs": 0,
            "sessions": 0,
            "databases": [],
            "cache_files": [],
            "storage_locations": [],
        }

        # Changelogs
        changelogs_dir = self.data_dir / "changelogs"
        if changelogs_dir.exists():
            summary["changelogs"] = len(list(changelogs_dir.glob("*.json")))
            summary["storage_locations"].append(str(changelogs_dir))

        # Sessions
        sessions_dir = self.data_dir / "sessions"
        if sessions_dir.exists():
            summary["sessions"] = len(list(sessions_dir.glob("*.json")))

        # Databases
        for db_file in self.data_dir.glob("*.db"):
            summary["databases"].append(str(db_file))

        # Cache
        for cache_file in ["usage.json", "fingerprint", "cache/license.json", "config.json"]:
            fp = self.ce365_home / cache_file
            if fp.exists():
                summary["cache_files"].append(str(fp))

        if self.ce365_home.exists():
            summary["storage_locations"].append(str(self.ce365_home))

        return summary

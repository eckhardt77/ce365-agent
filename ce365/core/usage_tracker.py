"""
CE365 Agent - Usage Tracker

Zählt Repair-Runs pro Monat.
Community: max 5/Monat, Pro: unbegrenzt.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict


class UsageTracker:
    """Tracked Repair-Tool-Nutzung pro Monat"""

    COMMUNITY_MONTHLY_LIMIT = 5

    def __init__(self, edition: str = "community"):
        self.edition = edition
        self.usage_file = Path.home() / ".ce365" / "usage.json"
        self.usage_file.parent.mkdir(parents=True, exist_ok=True)
        self._usage = self._load()

    def _current_month_key(self) -> str:
        """Aktueller Monat als Key (YYYY-MM)"""
        return datetime.now().strftime("%Y-%m")

    def _load(self) -> Dict:
        """Lädt Usage-Daten"""
        if not self.usage_file.exists():
            return {}
        try:
            return json.loads(self.usage_file.read_text())
        except Exception:
            return {}

    def _save(self):
        """Speichert Usage-Daten (mit restriktiven Berechtigungen)"""
        try:
            self.usage_file.write_text(json.dumps(self._usage, indent=2))
            os.chmod(self.usage_file, 0o600)
        except Exception:
            pass

    def get_repair_count(self) -> int:
        """Aktuelle Repair-Runs diesen Monat"""
        key = self._current_month_key()
        return self._usage.get(key, {}).get("repair_runs", 0)

    def get_remaining(self) -> int:
        """Verbleibende Repair-Runs (Community)"""
        if self.edition != "community":
            return -1  # Unbegrenzt
        return max(0, self.COMMUNITY_MONTHLY_LIMIT - self.get_repair_count())

    def can_run_repair(self) -> bool:
        """Prüft ob Repair-Run erlaubt ist"""
        if self.edition != "community":
            return True
        return self.get_repair_count() < self.COMMUNITY_MONTHLY_LIMIT

    def increment_repair(self):
        """Zählt einen Repair-Run"""
        key = self._current_month_key()
        if key not in self._usage:
            self._usage[key] = {"repair_runs": 0}
        self._usage[key]["repair_runs"] += 1
        self._save()

    def get_limit_message(self) -> str:
        """Limit-Nachricht für Community"""
        count = self.get_repair_count()
        remaining = self.get_remaining()
        return (
            f"Repair-Limit erreicht ({count}/{self.COMMUNITY_MONTHLY_LIMIT} diesen Monat). "
            f"Upgrade auf Pro für unbegrenzte Repairs."
        ) if remaining <= 0 else (
            f"Repair-Runs: {count}/{self.COMMUNITY_MONTHLY_LIMIT} diesen Monat "
            f"({remaining} verbleibend)"
        )

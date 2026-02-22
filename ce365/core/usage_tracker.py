"""
CE365 Agent - Usage Tracker

Free: 1 Repair TOTAL, 5 Sessions/Monat.
Core/Scale: unbegrenzt.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict


class UsageTracker:
    """Tracked Repair- und Session-Nutzung"""

    FREE_REPAIR_TOTAL_LIMIT = 1
    FREE_SESSION_MONTHLY_LIMIT = 5

    def __init__(self, edition: str = "free"):
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

    # === Repair Tracking ===

    def get_repair_count_total(self) -> int:
        """Gesamte Repair-Runs (alle Monate, für Free-Limit)"""
        total = 0
        for month_data in self._usage.values():
            if isinstance(month_data, dict):
                total += month_data.get("repair_runs", 0)
        return total

    def get_repair_count(self) -> int:
        """Aktuelle Repair-Runs diesen Monat"""
        key = self._current_month_key()
        return self._usage.get(key, {}).get("repair_runs", 0)

    def get_remaining(self) -> int:
        """Verbleibende Repair-Runs (Free: 1 total)"""
        if self.edition != "free":
            return -1  # Unbegrenzt
        return max(0, self.FREE_REPAIR_TOTAL_LIMIT - self.get_repair_count_total())

    def can_run_repair(self) -> bool:
        """Prüft ob Repair-Run erlaubt ist"""
        if self.edition != "free":
            return True
        return self.get_repair_count_total() < self.FREE_REPAIR_TOTAL_LIMIT

    def increment_repair(self):
        """Zählt einen Repair-Run"""
        key = self._current_month_key()
        if key not in self._usage:
            self._usage[key] = {"repair_runs": 0, "sessions": 0}
        self._usage[key]["repair_runs"] += 1
        self._save()

    def get_limit_message(self) -> str:
        """Limit-Nachricht für Free"""
        total = self.get_repair_count_total()
        remaining = self.get_remaining()
        return (
            f"Repair-Limit erreicht ({total}/{self.FREE_REPAIR_TOTAL_LIMIT} insgesamt). "
            f"Upgrade auf MSP Core für unbegrenzte Repairs."
        ) if remaining <= 0 else (
            f"Repair-Runs: {total}/{self.FREE_REPAIR_TOTAL_LIMIT} insgesamt "
            f"({remaining} verbleibend)"
        )

    # === Session Tracking ===

    def get_session_count(self) -> int:
        """Sessions diesen Monat"""
        key = self._current_month_key()
        return self._usage.get(key, {}).get("sessions", 0)

    def get_session_remaining(self) -> int:
        """Verbleibende Sessions (Free: 5/Monat)"""
        if self.edition != "free":
            return -1  # Unbegrenzt
        return max(0, self.FREE_SESSION_MONTHLY_LIMIT - self.get_session_count())

    def can_start_session(self) -> bool:
        """Prüft ob neue Session gestartet werden darf"""
        if self.edition != "free":
            return True
        return self.get_session_count() < self.FREE_SESSION_MONTHLY_LIMIT

    def increment_session(self):
        """Zählt eine Session"""
        key = self._current_month_key()
        if key not in self._usage:
            self._usage[key] = {"repair_runs": 0, "sessions": 0}
        if "sessions" not in self._usage[key]:
            self._usage[key]["sessions"] = 0
        self._usage[key]["sessions"] += 1
        self._save()

    def get_session_limit_message(self) -> str:
        """Session-Limit-Nachricht für Free"""
        count = self.get_session_count()
        remaining = self.get_session_remaining()
        return (
            f"Session-Limit erreicht ({count}/{self.FREE_SESSION_MONTHLY_LIMIT} diesen Monat). "
            f"Upgrade auf MSP Core für unbegrenzte Sessions."
        ) if remaining <= 0 else (
            f"Sessions: {count}/{self.FREE_SESSION_MONTHLY_LIMIT} diesen Monat "
            f"({remaining} verbleibend)"
        )

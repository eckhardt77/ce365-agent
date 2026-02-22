"""
Tests für UsageTracker — Session- und Repair-Limits pro Edition
"""

import json
import pytest
from pathlib import Path
from ce365.core.usage_tracker import UsageTracker


@pytest.fixture
def free_tracker(tmp_path):
    """UsageTracker für Free Edition mit temp-Verzeichnis"""
    tracker = UsageTracker(edition="free")
    tracker.usage_file = tmp_path / ".ce365" / "usage.json"
    tracker.usage_file.parent.mkdir(parents=True, exist_ok=True)
    tracker._usage = {}
    return tracker


@pytest.fixture
def core_tracker(tmp_path):
    """UsageTracker für Core Edition"""
    tracker = UsageTracker(edition="core")
    tracker.usage_file = tmp_path / ".ce365" / "usage.json"
    tracker.usage_file.parent.mkdir(parents=True, exist_ok=True)
    tracker._usage = {}
    return tracker


@pytest.fixture
def scale_tracker(tmp_path):
    """UsageTracker für Scale Edition"""
    tracker = UsageTracker(edition="scale")
    tracker.usage_file = tmp_path / ".ce365" / "usage.json"
    tracker.usage_file.parent.mkdir(parents=True, exist_ok=True)
    tracker._usage = {}
    return tracker


# === Repair Limits ===

class TestFreeRepairLimits:
    """Free: 1 Repair TOTAL (nicht monatlich)"""

    def test_initial_can_repair(self, free_tracker):
        assert free_tracker.can_run_repair() is True

    def test_one_repair_allowed(self, free_tracker):
        free_tracker.increment_repair()
        assert free_tracker.can_run_repair() is False

    def test_remaining_starts_at_one(self, free_tracker):
        assert free_tracker.get_remaining() == 1

    def test_remaining_zero_after_repair(self, free_tracker):
        free_tracker.increment_repair()
        assert free_tracker.get_remaining() == 0

    def test_total_count_across_months(self, free_tracker):
        """Repair-Total zählt über alle Monate hinweg"""
        free_tracker._usage = {
            "2026-01": {"repair_runs": 0, "sessions": 3},
            "2026-02": {"repair_runs": 1, "sessions": 2},
        }
        assert free_tracker.get_repair_count_total() == 1
        assert free_tracker.can_run_repair() is False

    def test_limit_message_when_exhausted(self, free_tracker):
        free_tracker.increment_repair()
        msg = free_tracker.get_limit_message()
        assert "Limit erreicht" in msg
        assert "MSP Core" in msg

    def test_limit_message_when_remaining(self, free_tracker):
        msg = free_tracker.get_limit_message()
        assert "1" in msg
        assert "verbleibend" in msg


class TestCoreRepairLimits:
    """Core: Unbegrenzte Repairs"""

    def test_always_can_repair(self, core_tracker):
        for _ in range(100):
            core_tracker.increment_repair()
        assert core_tracker.can_run_repair() is True

    def test_remaining_is_unlimited(self, core_tracker):
        assert core_tracker.get_remaining() == -1


class TestScaleRepairLimits:
    """Scale: Unbegrenzte Repairs"""

    def test_always_can_repair(self, scale_tracker):
        assert scale_tracker.can_run_repair() is True

    def test_remaining_is_unlimited(self, scale_tracker):
        assert scale_tracker.get_remaining() == -1


# === Session Limits ===

class TestFreeSessionLimits:
    """Free: 5 Sessions/Monat"""

    def test_initial_can_start(self, free_tracker):
        assert free_tracker.can_start_session() is True

    def test_five_sessions_allowed(self, free_tracker):
        for _ in range(5):
            assert free_tracker.can_start_session() is True
            free_tracker.increment_session()
        assert free_tracker.can_start_session() is False

    def test_session_remaining(self, free_tracker):
        assert free_tracker.get_session_remaining() == 5
        free_tracker.increment_session()
        free_tracker.increment_session()
        assert free_tracker.get_session_remaining() == 3

    def test_session_count(self, free_tracker):
        assert free_tracker.get_session_count() == 0
        free_tracker.increment_session()
        assert free_tracker.get_session_count() == 1

    def test_session_limit_message_exhausted(self, free_tracker):
        for _ in range(5):
            free_tracker.increment_session()
        msg = free_tracker.get_session_limit_message()
        assert "Limit erreicht" in msg
        assert "MSP Core" in msg

    def test_session_limit_message_remaining(self, free_tracker):
        free_tracker.increment_session()
        msg = free_tracker.get_session_limit_message()
        assert "4 verbleibend" in msg


class TestCoreSessionLimits:
    """Core: Unbegrenzte Sessions"""

    def test_always_can_start(self, core_tracker):
        for _ in range(100):
            core_tracker.increment_session()
        assert core_tracker.can_start_session() is True

    def test_remaining_is_unlimited(self, core_tracker):
        assert core_tracker.get_session_remaining() == -1


class TestScaleSessionLimits:
    """Scale: Unbegrenzte Sessions"""

    def test_always_can_start(self, scale_tracker):
        assert scale_tracker.can_start_session() is True

    def test_remaining_is_unlimited(self, scale_tracker):
        assert scale_tracker.get_session_remaining() == -1


# === Persistence ===

class TestPersistence:
    """Usage-Daten werden korrekt gespeichert und geladen"""

    def test_save_and_reload(self, tmp_path):
        tracker1 = UsageTracker(edition="free")
        tracker1.usage_file = tmp_path / ".ce365" / "usage.json"
        tracker1.usage_file.parent.mkdir(parents=True, exist_ok=True)
        tracker1._usage = {}

        tracker1.increment_session()
        tracker1.increment_repair()

        # Neuer Tracker lädt die gespeicherten Daten
        tracker2 = UsageTracker(edition="free")
        tracker2.usage_file = tracker1.usage_file
        tracker2._usage = tracker2._load()

        assert tracker2.get_session_count() == 1
        assert tracker2.get_repair_count() == 1

    def test_corrupt_file_returns_empty(self, tmp_path):
        usage_file = tmp_path / ".ce365" / "usage.json"
        usage_file.parent.mkdir(parents=True, exist_ok=True)
        usage_file.write_text("not valid json!!!")

        tracker = UsageTracker(edition="free")
        tracker.usage_file = usage_file
        tracker._usage = tracker._load()
        assert tracker._usage == {}

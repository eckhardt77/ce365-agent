"""
Tests fuer ChangelogWriter — duration_ms, snapshot_before, snapshot_after
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from ce365.storage.changelog import ChangelogEntry, ChangelogWriter


@pytest.fixture
def changelog_writer(tmp_path):
    """ChangelogWriter mit temporaerem Verzeichnis"""
    with patch("ce365.storage.changelog.get_settings") as mock_settings:
        settings = MagicMock()
        settings.changelogs_dir = tmp_path / "changelogs"
        mock_settings.return_value = settings
        writer = ChangelogWriter("test-session-123")
    return writer


class TestChangelogEntry:
    """Tests fuer ChangelogEntry Dataclass"""

    def test_default_fields(self):
        entry = ChangelogEntry(
            timestamp="2026-02-22T14:00:00",
            tool_name="test_tool",
            tool_input={"key": "value"},
            result="OK",
            success=True,
        )
        assert entry.duration_ms == 0
        assert entry.snapshot_before == ""
        assert entry.snapshot_after == ""

    def test_with_duration(self):
        entry = ChangelogEntry(
            timestamp="2026-02-22T14:00:00",
            tool_name="test_tool",
            tool_input={},
            result="OK",
            success=True,
            duration_ms=1234,
        )
        assert entry.duration_ms == 1234

    def test_with_snapshots(self):
        entry = ChangelogEntry(
            timestamp="2026-02-22T14:00:00",
            tool_name="cleanup_disk",
            tool_input={},
            result="OK",
            success=True,
            snapshot_before="Disk 97% belegt",
            snapshot_after="Disk 72% belegt",
        )
        assert entry.snapshot_before == "Disk 97% belegt"
        assert entry.snapshot_after == "Disk 72% belegt"


class TestChangelogWriterAddEntry:
    """Tests fuer add_entry mit neuen Feldern"""

    def test_add_entry_with_duration(self, changelog_writer):
        changelog_writer.add_entry(
            tool_name="get_system_info",
            tool_input={},
            result="System OK",
            success=True,
            duration_ms=500,
        )
        assert len(changelog_writer.entries) == 1
        assert changelog_writer.entries[0].duration_ms == 500

    def test_add_entry_with_snapshots(self, changelog_writer):
        changelog_writer.add_entry(
            tool_name="cleanup_disk",
            tool_input={"action": "cleanup"},
            result="45 GB freigeraeumt",
            success=True,
            duration_ms=3200,
            snapshot_before="Disk 97% belegt",
            snapshot_after="Disk 72% belegt",
        )
        entry = changelog_writer.entries[0]
        assert entry.snapshot_before == "Disk 97% belegt"
        assert entry.snapshot_after == "Disk 72% belegt"
        assert entry.duration_ms == 3200

    def test_add_entry_default_duration(self, changelog_writer):
        changelog_writer.add_entry(
            tool_name="check_logs",
            tool_input={},
            result="OK",
            success=True,
        )
        assert changelog_writer.entries[0].duration_ms == 0


class TestChangelogPersistence:
    """Tests fuer JSON-Serialisierung mit neuen Feldern"""

    def test_save_and_load_with_new_fields(self, changelog_writer, tmp_path):
        changelog_writer.add_entry(
            tool_name="cleanup_disk",
            tool_input={"action": "cleanup"},
            result="OK",
            success=True,
            duration_ms=1500,
            snapshot_before="vor Cleanup",
            snapshot_after="nach Cleanup",
        )

        # JSON lesen und pruefen
        with open(changelog_writer.log_path, "r") as f:
            data = json.load(f)

        entry_data = data["entries"][0]
        assert entry_data["duration_ms"] == 1500
        assert entry_data["snapshot_before"] == "vor Cleanup"
        assert entry_data["snapshot_after"] == "nach Cleanup"

    def test_load_backward_compatible(self, tmp_path):
        """Alte Changelog-Dateien ohne neue Felder laden"""
        with patch("ce365.storage.changelog.get_settings") as mock_settings:
            settings = MagicMock()
            settings.changelogs_dir = tmp_path / "changelogs"
            mock_settings.return_value = settings

            # Alte Datei simulieren (ohne duration_ms etc.)
            changelogs_dir = tmp_path / "changelogs"
            changelogs_dir.mkdir(parents=True)
            old_data = {
                "session_id": "old-session",
                "created_at": "2026-01-01T00:00:00",
                "entries": [
                    {
                        "timestamp": "2026-01-01T00:01:00",
                        "tool_name": "old_tool",
                        "tool_input": {},
                        "result": "OK",
                        "success": True,
                    }
                ],
            }
            with open(changelogs_dir / "old-session.json", "w") as f:
                json.dump(old_data, f)

            loaded = ChangelogWriter.load("old-session")
            assert len(loaded.entries) == 1
            assert loaded.entries[0].duration_ms == 0
            assert loaded.entries[0].snapshot_before == ""
            assert loaded.entries[0].snapshot_after == ""


class TestGetSummary:
    """Tests fuer get_summary mit Duration"""

    def test_summary_includes_duration(self, changelog_writer):
        changelog_writer.add_entry(
            tool_name="cleanup_disk",
            tool_input={},
            result="OK",
            success=True,
            duration_ms=3200,
        )
        summary = changelog_writer.get_summary()
        assert "3.2s" in summary
        assert "Dauer:" in summary

    def test_summary_includes_snapshots(self, changelog_writer):
        changelog_writer.add_entry(
            tool_name="cleanup_disk",
            tool_input={},
            result="OK",
            success=True,
            snapshot_before="Disk 97%",
            snapshot_after="Disk 72%",
        )
        summary = changelog_writer.get_summary()
        assert "Vorher: Disk 97%" in summary
        assert "Nachher: Disk 72%" in summary

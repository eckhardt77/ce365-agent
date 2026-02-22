"""
Tests für ExecutionLock (GO REPAIR Parsing)

Testet das Parsing von GO REPAIR Befehlen und Schritt-Validierung.
"""

import pytest
from ce365.workflow.lock import ExecutionLock, _ALL_STEPS


class TestIsGoCommand:
    """Tests für is_go_command()"""

    def test_valid_go_command(self):
        assert ExecutionLock.is_go_command("GO REPAIR: 1,2,3") is True

    def test_case_insensitive(self):
        assert ExecutionLock.is_go_command("go repair: 1") is True
        assert ExecutionLock.is_go_command("Go Repair: 1,2") is True

    def test_extra_whitespace(self):
        assert ExecutionLock.is_go_command("  GO REPAIR: 1  ") is True
        assert ExecutionLock.is_go_command("GO  REPAIR:  1") is True

    def test_go_without_steps(self):
        """GO REPAIR ohne Schrittangabe = alle freigeben"""
        assert ExecutionLock.is_go_command("GO REPAIR") is True
        assert ExecutionLock.is_go_command("go repair") is True

    def test_go_with_text(self):
        """GO REPAIR mit Text statt Zahlen"""
        assert ExecutionLock.is_go_command("GO REPAIR: Desktop-Organisieren (Plan A)") is True
        assert ExecutionLock.is_go_command("GO REPAIR: Plan A") is True

    def test_invalid_commands(self):
        assert ExecutionLock.is_go_command("REPAIR: 1") is False
        assert ExecutionLock.is_go_command("Hello World") is False
        assert ExecutionLock.is_go_command("") is False


class TestParseGoCommand:
    """Tests für parse_go_command() — gibt (steps, freitext) Tuple zurück"""

    def test_single_step(self):
        steps, freitext = ExecutionLock.parse_go_command("GO REPAIR: 1")
        assert steps == [1]
        assert freitext == ""

    def test_multiple_steps(self):
        steps, freitext = ExecutionLock.parse_go_command("GO REPAIR: 1,2,3")
        assert steps == [1, 2, 3]
        assert freitext == ""

    def test_range(self):
        steps, freitext = ExecutionLock.parse_go_command("GO REPAIR: 1-3")
        assert steps == [1, 2, 3]
        assert freitext == ""

    def test_mixed_format(self):
        steps, freitext = ExecutionLock.parse_go_command("GO REPAIR: 1,3-5,7")
        assert steps == [1, 3, 4, 5, 7]
        assert freitext == ""

    def test_case_insensitive(self):
        steps, freitext = ExecutionLock.parse_go_command("go repair: 1,2")
        assert steps == [1, 2]
        assert freitext == ""

    def test_whitespace_handling(self):
        steps, freitext = ExecutionLock.parse_go_command("GO  REPAIR:  1, 2, 3")
        assert steps == [1, 2, 3]
        assert freitext == ""

    def test_sorted_output(self):
        steps, freitext = ExecutionLock.parse_go_command("GO REPAIR: 3,1,2")
        assert steps == [1, 2, 3]
        assert freitext == ""

    def test_deduplicated_output(self):
        steps, freitext = ExecutionLock.parse_go_command("GO REPAIR: 1,1,2,2")
        assert steps == [1, 2]
        assert freitext == ""

    def test_range_with_duplicates(self):
        steps, freitext = ExecutionLock.parse_go_command("GO REPAIR: 1-3,2,3")
        assert steps == [1, 2, 3]
        assert freitext == ""

    def test_go_repair_without_steps(self):
        """GO REPAIR ohne Schritte = alle freigeben, kein Freitext"""
        steps, freitext = ExecutionLock.parse_go_command("GO REPAIR")
        assert steps == _ALL_STEPS
        assert freitext == ""

    def test_go_repair_with_freitext(self):
        """GO REPAIR mit Freitext = alle Schritte + Freitext weiterleiten"""
        steps, freitext = ExecutionLock.parse_go_command("GO REPAIR: disable Login Items [Notion, Steam]")
        assert steps == _ALL_STEPS
        assert freitext == "disable Login Items [Notion, Steam]"

    def test_go_repair_freitext_plan(self):
        """GO REPAIR mit natuerlichsprachlicher Anweisung"""
        steps, freitext = ExecutionLock.parse_go_command("GO REPAIR: Desktop-Organisieren (Plan A)")
        assert steps == _ALL_STEPS
        assert freitext == "Desktop-Organisieren (Plan A)"

    def test_go_repair_freitext_plan_a(self):
        """GO REPAIR: Plan A = Freitext"""
        steps, freitext = ExecutionLock.parse_go_command("GO REPAIR: Plan A")
        assert steps == _ALL_STEPS
        assert freitext == "Plan A"

    def test_go_repair_freitext_long(self):
        """GO REPAIR: beliebiger Text = Freitext weiterleiten"""
        steps, freitext = ExecutionLock.parse_go_command("GO REPAIR: Ordner anlegen und Dateien verschieben")
        assert steps == _ALL_STEPS
        assert freitext == "Ordner anlegen und Dateien verschieben"

    def test_invalid_format_returns_none(self):
        assert ExecutionLock.parse_go_command("REPAIR: 1") is None
        assert ExecutionLock.parse_go_command("Hello") is None
        assert ExecutionLock.parse_go_command("") is None

    def test_large_step_numbers(self):
        steps, freitext = ExecutionLock.parse_go_command("GO REPAIR: 10,20,30")
        assert steps == [10, 20, 30]
        assert freitext == ""


class TestFormatSteps:
    """Tests für format_steps()"""

    def test_format_single(self):
        assert ExecutionLock.format_steps([1]) == "1"

    def test_format_multiple(self):
        assert ExecutionLock.format_steps([1, 2, 3]) == "1, 2, 3"

    def test_format_empty(self):
        assert ExecutionLock.format_steps([]) == ""

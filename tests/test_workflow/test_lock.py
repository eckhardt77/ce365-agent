"""
Tests für ExecutionLock (GO REPAIR Parsing)

Testet das Parsing von GO REPAIR Befehlen und Schritt-Validierung.
"""

import pytest
from techcare.workflow.lock import ExecutionLock


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

    def test_invalid_commands(self):
        assert ExecutionLock.is_go_command("REPAIR: 1") is False
        assert ExecutionLock.is_go_command("GO: 1") is False
        assert ExecutionLock.is_go_command("Hello World") is False
        assert ExecutionLock.is_go_command("") is False


class TestParseGoCommand:
    """Tests für parse_go_command()"""

    def test_single_step(self):
        result = ExecutionLock.parse_go_command("GO REPAIR: 1")
        assert result == [1]

    def test_multiple_steps(self):
        result = ExecutionLock.parse_go_command("GO REPAIR: 1,2,3")
        assert result == [1, 2, 3]

    def test_range(self):
        result = ExecutionLock.parse_go_command("GO REPAIR: 1-3")
        assert result == [1, 2, 3]

    def test_mixed_format(self):
        result = ExecutionLock.parse_go_command("GO REPAIR: 1,3-5,7")
        assert result == [1, 3, 4, 5, 7]

    def test_case_insensitive(self):
        result = ExecutionLock.parse_go_command("go repair: 1,2")
        assert result == [1, 2]

    def test_whitespace_handling(self):
        result = ExecutionLock.parse_go_command("GO  REPAIR:  1, 2, 3")
        assert result == [1, 2, 3]

    def test_sorted_output(self):
        result = ExecutionLock.parse_go_command("GO REPAIR: 3,1,2")
        assert result == [1, 2, 3]

    def test_deduplicated_output(self):
        result = ExecutionLock.parse_go_command("GO REPAIR: 1,1,2,2")
        assert result == [1, 2]

    def test_range_with_duplicates(self):
        result = ExecutionLock.parse_go_command("GO REPAIR: 1-3,2,3")
        assert result == [1, 2, 3]

    def test_invalid_format_returns_none(self):
        assert ExecutionLock.parse_go_command("REPAIR: 1") is None
        assert ExecutionLock.parse_go_command("Hello") is None
        assert ExecutionLock.parse_go_command("") is None

    def test_invalid_steps_returns_none(self):
        assert ExecutionLock.parse_go_command("GO REPAIR: abc") is None
        assert ExecutionLock.parse_go_command("GO REPAIR: 1,abc") is None

    def test_invalid_range_returns_none(self):
        # Reversed range (start > end)
        assert ExecutionLock.parse_go_command("GO REPAIR: 3-1") is None

    def test_large_step_numbers(self):
        result = ExecutionLock.parse_go_command("GO REPAIR: 10,20,30")
        assert result == [10, 20, 30]


class TestFormatSteps:
    """Tests für format_steps()"""

    def test_format_single(self):
        assert ExecutionLock.format_steps([1]) == "1"

    def test_format_multiple(self):
        assert ExecutionLock.format_steps([1, 2, 3]) == "1, 2, 3"

    def test_format_empty(self):
        assert ExecutionLock.format_steps([]) == ""

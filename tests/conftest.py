"""
CE365 Agent - Shared Test Fixtures
"""

import os
import pytest
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

# Setze Test-Environment BEVOR Settings geladen werden
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-not-real")
os.environ.setdefault("EDITION", "community")
os.environ.setdefault("LICENSE_KEY", "")


@pytest.fixture
def state_machine():
    """Frische WorkflowStateMachine Instanz"""
    from ce365.workflow.state_machine import WorkflowStateMachine
    return WorkflowStateMachine()


@pytest.fixture
def tool_registry():
    """Leere ToolRegistry Instanz"""
    from ce365.tools.registry import ToolRegistry
    return ToolRegistry()


@pytest.fixture
def mock_audit_tool():
    """Mock AuditTool"""
    from ce365.tools.base import AuditTool

    class MockAuditTool(AuditTool):
        @property
        def name(self) -> str:
            return "mock_audit"

        @property
        def description(self) -> str:
            return "Mock audit tool for testing"

        @property
        def input_schema(self) -> dict:
            return {
                "type": "object",
                "properties": {},
                "required": [],
            }

        async def execute(self, **kwargs) -> str:
            return "audit result"

    return MockAuditTool()


@pytest.fixture
def mock_repair_tool():
    """Mock RepairTool"""
    from ce365.tools.base import RepairTool

    class MockRepairTool(RepairTool):
        @property
        def name(self) -> str:
            return "mock_repair"

        @property
        def description(self) -> str:
            return "Mock repair tool for testing"

        @property
        def input_schema(self) -> dict:
            return {
                "type": "object",
                "properties": {},
                "required": [],
            }

        async def execute(self, **kwargs) -> str:
            return "repair result"

    return MockRepairTool()


@pytest.fixture
def mock_changelog_writer():
    """Mock ChangelogWriter (ohne Filesystem-Zugriff)"""
    writer = MagicMock()
    writer.add_entry = MagicMock()
    writer.get_entries = MagicMock(return_value=[])
    writer.get_summary = MagicMock(return_value="Keine Änderungen.")
    return writer


@pytest.fixture
def tmp_ce365_dir(tmp_path):
    """Temporäres .ce365 Verzeichnis"""
    ce365_dir = tmp_path / ".ce365"
    ce365_dir.mkdir()
    (ce365_dir / "cache").mkdir()
    return ce365_dir


@pytest.fixture
def session():
    """Frische Session Instanz"""
    from ce365.core.session import Session
    return Session()

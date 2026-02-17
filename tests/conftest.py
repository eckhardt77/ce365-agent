"""
TechCare Bot - Shared Test Fixtures
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
    from techcare.workflow.state_machine import WorkflowStateMachine
    return WorkflowStateMachine()


@pytest.fixture
def tool_registry():
    """Leere ToolRegistry Instanz"""
    from techcare.tools.registry import ToolRegistry
    return ToolRegistry()


@pytest.fixture
def mock_audit_tool():
    """Mock AuditTool"""
    from techcare.tools.base import AuditTool

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
    from techcare.tools.base import RepairTool

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
def tmp_techcare_dir(tmp_path):
    """Temporäres .techcare Verzeichnis"""
    techcare_dir = tmp_path / ".techcare"
    techcare_dir.mkdir()
    (techcare_dir / "cache").mkdir()
    return techcare_dir


@pytest.fixture
def session():
    """Frische Session Instanz"""
    from techcare.core.session import Session
    return Session()

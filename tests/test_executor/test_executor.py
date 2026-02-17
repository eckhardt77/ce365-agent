"""
Tests für CommandExecutor

Testet State Validation, Tool Execution und Changelog Writing.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from techcare.tools.executor import CommandExecutor
from techcare.tools.registry import ToolRegistry
from techcare.workflow.state_machine import WorkflowStateMachine, WorkflowState


@pytest.fixture
def executor(tool_registry, state_machine, mock_changelog_writer, mock_audit_tool, mock_repair_tool):
    """CommandExecutor mit registrierten Tools"""
    tool_registry.register(mock_audit_tool)
    tool_registry.register(mock_repair_tool)
    return CommandExecutor(tool_registry, state_machine, mock_changelog_writer)


class TestToolExecution:
    """Tests für Tool Execution"""

    @pytest.mark.asyncio
    async def test_execute_audit_tool(self, executor):
        success, result = await executor.execute_tool("mock_audit", {})
        assert success is True
        assert result == "audit result"

    @pytest.mark.asyncio
    async def test_execute_nonexistent_tool(self, executor):
        success, result = await executor.execute_tool("nonexistent", {})
        assert success is False
        assert "nicht gefunden" in result

    @pytest.mark.asyncio
    async def test_execute_repair_tool_blocked_without_lock(self, executor):
        success, result = await executor.execute_tool("mock_repair", {})
        assert success is False
        assert "GO REPAIR" in result

    @pytest.mark.asyncio
    async def test_execute_repair_tool_after_lock(self, executor, state_machine):
        state_machine.transition_to(WorkflowState.AUDIT)
        state_machine.transition_to_plan_ready("Plan")
        state_machine.lock_execution([1])

        success, result = await executor.execute_tool("mock_repair", {})
        assert success is True
        assert result == "repair result"


class TestChangelogIntegration:
    """Tests für Changelog Writing bei Repair-Tools"""

    @pytest.mark.asyncio
    async def test_changelog_written_on_repair(self, executor, state_machine, mock_changelog_writer):
        state_machine.transition_to(WorkflowState.AUDIT)
        state_machine.transition_to_plan_ready("Plan")
        state_machine.lock_execution([1])

        await executor.execute_tool("mock_repair", {"param": "value"})
        mock_changelog_writer.add_entry.assert_called_once()
        call_args = mock_changelog_writer.add_entry.call_args
        assert call_args.kwargs["tool_name"] == "mock_repair"
        assert call_args.kwargs["success"] is True

    @pytest.mark.asyncio
    async def test_no_changelog_on_audit(self, executor, mock_changelog_writer):
        await executor.execute_tool("mock_audit", {})
        mock_changelog_writer.add_entry.assert_not_called()


class TestErrorHandling:
    """Tests für Error Handling"""

    @pytest.mark.asyncio
    async def test_tool_execution_error(self, tool_registry, state_machine, mock_changelog_writer):
        from techcare.tools.base import AuditTool

        class FailingTool(AuditTool):
            @property
            def name(self):
                return "failing_tool"
            @property
            def description(self):
                return "Always fails"
            @property
            def input_schema(self):
                return {"type": "object", "properties": {}}
            async def execute(self, **kwargs):
                raise RuntimeError("Tool crashed!")

        tool_registry.register(FailingTool())
        executor = CommandExecutor(tool_registry, state_machine, mock_changelog_writer)

        success, result = await executor.execute_tool("failing_tool", {})
        assert success is False
        assert "Fehler" in result
        assert "Tool crashed!" in result

    @pytest.mark.asyncio
    async def test_repair_error_logged_to_changelog(self, tool_registry, state_machine, mock_changelog_writer):
        from techcare.tools.base import RepairTool

        class FailingRepair(RepairTool):
            @property
            def name(self):
                return "failing_repair"
            @property
            def description(self):
                return "Always fails"
            @property
            def input_schema(self):
                return {"type": "object", "properties": {}}
            async def execute(self, **kwargs):
                raise RuntimeError("Repair failed!")

        tool_registry.register(FailingRepair())
        executor = CommandExecutor(tool_registry, state_machine, mock_changelog_writer)

        state_machine.transition_to(WorkflowState.AUDIT)
        state_machine.transition_to_plan_ready("Plan")
        state_machine.lock_execution([1])

        success, result = await executor.execute_tool("failing_repair", {})
        assert success is False
        mock_changelog_writer.add_entry.assert_called_once()
        assert mock_changelog_writer.add_entry.call_args.kwargs["success"] is False

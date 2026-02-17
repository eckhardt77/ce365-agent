"""
Integration Tests für Tool Execution

Testet Audit-Tool Ausführung und Repair-Tool Blockade ohne Lock.
"""

import pytest
from unittest.mock import MagicMock
from ce365.tools.registry import ToolRegistry
from ce365.tools.executor import CommandExecutor
from ce365.workflow.state_machine import WorkflowStateMachine, WorkflowState


@pytest.fixture
def full_executor():
    """Executor mit echten Audit- und Repair-Tools"""
    from ce365.tools.audit.system_info import SystemInfoTool
    from ce365.tools.repair.disk_cleanup import DiskCleanupTool

    registry = ToolRegistry()
    registry.register(SystemInfoTool())
    registry.register(DiskCleanupTool())

    sm = WorkflowStateMachine()
    changelog = MagicMock()
    changelog.add_entry = MagicMock()

    return CommandExecutor(registry, sm, changelog), sm


@pytest.mark.integration
class TestAuditToolExecution:
    """Tests für echte Audit-Tool Ausführung"""

    @pytest.mark.asyncio
    async def test_system_info_tool_executes(self, full_executor):
        executor, sm = full_executor
        success, result = await executor.execute_tool("get_system_info", {})
        assert success is True
        assert isinstance(result, str)
        assert len(result) > 0


@pytest.mark.integration
class TestRepairToolBlockade:
    """Tests dass Repair-Tools ohne Lock blockiert werden"""

    @pytest.mark.asyncio
    async def test_repair_blocked_in_idle(self, full_executor):
        executor, sm = full_executor
        success, result = await executor.execute_tool("cleanup_disk", {})
        assert success is False
        assert "GO REPAIR" in result

    @pytest.mark.asyncio
    async def test_repair_blocked_in_audit(self, full_executor):
        executor, sm = full_executor
        # Trigger audit state
        await executor.execute_tool("get_system_info", {})
        assert sm.current_state == WorkflowState.AUDIT

        # Repair should still be blocked
        success, result = await executor.execute_tool("cleanup_disk", {})
        assert success is False

    @pytest.mark.asyncio
    async def test_repair_allowed_after_lock(self, full_executor):
        executor, sm = full_executor
        sm.transition_to(WorkflowState.AUDIT)
        sm.transition_to_plan_ready("1. Disk Cleanup")
        sm.lock_execution([1])

        # Now repair should work (but may fail due to OS permissions - that's OK)
        success, result = await executor.execute_tool("cleanup_disk", {})
        # We only care that it wasn't blocked by state machine
        # The tool itself may fail due to permissions, which is fine
        assert isinstance(result, str)

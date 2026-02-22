"""
Integration Tests für Bot Startup

Testet ob der Bot korrekt initialisiert wird: Tools registriert, State Machine bereit.
"""

import pytest
from unittest.mock import patch, MagicMock
from ce365.tools.registry import ToolRegistry
from ce365.tools.base import AuditTool, RepairTool
from ce365.workflow.state_machine import WorkflowStateMachine, WorkflowState
from ce365.workflow.lock import ExecutionLock
from ce365.core.session import Session


@pytest.mark.integration
class TestToolRegistration:
    """Tests dass alle erwarteten Tools registriert werden können"""

    def test_all_audit_tools_importable(self):
        """Prüft ob alle Audit-Tools importiert werden können"""
        from ce365.tools.audit.system_info import SystemInfoTool
        from ce365.tools.audit.logs import CheckSystemLogsTool
        from ce365.tools.audit.processes import CheckRunningProcessesTool
        from ce365.tools.audit.updates import CheckSystemUpdatesTool
        from ce365.tools.audit.backup import CheckBackupStatusTool
        from ce365.tools.audit.security import CheckSecurityStatusTool
        from ce365.tools.audit.startup import CheckStartupProgramsTool

        tools = [
            SystemInfoTool(),
            CheckSystemLogsTool(),
            CheckRunningProcessesTool(),
            CheckSystemUpdatesTool(),
            CheckBackupStatusTool(),
            CheckSecurityStatusTool(),
            CheckStartupProgramsTool(),
        ]

        for tool in tools:
            assert isinstance(tool, AuditTool)
            assert tool.name
            assert tool.description
            assert tool.input_schema

    def test_all_repair_tools_importable(self):
        """Prüft ob alle Repair-Tools importiert werden können"""
        from ce365.tools.repair.service_manager import ServiceManagerTool
        from ce365.tools.repair.disk_cleanup import DiskCleanupTool
        from ce365.tools.repair.network_tools import FlushDNSCacheTool, ResetNetworkStackTool

        tools = [
            ServiceManagerTool(),
            DiskCleanupTool(),
            FlushDNSCacheTool(),
            ResetNetworkStackTool(),
        ]

        for tool in tools:
            assert isinstance(tool, RepairTool)
            assert tool.name
            assert tool.description
            assert tool.requires_approval is True

    def test_registry_accepts_all_tools(self):
        """Prüft ob alle Tools ohne Konflikte registriert werden können"""
        from ce365.tools.audit.system_info import SystemInfoTool
        from ce365.tools.audit.logs import CheckSystemLogsTool
        from ce365.tools.repair.disk_cleanup import DiskCleanupTool
        from ce365.tools.repair.network_tools import FlushDNSCacheTool

        registry = ToolRegistry()
        tools = [
            SystemInfoTool(),
            CheckSystemLogsTool(),
            DiskCleanupTool(),
            FlushDNSCacheTool(),
        ]

        for tool in tools:
            registry.register(tool)

        assert len(registry) == 4
        assert len(registry.get_audit_tools()) == 2
        assert len(registry.get_repair_tools()) == 2

    def test_tool_definitions_valid_for_anthropic(self):
        """Prüft ob Tool-Definitionen das Anthropic-Format haben"""
        from ce365.tools.audit.system_info import SystemInfoTool

        registry = ToolRegistry()
        registry.register(SystemInfoTool())

        definitions = registry.get_tool_definitions()
        assert len(definitions) == 1

        defn = definitions[0]
        assert "name" in defn
        assert "description" in defn
        assert "input_schema" in defn
        assert isinstance(defn["input_schema"], dict)


@pytest.mark.integration
class TestWorkflowIntegration:
    """Tests für Workflow-Komponenten zusammen"""

    def test_full_go_repair_flow(self):
        """Kompletter Flow: Audit → Plan → GO REPAIR → Execute"""
        sm = WorkflowStateMachine()
        registry = ToolRegistry()

        from ce365.tools.audit.system_info import SystemInfoTool
        from ce365.tools.repair.disk_cleanup import DiskCleanupTool

        registry.register(SystemInfoTool())
        registry.register(DiskCleanupTool())

        # 1. Audit phase
        audit_tool = registry.get_tool("get_system_info")
        can, _ = sm.can_execute_tool(audit_tool.name, registry.is_repair_tool(audit_tool.name))
        assert can is True

        # 2. Plan ready
        sm.transition_to_plan_ready("1. Disk Cleanup\n2. Restart")

        # 3. Repair blocked before GO REPAIR
        can, msg = sm.can_execute_tool("cleanup_disk", True)
        assert can is False

        # 4. Parse GO REPAIR
        command = "GO REPAIR: 1,2"
        assert ExecutionLock.is_go_command(command)
        steps, freitext = ExecutionLock.parse_go_command(command)
        assert steps == [1, 2]
        assert freitext == ""

        # 5. Lock execution
        sm.lock_execution(steps, freitext)

        # 6. Repair now allowed
        can, _ = sm.can_execute_tool("cleanup_disk", True)
        assert can is True

    def test_session_with_workflow(self):
        """Session verfolgt Messages während Workflow"""
        session = Session()
        sm = WorkflowStateMachine()

        session.add_message("user", "Mein PC ist langsam")
        sm.can_execute_tool("get_system_info", False)
        session.add_message("assistant", "Ich analysiere Ihr System...")

        assert len(session.messages) == 2
        assert sm.current_state == WorkflowState.AUDIT

from typing import Dict, Any, Optional
from techcare.tools.registry import ToolRegistry
from techcare.workflow.state_machine import WorkflowStateMachine
from techcare.storage.changelog import ChangelogWriter


class CommandExecutor:
    """
    Safe Command Executor mit State Validation

    Responsibilities:
    - Tool Execution mit State Machine Validation
    - Changelog Writing für Repair-Tools
    - Error Handling
    """

    def __init__(
        self,
        tool_registry: ToolRegistry,
        state_machine: WorkflowStateMachine,
        changelog_writer: ChangelogWriter,
    ):
        self.tool_registry = tool_registry
        self.state_machine = state_machine
        self.changelog_writer = changelog_writer

    async def execute_tool(
        self, tool_name: str, tool_input: Dict[str, Any]
    ) -> tuple[bool, str]:
        """
        Tool ausführen mit State Validation

        Args:
            tool_name: Name des Tools
            tool_input: Tool Parameter

        Returns:
            (success: bool, result: str)
        """
        # Tool aus Registry holen
        tool = self.tool_registry.get_tool(tool_name)
        if not tool:
            return False, f"❌ Tool '{tool_name}' nicht gefunden"

        # State Validation
        is_repair_tool = self.tool_registry.is_repair_tool(tool_name)
        can_execute, error_msg = self.state_machine.can_execute_tool(
            tool_name, is_repair_tool
        )

        if not can_execute:
            return False, error_msg

        # Tool ausführen
        try:
            result = await tool.execute(**tool_input)
            success = True

            # Changelog schreiben (nur für Repair-Tools)
            if is_repair_tool:
                self.changelog_writer.add_entry(
                    tool_name=tool_name,
                    tool_input=tool_input,
                    result=result,
                    success=True,
                )

            return success, result

        except Exception as e:
            error_result = f"❌ Fehler bei Ausführung von '{tool_name}': {str(e)}"

            # Fehler auch loggen (für Repair-Tools)
            if is_repair_tool:
                self.changelog_writer.add_entry(
                    tool_name=tool_name,
                    tool_input=tool_input,
                    result=str(e),
                    success=False,
                )

            return False, error_result

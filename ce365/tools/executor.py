from typing import Dict, Any, Optional
from ce365.tools.registry import ToolRegistry
from ce365.workflow.state_machine import WorkflowStateMachine
from ce365.workflow.hooks import HookManager, HookEvent, HookContext
from ce365.storage.changelog import ChangelogWriter
from ce365.core.usage_tracker import UsageTracker


class CommandExecutor:
    """
    Safe Command Executor mit State Validation + Hook-System

    Responsibilities:
    - Tool Execution mit State Machine Validation
    - PRE/POST Hooks fuer Workflow-Automatisierung
    - Changelog Writing fuer Repair-Tools
    - Usage Tracking (Community: 5 Repair Runs/Monat)
    - Error Handling
    """

    def __init__(
        self,
        tool_registry: ToolRegistry,
        state_machine: WorkflowStateMachine,
        changelog_writer: ChangelogWriter,
        usage_tracker: UsageTracker = None,
        hook_manager: HookManager = None,
    ):
        self.tool_registry = tool_registry
        self.state_machine = state_machine
        self.changelog_writer = changelog_writer
        self.usage_tracker = usage_tracker
        self.hook_manager = hook_manager

    async def execute_tool(
        self, tool_name: str, tool_input: Dict[str, Any]
    ) -> tuple[bool, str]:
        """
        Tool ausfuehren mit State Validation und Hooks

        Args:
            tool_name: Name des Tools
            tool_input: Tool Parameter

        Returns:
            (success: bool, result: str)
        """
        # Tool aus Registry holen
        tool = self.tool_registry.get_tool(tool_name)
        if not tool:
            return False, f"Tool '{tool_name}' nicht gefunden"

        # State Validation
        is_repair_tool = self.tool_registry.is_repair_tool(tool_name)
        can_execute, error_msg = self.state_machine.can_execute_tool(
            tool_name, is_repair_tool
        )

        if not can_execute:
            return False, error_msg

        # Usage Limit pruefen (Community: 5 Repair Runs/Monat)
        if is_repair_tool and self.usage_tracker and not self.usage_tracker.can_run_repair():
            return False, self.usage_tracker.get_limit_message()

        # === PRE-Hooks ===
        hook_messages = []
        if self.hook_manager:
            pre_event = HookEvent.PRE_REPAIR if is_repair_tool else HookEvent.PRE_TOOL
            pre_context = HookContext(
                event=pre_event,
                tool_name=tool_name,
                tool_input=tool_input,
            )
            pre_result = await self.hook_manager.run_hooks(pre_event, pre_context)

            if pre_result.message:
                hook_messages.append(pre_result.message)

            if not pre_result.proceed:
                blocked_msg = pre_result.message or f"Hook hat Ausfuehrung von '{tool_name}' blockiert"
                return False, blocked_msg

            # Modifizierte Inputs uebernehmen
            if pre_result.modified_input is not None:
                tool_input = pre_result.modified_input

        # === Tool ausfuehren ===
        try:
            result = await tool.execute(**tool_input)
            success = True

            # Changelog schreiben + Usage tracking (nur fuer Repair-Tools)
            if is_repair_tool:
                # Remote-Prefix im Changelog
                from ce365.core.command_runner import get_command_runner
                runner = get_command_runner()
                log_tool_name = tool_name
                if runner.is_remote:
                    log_tool_name = f"[REMOTE:{runner.remote_host}] {tool_name}"

                self.changelog_writer.add_entry(
                    tool_name=log_tool_name,
                    tool_input=tool_input,
                    result=result,
                    success=True,
                )
                if self.usage_tracker:
                    self.usage_tracker.increment_repair()

            # === POST-Hooks ===
            if self.hook_manager:
                post_event = HookEvent.POST_REPAIR if is_repair_tool else HookEvent.POST_TOOL
                post_context = HookContext(
                    event=post_event,
                    tool_name=tool_name,
                    tool_input=tool_input,
                    tool_result=result,
                    tool_success=True,
                )
                post_result = await self.hook_manager.run_hooks(post_event, post_context)
                if post_result.message:
                    hook_messages.append(post_result.message)

            # Hook-Nachrichten an Ergebnis anhaengen
            if hook_messages:
                result = result + "\n\n---\n" + "\n".join(hook_messages)

            return success, result

        except Exception as e:
            error_result = f"Fehler bei Ausfuehrung von '{tool_name}': {str(e)}"

            # Fehler auch loggen (fuer Repair-Tools)
            if is_repair_tool:
                self.changelog_writer.add_entry(
                    tool_name=tool_name,
                    tool_input=tool_input,
                    result=str(e),
                    success=False,
                )

            # POST-Hooks auch bei Fehler ausfuehren
            if self.hook_manager:
                post_event = HookEvent.POST_REPAIR if is_repair_tool else HookEvent.POST_TOOL
                post_context = HookContext(
                    event=post_event,
                    tool_name=tool_name,
                    tool_input=tool_input,
                    tool_result=str(e),
                    tool_success=False,
                )
                await self.hook_manager.run_hooks(post_event, post_context)

            return False, error_result

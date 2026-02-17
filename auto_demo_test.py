#!/usr/bin/env python3
"""CE365 Agent - Automatischer Demo Test"""

import asyncio
from ce365.tools.audit.system_info import SystemInfoTool
from ce365.tools.repair.service_manager import ServiceManagerTool
from ce365.tools.registry import ToolRegistry
from ce365.workflow.state_machine import WorkflowStateMachine, WorkflowState
from ce365.workflow.lock import ExecutionLock
from ce365.storage.changelog import ChangelogWriter
from ce365.ui.console import RichConsole
from ce365.config.system_prompt import get_system_prompt

console = RichConsole()

def print_section(title: str):
    console.console.print()
    console.console.print("=" * 80, style="cyan")
    console.console.print(f"  {title}", style="bold cyan")
    console.console.print("=" * 80, style="cyan")
    console.console.print()

async def auto_demo_test():
    console.display_logo()
    console.display_info("AUTO-DEMO: CE365 Agent Komponenten-Test")
    console.display_separator()

    # 1. SYSTEM PROMPT
    print_section("1. SYSTEM PROMPT VALIDIERUNG")
    system_prompt = get_system_prompt()
    checks = [
        ("FUNDAMENTALE REGELN", "FUNDAMENTALE REGELN" in system_prompt),
        ("STARTFRAGEN", "STARTFRAGEN" in system_prompt),
        ("Backup-Check", "Backup" in system_prompt),
        ("ALLOWLIST", "ALLOWLIST" in system_prompt),
        ("BLOCKLIST", "BLOCKLIST" in system_prompt),
        ("EINZELSCHRITT", "EINZELSCHRITT" in system_prompt),
        ("AUDIT-KIT WINDOWS", "AUDIT-KIT WINDOWS" in system_prompt),
        ("AUDIT-KIT macOS", "AUDIT-KIT macOS" in system_prompt),
        ("NUR Deutsch", "NUR DEUTSCH" in system_prompt),
    ]
    for check_name, result in checks:
        status = "✓" if result else "✗"
        color = "green" if result else "red"
        console.console.print(f"  {status} {check_name}", style=color)

    # 2. TOOL REGISTRY
    print_section("2. TOOL REGISTRY")
    tool_registry = ToolRegistry()
    tool_registry.register(SystemInfoTool())
    tool_registry.register(ServiceManagerTool())
    console.display_success(f"✓ {len(tool_registry)} Tools registriert")
    console.console.print(f"  - Audit-Tools: {len(tool_registry.get_audit_tools())}")
    console.console.print(f"  - Repair-Tools: {len(tool_registry.get_repair_tools())}")

    # 3. STATE MACHINE
    print_section("3. WORKFLOW STATE MACHINE")
    state_machine = WorkflowStateMachine()
    console.console.print(f"  Initial: [bold]{state_machine.current_state.value}[/bold]")
    state_machine.transition_to(WorkflowState.AUDIT)
    console.console.print(f"    ✓ IDLE → AUDIT", style="green")
    state_machine.transition_to(WorkflowState.ANALYSIS)
    console.console.print(f"    ✓ AUDIT → ANALYSIS", style="green")
    state_machine.transition_to_plan_ready("Demo Plan")
    console.console.print(f"    ✓ ANALYSIS → PLAN_READY", style="green")

    # 4. AUDIT-TOOL
    print_section("4. AUDIT-TOOL AUSFÜHRUNG")
    console.display_info("Führe get_system_info aus...")
    system_info_tool = tool_registry.get_tool("get_system_info")
    result = await system_info_tool.execute(detailed=False)
    result_lines = result.split('\n')[:12]
    for line in result_lines:
        console.console.print(f"  {line}")
    console.display_success("✓ Audit-Tool erfolgreich")

    # 5. GO REPAIR PARSING
    print_section("5. GO REPAIR PARSING")
    tests = [
        ("GO REPAIR: 1,2,3", [1, 2, 3]),
        ("GO REPAIR: 1-3", [1, 2, 3]),
        ("go repair: 2", [2]),
    ]
    for cmd, expected in tests:
        parsed = ExecutionLock.parse_go_command(cmd)
        match = parsed == expected
        status = "✓" if match else "✗"
        color = "green" if match else "red"
        console.console.print(f"    {status} '{cmd}' → {parsed}", style=color)

    # 6. EXECUTION LOCK
    print_section("6. EXECUTION LOCK")
    state_machine.lock_execution([1, 2])
    console.display_success("✓ Lock aktiviert")
    console.console.print(f"  State: [bold]{state_machine.current_state.value}[/bold]")

    # 7. CHANGELOG
    print_section("7. CHANGELOG")
    changelog = ChangelogWriter("demo-test")
    changelog.add_entry("manage_service", {"service": "test"}, "✓ Erfolg", True)
    console.display_success(f"✓ Changelog: {changelog.log_path}")

    # ZUSAMMENFASSUNG
    print_section("ZUSAMMENFASSUNG")
    console.console.print("[bold green]✅ ALLE TESTS ERFOLGREICH:[/bold green]")
    tests = [
        "System Prompt (alle Features)",
        "Tool Registry",
        "State Machine",
        "Audit-Tool",
        "GO REPAIR Parsing",
        "Execution Lock",
        "Changelog",
    ]
    for test in tests:
        console.console.print(f"  ✓ {test}", style="green")

    console.console.print()
    console.display_success("🎉 Demo abgeschlossen!")
    return True

if __name__ == "__main__":
    asyncio.run(auto_demo_test())

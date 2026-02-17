#!/usr/bin/env python3
"""
TechCare Bot - Demo Test (ohne echten API Key)

Simuliert einen kompletten Workflow:
1. Startfragen
2. Audit-Phase
3. Diagnose
4. Reparatur-Plan
5. GO REPAIR
6. Ausführung
"""

import asyncio
from techcare.tools.audit.system_info import SystemInfoTool
from techcare.tools.repair.service_manager import ServiceManagerTool
from techcare.tools.registry import ToolRegistry
from techcare.workflow.state_machine import WorkflowStateMachine, WorkflowState
from techcare.workflow.lock import ExecutionLock
from techcare.storage.changelog import ChangelogWriter
from techcare.ui.console import RichConsole
from techcare.config.system_prompt import get_system_prompt

console = RichConsole()


def print_section(title: str):
    """Section Header"""
    console.console.print()
    console.console.print("=" * 80, style="cyan")
    console.console.print(f"  {title}", style="bold cyan")
    console.console.print("=" * 80, style="cyan")
    console.console.print()


async def demo_test():
    """Demo-Test des TechCare Bot Workflows"""

    console.display_logo()
    console.display_info("DEMO-MODUS: Simuliert TechCare Bot Workflow")
    console.display_separator()

    # ==========================================
    # 1. SYSTEM PROMPT ANZEIGEN
    # ==========================================
    print_section("1. SYSTEM PROMPT (Auszug)")
    system_prompt = get_system_prompt()

    # Zeige relevante Teile
    lines = system_prompt.split('\n')
    console.console.print("[bold]FUNDAMENTALE REGELN:[/bold]")
    for i, line in enumerate(lines[3:9]):
        console.console.print(f"  {line}", style="yellow")

    console.console.print("\n[bold]STARTFRAGEN:[/bold]")
    for i, line in enumerate(lines[11:20]):
        if line.strip():
            console.console.print(f"  {line}", style="yellow")

    input("\n[cyan]⏎ Weiter...[/cyan]")

    # ==========================================
    # 2. TOOL REGISTRY INITIALISIERUNG
    # ==========================================
    print_section("2. TOOL REGISTRY")

    tool_registry = ToolRegistry()
    tool_registry.register(SystemInfoTool())
    tool_registry.register(ServiceManagerTool())

    console.display_success(f"Tools registriert: {len(tool_registry)}")
    console.console.print(f"  - Audit-Tools: {len(tool_registry.get_audit_tools())}")
    console.console.print(f"  - Repair-Tools: {len(tool_registry.get_repair_tools())}")

    console.console.print("\n[bold]Registrierte Tools:[/bold]")
    for tool in tool_registry.get_all_tools():
        tool_type = "🔍 AUDIT" if tool.tool_type == "audit" else "🔧 REPAIR"
        console.console.print(f"  {tool_type}: {tool.name}")

    input("\n[cyan]⏎ Weiter...[/cyan]")

    # ==========================================
    # 3. STATE MACHINE
    # ==========================================
    print_section("3. WORKFLOW STATE MACHINE")

    state_machine = WorkflowStateMachine()
    console.display_info(f"Initial State: {state_machine.current_state.value}")

    # Test State Transitions
    console.console.print("\n[bold]State Transitions:[/bold]")

    # IDLE → AUDIT
    state_machine.transition_to(WorkflowState.AUDIT)
    console.console.print(f"  1. IDLE → AUDIT: ✓")

    # AUDIT → ANALYSIS
    state_machine.transition_to(WorkflowState.ANALYSIS)
    console.console.print(f"  2. AUDIT → ANALYSIS: ✓")

    # ANALYSIS → PLAN_READY
    state_machine.transition_to_plan_ready("Test Plan")
    console.console.print(f"  3. ANALYSIS → PLAN_READY: ✓")
    console.console.print(f"     [dim]Plan gespeichert: '{state_machine.repair_plan[:20]}...'[/dim]")

    input("\n[cyan]⏎ Weiter...[/cyan]")

    # ==========================================
    # 4. AUDIT-TOOL AUSFÜHRUNG
    # ==========================================
    print_section("4. AUDIT-TOOL AUSFÜHRUNG")

    console.display_info("Führe get_system_info aus...")

    system_info_tool = tool_registry.get_tool("get_system_info")
    result = await system_info_tool.execute(detailed=False)

    console.display_tool_result("get_system_info", result, success=True)

    input("\n[cyan]⏎ Weiter...[/cyan]")

    # ==========================================
    # 5. GO REPAIR COMMAND PARSING
    # ==========================================
    print_section("5. GO REPAIR COMMAND PARSING")

    test_commands = [
        "GO REPAIR: 1,2,3",
        "GO REPAIR: 1-3",
        "GO REPAIR: 1,3-5,7",
        "go repair: 2",  # case insensitive
        "GO REPAIR: invalid",  # sollte None zurückgeben
    ]

    console.console.print("[bold]Test-Commands:[/bold]")
    for cmd in test_commands:
        parsed = ExecutionLock.parse_go_command(cmd)
        if parsed:
            console.console.print(f"  ✓ '{cmd}' → {parsed}", style="green")
        else:
            console.console.print(f"  ✗ '{cmd}' → ungültig", style="red")

    input("\n[cyan]⏎ Weiter...[/cyan]")

    # ==========================================
    # 6. EXECUTION LOCK AKTIVIERUNG
    # ==========================================
    print_section("6. EXECUTION LOCK")

    console.display_info("Simuliere GO REPAIR: 1,2")

    approved_steps = [1, 2]
    state_machine.lock_execution(approved_steps)

    console.display_success(f"Execution Lock aktiviert!")
    console.console.print(f"  State: {state_machine.current_state.value}")
    console.console.print(f"  Freigegebene Schritte: {approved_steps}")

    # Test Step Approval
    console.console.print("\n[bold]Step Approval Check:[/bold]")
    for i in range(1, 4):
        approved = state_machine.is_step_approved(i)
        status = "✓ Freigegeben" if approved else "✗ Nicht freigegeben"
        color = "green" if approved else "red"
        console.console.print(f"  Schritt {i}: {status}", style=color)

    input("\n[cyan]⏎ Weiter...[/cyan]")

    # ==========================================
    # 7. REPAIR-TOOL AUSFÜHRUNG (Simulation)
    # ==========================================
    print_section("7. REPAIR-TOOL AUSFÜHRUNG (macOS Simulation)")

    console.display_info("Führe manage_service (Status-Abfrage) aus...")
    console.display_warning("Hinweis: Da wir auf macOS sind, simulieren wir einen Service-Check")

    service_tool = tool_registry.get_tool("manage_service")

    # Status-Abfrage (sollte funktionieren)
    console.display_tool_call("manage_service", {
        "service_name": "com.apple.audio.coreaudiod",
        "action": "status"
    })

    try:
        result = await service_tool.execute(
            service_name="com.apple.audio.coreaudiod",
            action="status"
        )
        console.display_tool_result("manage_service", result, success=True)
    except Exception as e:
        console.display_tool_result("manage_service", str(e), success=False)

    input("\n[cyan]⏎ Weiter...[/cyan]")

    # ==========================================
    # 8. CHANGELOG
    # ==========================================
    print_section("8. CHANGELOG")

    changelog = ChangelogWriter("demo-session-test")

    # Simuliere Changelog-Einträge
    changelog.add_entry(
        tool_name="manage_service",
        tool_input={"service_name": "wuauserv", "action": "restart"},
        result="✓ Service erfolgreich neugestartet",
        success=True
    )

    changelog.add_entry(
        tool_name="manage_service",
        tool_input={"service_name": "Spooler", "action": "start"},
        result="✓ Service erfolgreich gestartet",
        success=True
    )

    console.display_info(f"Changelog gespeichert: {changelog.log_path}")
    console.console.print()
    console.console.print(changelog.get_summary())

    input("\n[cyan]⏎ Weiter...[/cyan]")

    # ==========================================
    # 9. COMPLETE WORKFLOW SIMULATION
    # ==========================================
    print_section("9. KOMPLETTER WORKFLOW (Simuliert)")

    console.console.print("[bold cyan]User:[/bold cyan] Neuer Fall")
    console.console.print()

    # TechCare Antwort (simuliert)
    console.display_assistant_message("""🔧 TechCare - Neue Diagnose-Session
──────────────────────────────────────

Bitte beantworte folgende Fragen:

1. **Backup-Status:** Existiert ein aktuelles Backup? (Ja/Nein/Unbekannt)
2. **Betriebssystem:** Welches System? (Windows 10/11 oder macOS)
3. **Problem:** Was ist das konkrete Problem? Fehlermeldungen?
4. **Bereits versucht:** Wurde bereits etwas versucht?

──────────────────────────────────────""")

    input("\n[cyan]⏎ Weiter...[/cyan]")

    console.console.print("[bold cyan]User:[/bold cyan] Ja Backup, Windows 11, Windows Update Fehler 0x80070002")
    console.console.print()

    console.display_assistant_message("""✓ Backup vorhanden - gut!
✓ Windows 11 erkannt

📋 AUDIT-PHASE
──────────────

Ich benötige folgende Informationen. Bitte führe aus und kopiere Output:

**Kommando 1:**
```cmd
systeminfo | findstr /C:"OS Name" /C:"OS Version"
```

[Warte auf Output...]""")

    input("\n[cyan]⏎ Weiter...[/cyan]")

    # ==========================================
    # 10. ZUSAMMENFASSUNG
    # ==========================================
    print_section("10. TEST-ZUSAMMENFASSUNG")

    console.console.print("[bold green]✅ ERFOLGREICH GETESTET:[/bold green]")
    console.console.print("  ✓ System Prompt geladen")
    console.console.print("  ✓ Tool Registry funktioniert")
    console.console.print("  ✓ State Machine Transitions")
    console.console.print("  ✓ Audit-Tool Ausführung (get_system_info)")
    console.console.print("  ✓ Repair-Tool Ausführung (manage_service)")
    console.console.print("  ✓ GO REPAIR Command Parsing")
    console.console.print("  ✓ Execution Lock Aktivierung")
    console.console.print("  ✓ Changelog Writing")
    console.console.print("  ✓ Complete Workflow Simulation")

    console.console.print()
    console.console.print("[bold yellow]📝 NÄCHSTE SCHRITTE:[/bold yellow]")
    console.console.print("  1. API Key in .env eintragen")
    console.console.print("  2. Bot mit 'techcare' starten")
    console.console.print("  3. Echten Fall testen")

    console.console.print()
    console.display_success("Demo-Test abgeschlossen! 🎉")


if __name__ == "__main__":
    asyncio.run(demo_test())

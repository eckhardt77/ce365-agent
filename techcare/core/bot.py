"""
TechCare Bot - AI-powered IT Maintenance Assistant

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
Licensed under MIT License
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from techcare.core.client import AnthropicClient
from techcare.core.session import Session
from techcare.tools.registry import ToolRegistry
from techcare.tools.executor import CommandExecutor
from techcare.workflow.state_machine import WorkflowStateMachine
from techcare.workflow.lock import ExecutionLock
from techcare.storage.changelog import ChangelogWriter
from techcare.config.system_prompt import get_system_prompt
from techcare.ui.console import RichConsole

# Learning System
from techcare.learning.case_library import CaseLibrary, Case

# Security - PII Detection
from techcare.security.pii_detector import get_pii_detector

# Tools importieren
from techcare.tools.audit.system_info import SystemInfoTool
from techcare.tools.audit.logs import CheckSystemLogsTool
from techcare.tools.audit.processes import CheckRunningProcessesTool
from techcare.tools.audit.updates import CheckSystemUpdatesTool
from techcare.tools.audit.backup import CheckBackupStatusTool
from techcare.tools.audit.stress_tests import (
    StressTestCPUTool, StressTestMemoryTool, TestDiskSpeedTool,
    CheckSystemTemperatureTool, RunStabilityTestTool
)
from techcare.tools.repair.service_manager import ServiceManagerTool
from techcare.tools.repair.disk_cleanup import DiskCleanupTool
from techcare.tools.repair.network_tools import FlushDNSCacheTool, ResetNetworkStackTool
from techcare.tools.repair.system_repair import RunSFCScanTool, RepairDiskPermissionsTool, RepairDiskTool
from techcare.tools.repair.updates import InstallSystemUpdatesTool
from techcare.tools.repair.backup import CreateRestorePointTool, TriggerTimeMachineBackupTool
from techcare.tools.research.web_search import WebSearchTool, WebSearchInstantAnswerTool


class TechCareBot:
    """
    TechCare Bot - IT-Wartungs-Assistent

    Orchestriert:
    - Anthropic Tool Use Loop
    - Workflow State Machine
    - Tool Execution
    - User Interaction
    """

    def __init__(self):
        # Core Components
        self.client = AnthropicClient()
        self.session = Session()
        self.console = RichConsole()
        self.state_machine = WorkflowStateMachine()
        self.changelog = ChangelogWriter(self.session.session_id)

        # Learning System
        self.case_library = CaseLibrary()

        # Security - PII Detection
        self.pii_detector = get_pii_detector()

        # Session Tracking für Learning
        self.session_start_time = datetime.now()
        self.detected_os_type: Optional[str] = None
        self.detected_os_version: Optional[str] = None
        self.problem_description: Optional[str] = None
        self.error_codes: Optional[str] = None
        self.diagnosed_root_cause: Optional[str] = None
        self.similar_case_offered: Optional[int] = None  # Case ID wenn angeboten

        # Tool System
        self.tool_registry = ToolRegistry()
        self._register_tools()

        # Executor
        self.executor = CommandExecutor(
            tool_registry=self.tool_registry,
            state_machine=self.state_machine,
            changelog_writer=self.changelog,
        )

        # System Prompt
        self.system_prompt = get_system_prompt()

    def _register_tools(self):
        """Alle Tools registrieren"""
        # Audit Tools - System Info
        self.tool_registry.register(SystemInfoTool())
        self.tool_registry.register(CheckSystemLogsTool())
        self.tool_registry.register(CheckRunningProcessesTool())
        self.tool_registry.register(CheckSystemUpdatesTool())
        self.tool_registry.register(CheckBackupStatusTool())

        # Audit Tools - Stress Tests & Diagnostics
        self.tool_registry.register(StressTestCPUTool())
        self.tool_registry.register(StressTestMemoryTool())
        self.tool_registry.register(TestDiskSpeedTool())
        self.tool_registry.register(CheckSystemTemperatureTool())
        self.tool_registry.register(RunStabilityTestTool())

        # Research Tools (Web Search)
        self.tool_registry.register(WebSearchTool())
        self.tool_registry.register(WebSearchInstantAnswerTool())

        # Repair Tools - System
        self.tool_registry.register(ServiceManagerTool())
        self.tool_registry.register(DiskCleanupTool())
        self.tool_registry.register(FlushDNSCacheTool())
        self.tool_registry.register(ResetNetworkStackTool())
        self.tool_registry.register(RunSFCScanTool())
        self.tool_registry.register(RepairDiskPermissionsTool())
        self.tool_registry.register(RepairDiskTool())
        self.tool_registry.register(InstallSystemUpdatesTool())

        # Repair Tools - Backup
        self.tool_registry.register(CreateRestorePointTool())
        self.tool_registry.register(TriggerTimeMachineBackupTool())

        self.console.display_info(
            f"🔧 Tools registriert: {len(self.tool_registry)} "
            f"(Audit: {len(self.tool_registry.get_audit_tools())}, "
            f"Repair: {len(self.tool_registry.get_repair_tools())})"
        )

    async def run(self):
        """Main Bot Loop"""
        self.console.display_logo()
        self.console.display_info(f"Session ID: {self.session.session_id}")
        self.console.display_info("Tippe 'exit' oder 'quit' zum Beenden")

        # Learning Stats anzeigen
        try:
            stats = self.case_library.get_statistics()
            if stats['total_cases'] > 0:
                self.console.display_info(
                    f"💡 Learning: {stats['total_cases']} Fälle gespeichert, "
                    f"{stats['total_reuses']} Wiederverwendungen"
                )
        except:
            pass

        self.console.display_separator()

        while True:
            try:
                # User Input
                user_input = self.console.get_input()

                if not user_input:
                    continue

                # Exit Commands
                if user_input.lower() in ["exit", "quit", "q"]:
                    self.console.display_success("Session beendet. Auf Wiedersehen!")
                    break

                # Special Command: stats
                if user_input.lower() == "stats":
                    stats = self.case_library.get_statistics()
                    self.console.display_learning_stats(stats)
                    continue

                # GO REPAIR Command
                if ExecutionLock.is_go_command(user_input):
                    await self.handle_go_repair(user_input)
                    continue

                # Learning: Problem-Info extrahieren
                self._extract_problem_info(user_input)

                # Learning: Nach 2+ Messages, prüfe ob ähnliche Fälle
                if len(self.session.messages) >= 2 and self.detected_os_type:
                    # Nur einmal anbieten
                    if self.similar_case_offered is None:
                        similar_found = await self._check_for_similar_cases()
                        if similar_found:
                            # Warte auf User-Entscheidung (1 oder 2)
                            continue

                # Process Message
                self.console.display_separator()
                await self.process_message(user_input)

            except KeyboardInterrupt:
                self.console.display_warning("\n\nSession unterbrochen. Beende...")
                break
            except Exception as e:
                self.console.display_error(f"Unerwarteter Fehler: {str(e)}")

        # Cleanup
        if self.changelog.entries:
            self.console.display_info("\n📝 Changelog gespeichert:")
            self.console.display_info(str(self.changelog.log_path))

            # Learning: Session speichern wenn erfolgreich
            if self.state_machine.current_state.value == "completed":
                await self._save_session_as_case(success=True)

    async def process_message(self, user_input: str):
        """
        Message verarbeiten mit Tool Use Loop

        Tool Use Loop:
        1. PII Detection & Anonymisierung
        2. User Message zu History
        3. Claude API Call mit Tools
        4. stop_reason prüfen:
           - "end_turn" → Text-Antwort zurückgeben
           - "tool_use" → handle_tool_use() → rekursiv fortsetzen
        """
        # 1. PII Detection & Anonymisierung
        anonymized_input, detections = self.pii_detector.anonymize(user_input)

        # User-Warning anzeigen wenn PII gefunden
        if detections and self.pii_detector.show_warnings:
            warning = self.pii_detector.format_detection_warning(detections)
            self.console.display_warning(warning)

        # Anonymisierten Input verwenden (für Claude API & Learning System)
        processed_input = anonymized_input if detections else user_input

        # 2. User Message zu History
        self.session.add_message(role="user", content=processed_input)

        # API Call
        try:
            response = self.client.create_message(
                messages=self.session.get_messages(),
                system=self.system_prompt,
                tools=self.tool_registry.get_tool_definitions(),
            )

            # stop_reason prüfen
            if response.stop_reason == "end_turn":
                # Text-Antwort extrahieren
                text_content = self._extract_text(response.content)
                if text_content:
                    self.session.add_message(role="assistant", content=text_content)
                    self.console.display_assistant_message(text_content)

            elif response.stop_reason == "tool_use":
                # Tool Use Loop
                await self.handle_tool_use(response)

            else:
                self.console.display_warning(
                    f"Unbekannter stop_reason: {response.stop_reason}"
                )

        except Exception as e:
            self.console.display_error(f"API Fehler: {str(e)}")

    async def handle_tool_use(self, response):
        """
        Tool Use Blocks verarbeiten

        Flow:
        1. Text + Tool Use Blocks extrahieren
        2. Tools ausführen (mit State Validation)
        3. Tool Results sammeln
        4. Assistant Message + Tool Results zu History
        5. Rekursiv process_message() fortsetzen
        """
        # Text + Tool Use Blocks extrahieren
        text_parts = []
        tool_uses = []

        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_uses.append(block)

        # Text anzeigen (wenn vorhanden)
        if text_parts:
            text = "\n".join(text_parts)
            self.console.display_assistant_message(text)

        # Tools ausführen
        tool_results = []
        for tool_use in tool_uses:
            tool_name = tool_use.name
            tool_input = tool_use.input
            tool_id = tool_use.id

            self.console.display_tool_call(tool_name, tool_input)

            # Tool ausführen
            success, result = await self.executor.execute_tool(tool_name, tool_input)

            self.console.display_tool_result(tool_name, result, success)

            # Tool Result für API
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": result,
                }
            )

        # Assistant Message (mit Tool Use) zu History
        self.session.add_message(role="assistant", content=response.content)

        # Tool Results zu History
        self.session.add_message(role="user", content=tool_results)

        # Rekursiv fortsetzen (ohne User Input)
        self.console.display_separator()
        await self.continue_after_tools()

    async def continue_after_tools(self):
        """Nach Tool Execution fortsetzen"""
        try:
            response = self.client.create_message(
                messages=self.session.get_messages(),
                system=self.system_prompt,
                tools=self.tool_registry.get_tool_definitions(),
            )

            if response.stop_reason == "end_turn":
                text_content = self._extract_text(response.content)
                if text_content:
                    self.session.add_message(role="assistant", content=text_content)
                    self.console.display_assistant_message(text_content)

            elif response.stop_reason == "tool_use":
                # Weitere Tool Calls
                await self.handle_tool_use(response)

        except Exception as e:
            self.console.display_error(f"API Fehler: {str(e)}")

    async def handle_go_repair(self, command: str):
        """
        GO REPAIR Befehl verarbeiten

        Flow:
        1. Parse Command → approved_steps
        2. State Machine Lock aktivieren
        3. Bestätigung anzeigen
        """
        # Parse Command
        approved_steps = ExecutionLock.parse_go_command(command)

        if not approved_steps:
            self.console.display_error(
                "Ungültiger GO REPAIR Befehl.\n"
                "Format: GO REPAIR: 1,2,3 oder GO REPAIR: 1-3"
            )
            return

        # State Check
        if self.state_machine.current_state.value != "plan_ready":
            self.console.display_error(
                f"GO REPAIR kann nur im PLAN_READY State verwendet werden.\n"
                f"Aktueller State: {self.state_machine.current_state.value}\n"
                f"Workflow: Audit → Analyse → Plan → GO REPAIR"
            )
            return

        # Lock aktivieren
        try:
            self.state_machine.lock_execution(approved_steps)
            self.console.display_success(
                f"✓ Execution Lock aktiviert für Schritte: {ExecutionLock.format_steps(approved_steps)}"
            )
            self.console.display_info(
                "Claude kann jetzt die freigegebenen Repair-Tools ausführen."
            )

            # Claude informieren
            approval_message = (
                f"GO REPAIR Freigabe erhalten für Schritte: {ExecutionLock.format_steps(approved_steps)}. "
                "Führe jetzt die freigegebenen Schritte aus."
            )
            await self.process_message(approval_message)

        except ValueError as e:
            self.console.display_error(str(e))

    def _extract_text(self, content: List[Any]) -> str:
        """Text aus Content Blocks extrahieren"""
        text_parts = []
        for block in content:
            if hasattr(block, "type") and block.type == "text":
                text_parts.append(block.text)
            elif isinstance(block, str):
                text_parts.append(block)
        return "\n".join(text_parts)

    # ==========================================
    # LEARNING SYSTEM METHODS
    # ==========================================

    def _extract_problem_info(self, user_message: str):
        """
        Problem-Info aus User-Message extrahieren

        Versucht zu erkennen:
        - OS-Type (windows/macos)
        - OS-Version
        - Error-Codes
        - Problem-Beschreibung
        """
        message_lower = user_message.lower()

        # OS-Type Detection
        if "windows" in message_lower:
            self.detected_os_type = "windows"
            # Version
            if "windows 11" in message_lower or "win 11" in message_lower:
                self.detected_os_version = "Windows 11"
            elif "windows 10" in message_lower or "win 10" in message_lower:
                self.detected_os_version = "Windows 10"
        elif "macos" in message_lower or "mac os" in message_lower:
            self.detected_os_type = "macos"
            # Version
            if "sequoia" in message_lower or "15" in message_lower:
                self.detected_os_version = "macOS 15 Sequoia"
            elif "sonoma" in message_lower or "14" in message_lower:
                self.detected_os_version = "macOS 14 Sonoma"
            elif "ventura" in message_lower or "13" in message_lower:
                self.detected_os_version = "macOS 13 Ventura"

        # Error-Codes extrahieren (0x..., Error-Code: ...)
        import re
        error_patterns = [
            r'0x[0-9A-Fa-f]+',  # Hex-Codes
        ]

        found_errors = []
        for pattern in error_patterns:
            matches = re.findall(pattern, user_message, re.IGNORECASE)
            found_errors.extend(matches)

        if found_errors:
            # Nur unique Error-Codes, keine Duplikate
            self.error_codes = ", ".join(sorted(set(found_errors)))

        # Problem-Beschreibung (User-Message als Ganzes)
        if not self.problem_description:
            self.problem_description = user_message

    async def _check_for_similar_cases(self) -> bool:
        """
        Nach ähnlichen Fällen suchen und anbieten

        Returns:
            True wenn ähnlicher Fall gefunden und angeboten
        """
        if not self.detected_os_type or not self.problem_description:
            return False

        # Ähnliche Fälle suchen
        similar_cases = self.case_library.find_similar_cases(
            os_type=self.detected_os_type,
            problem_description=self.problem_description,
            error_code=self.error_codes,
            limit=1,  # Nur bester Match
            min_similarity=0.6  # Mindestens 60% Ähnlichkeit
        )

        if not similar_cases:
            return False

        case, similarity = similar_cases[0]

        # Nur anbieten wenn Similarity hoch genug und Fall bereits wiederverwendet
        if similarity < 0.6:
            return False

        # Bekannte Lösung anbieten
        case_data = {
            'problem_description': case.problem_description,
            'root_cause': case.root_cause,
            'solution_plan': case.solution_plan,
            'reuse_count': case.reuse_count,
            'success_rate': case.success_rate
        }

        self.console.display_known_solution(case_data, similarity)

        # Case ID speichern für späteren Reuse-Tracking
        self.similar_case_offered = case.id

        return True

    async def _save_session_as_case(self, success: bool):
        """
        Session als Fall für Learning speichern

        Wird aufgerufen wenn Session erfolgreich abgeschlossen
        """
        # Nur speichern wenn alle nötigen Infos vorhanden
        if not all([
            self.detected_os_type,
            self.problem_description,
            self.diagnosed_root_cause,
            self.state_machine.repair_plan
        ]):
            self.console.display_warning(
                "⚠️  Session konnte nicht für Learning gespeichert werden (fehlende Informationen)"
            )
            return

        # Duration berechnen
        duration = (datetime.now() - self.session_start_time).total_seconds() / 60

        # Case erstellen
        case = Case(
            os_type=self.detected_os_type,
            os_version=self.detected_os_version or "Unknown",
            problem_description=self.problem_description,
            error_codes=self.error_codes,
            root_cause=self.diagnosed_root_cause,
            solution_plan=self.state_machine.repair_plan,
            executed_steps=str(self.state_machine.executed_steps),
            success=success,
            session_id=self.session.session_id,
            tokens_used=self.client.get_token_usage()['total_tokens'],
            duration_minutes=int(duration)
        )

        try:
            case_id = self.case_library.save_case(case)
            self.console.display_success(
                f"✓ Fall für Learning gespeichert (ID: {case_id})"
            )

            # Wenn bekannte Lösung verwendet wurde, Reuse-Counter aktualisieren
            if self.similar_case_offered and success:
                self.case_library.mark_case_reused(
                    self.similar_case_offered,
                    success=True
                )
                self.console.display_info(
                    f"✓ Wiederverwendungs-Counter aktualisiert (Case {self.similar_case_offered})"
                )

        except Exception as e:
            self.console.display_error(
                f"❌ Fehler beim Speichern für Learning: {str(e)}"
            )

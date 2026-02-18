"""
CE365 Agent - AI-powered IT Maintenance Assistant

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
Licensed under MIT License
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from ce365.core.providers import create_provider
from ce365.core.session import Session
from ce365.tools.registry import ToolRegistry
from ce365.tools.executor import CommandExecutor
from ce365.workflow.state_machine import WorkflowStateMachine
from ce365.workflow.lock import ExecutionLock
from ce365.storage.changelog import ChangelogWriter
from ce365.config.system_prompt import get_system_prompt
from ce365.ui.console import RichConsole

# Learning System
from ce365.learning.case_library import CaseLibrary, Case

# Security - PII Detection
try:
    from ce365.security.pii_detector import get_pii_detector
    PII_AVAILABLE = True
except ImportError:
    PII_AVAILABLE = False
    print("⚠️  PII Detection nicht verfügbar (Python 3.14 Kompatibilität)")

# Tools importieren
from ce365.tools.audit.system_info import SystemInfoTool
from ce365.tools.audit.logs import CheckSystemLogsTool
from ce365.tools.audit.processes import CheckRunningProcessesTool
from ce365.tools.audit.updates import CheckSystemUpdatesTool
from ce365.tools.audit.backup import CheckBackupStatusTool
from ce365.tools.audit.stress_tests import (
    StressTestCPUTool, StressTestMemoryTool, TestDiskSpeedTool,
    CheckSystemTemperatureTool, RunStabilityTestTool
)
from ce365.tools.audit.reporting import GenerateSystemReportTool
from ce365.tools.audit.security import CheckSecurityStatusTool
from ce365.tools.audit.startup import CheckStartupProgramsTool
from ce365.tools.audit.malware_scan import MalwareScanTool  # NEU
from ce365.tools.audit.drivers import CheckDriversTool  # NEU - Driver Check
from ce365.tools.repair.service_manager import ServiceManagerTool
from ce365.tools.repair.disk_cleanup import DiskCleanupTool
from ce365.tools.repair.network_tools import FlushDNSCacheTool, ResetNetworkStackTool
from ce365.tools.repair.system_repair import RunSFCScanTool, RepairDiskPermissionsTool, RepairDiskTool
from ce365.tools.repair.updates import InstallSystemUpdatesTool
from ce365.tools.repair.backup import CreateRestorePointTool, TriggerTimeMachineBackupTool
from ce365.tools.repair.startup import DisableStartupProgramTool, EnableStartupProgramTool
from ce365.tools.repair.update_scheduler import ScheduleSystemUpdatesTool
from ce365.tools.research.web_search import WebSearchTool, WebSearchInstantAnswerTool
from ce365.tools.analysis.root_cause import RootCauseAnalyzer  # NEU

# License & Usage
from ce365.core.license import validate_license, check_edition_features
from ce365.core.usage_tracker import UsageTracker
from ce365.config.settings import get_settings


class CE365Bot:
    """
    CE365 Agent - IT-Wartungs-Assistent

    Orchestriert:
    - Anthropic Tool Use Loop
    - Workflow State Machine
    - Tool Execution
    - User Interaction
    """

    def __init__(self):
        # Core Components — Multi-Provider
        settings = get_settings()
        provider_keys = {
            "anthropic": settings.anthropic_api_key,
            "openai": settings.openai_api_key,
            "openrouter": settings.openrouter_api_key,
        }
        self.client = create_provider(
            provider_name=settings.llm_provider,
            api_key=provider_keys[settings.llm_provider],
            model=settings.llm_model,
        )
        self.session = Session()
        self.console = RichConsole()
        self.state_machine = WorkflowStateMachine()
        self.changelog = ChangelogWriter(self.session.session_id)

        # Learning System
        self.case_library = CaseLibrary()

        # Security - PII Detection
        if PII_AVAILABLE:
            self.pii_detector = get_pii_detector()
        else:
            self.pii_detector = None

        # Session Tracking für Learning
        self.session_start_time = datetime.now()
        self.detected_os_type: Optional[str] = None
        self.detected_os_version: Optional[str] = None
        self.problem_description: Optional[str] = None
        self.error_codes: Optional[str] = None
        self.diagnosed_root_cause: Optional[str] = None
        self.similar_case_offered: Optional[int] = None  # Case ID wenn angeboten

        # Edition-Validierung VOR Tool-Registrierung:
        # Nur "community" und "pro" sind gültige Editionen
        if settings.edition not in ("community", "pro"):
            settings.edition = "community"

        # Pro ohne gültige Credentials → Downgrade auf Community
        if settings.edition == "pro" and (not settings.license_key or not settings.license_server_url):
            settings.edition = "community"
            self._edition_downgraded = True
        else:
            self._edition_downgraded = False

        # Usage Tracker (Community: 5 Repair Runs/Monat)
        self.usage_tracker = UsageTracker(edition=settings.edition)

        # Session Management (Pro: Heartbeat)
        self._session_token: Optional[str] = None
        self._heartbeat_task: Optional[asyncio.Task] = None

        # Tool System
        self.tool_registry = ToolRegistry()
        self._register_tools()

        # Executor
        self.executor = CommandExecutor(
            tool_registry=self.tool_registry,
            state_machine=self.state_machine,
            changelog_writer=self.changelog,
            usage_tracker=self.usage_tracker,
        )

        # System Prompt
        self.system_prompt = get_system_prompt()

    def _register_tools(self):
        """Alle Tools registrieren (mit Edition-basiertem Feature-Gating)"""
        settings = get_settings()
        edition = settings.edition

        # === Basis-Audit Tools (alle Editionen) ===
        self.tool_registry.register(SystemInfoTool())
        self.tool_registry.register(CheckSystemLogsTool())
        self.tool_registry.register(CheckRunningProcessesTool())
        self.tool_registry.register(CheckSystemUpdatesTool())
        self.tool_registry.register(CheckBackupStatusTool())
        self.tool_registry.register(CheckSecurityStatusTool())
        self.tool_registry.register(CheckStartupProgramsTool())

        # === Basis-Repair Tools (alle Editionen, Free: 5/Monat) ===
        self.tool_registry.register(ServiceManagerTool())
        self.tool_registry.register(DiskCleanupTool())
        self.tool_registry.register(FlushDNSCacheTool())

        # === Erweiterte Audit Tools (Pro) ===
        if check_edition_features(edition, "advanced_audit"):
            self.tool_registry.register(StressTestCPUTool())
            self.tool_registry.register(StressTestMemoryTool())
            self.tool_registry.register(TestDiskSpeedTool())
            self.tool_registry.register(CheckSystemTemperatureTool())
            self.tool_registry.register(RunStabilityTestTool())
            self.tool_registry.register(MalwareScanTool())
            self.tool_registry.register(GenerateSystemReportTool())
            self.tool_registry.register(CheckDriversTool())

        # === Erweiterte Repair Tools (Pro) ===
        if check_edition_features(edition, "advanced_repair"):
            self.tool_registry.register(RunSFCScanTool())
            self.tool_registry.register(RepairDiskPermissionsTool())
            self.tool_registry.register(RepairDiskTool())
            self.tool_registry.register(ResetNetworkStackTool())
            self.tool_registry.register(InstallSystemUpdatesTool())
            self.tool_registry.register(CreateRestorePointTool())
            self.tool_registry.register(TriggerTimeMachineBackupTool())
            self.tool_registry.register(DisableStartupProgramTool())
            self.tool_registry.register(EnableStartupProgramTool())
            self.tool_registry.register(ScheduleSystemUpdatesTool())

        # === Web Search + Root Cause Analysis (Pro) ===
        if check_edition_features(edition, "web_search"):
            self.tool_registry.register(WebSearchTool())
            self.tool_registry.register(WebSearchInstantAnswerTool())

        if check_edition_features(edition, "root_cause_analysis"):
            self.tool_registry.register(RootCauseAnalyzer())

        self.console.display_info(
            f"🔧 Tools registriert: {len(self.tool_registry)} "
            f"(Audit: {len(self.tool_registry.get_audit_tools())}, "
            f"Repair: {len(self.tool_registry.get_repair_tools())})"
        )

    async def run(self):
        """Main Bot Loop"""
        self.console.display_logo()

        # Lizenz-Check (wenn License Key gesetzt ist)
        await self._check_license()

        # Pro: Session starten + Heartbeat
        settings = get_settings()
        if settings.edition == "pro" and settings.license_server_url:
            await self._start_session()

        # ToS Akzeptanz prüfen (nur beim ersten Start)
        if not self._check_tos_acceptance():
            return

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

        # Automatischer System-Statusbericht beim Start
        await self._display_initial_system_status()

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
                await self.process_message(user_input)

            except KeyboardInterrupt:
                self.console.display_warning("\n\nSession unterbrochen. Beende...")
                break
            except Exception as e:
                self.console.display_error(f"Unerwarteter Fehler: {str(e)}")

        # Session freigeben (Pro)
        await self._release_session()

        # Cleanup
        if self.changelog.entries:
            self.console.display_info("\n📝 Changelog gespeichert:")
            self.console.display_info(str(self.changelog.log_path))

            # Learning: Session speichern wenn erfolgreich
            if self.state_machine.current_state.value == "completed":
                await self._save_session_as_case(success=True)

    def _check_tos_acceptance(self) -> bool:
        """
        Prüft ob User ToS akzeptiert hat

        Returns:
            True wenn akzeptiert, False wenn abgelehnt (Bot wird beendet)
        """
        import os
        from pathlib import Path

        # ToS-Acceptance File
        tos_file = Path.home() / ".ce365_tos_accepted"

        # Wenn Datei existiert: User hat schon zugestimmt
        if tos_file.exists():
            return True

        # Disclaimer anzeigen
        self.console.display_separator()
        self.console.console.print("[bold red]⚠️  WICHTIG: HAFTUNGSAUSSCHLUSS[/bold red]\n")

        disclaimer_path = Path(__file__).parent.parent.parent / "DISCLAIMER.txt"

        if disclaimer_path.exists():
            with open(disclaimer_path, 'r', encoding='utf-8') as f:
                disclaimer = f.read()
            self.console.console.print(disclaimer)
        else:
            # Fallback wenn Datei nicht gefunden
            self.console.console.print("""
CE365 Agent wird "AS IS" bereitgestellt, OHNE JEGLICHE GARANTIE.

⚠️  KEINE HAFTUNG für:
   - Datenverlust
   - System-Schäden
   - Fehlgeschlagene Reparaturen

✅ Nutzung auf EIGENE VERANTWORTUNG
✅ BACKUP-PFLICHT vor Reparaturen
✅ Technisches Verständnis erforderlich

Durch Nutzung akzeptieren Sie diese Bedingungen.
            """)

        self.console.display_separator()
        self.console.console.print()

        # User-Eingabe
        while True:
            response = self.console.get_input(
                "Ich habe den Haftungsausschluss gelesen und akzeptiere die Bedingungen (ja/nein)"
            ).strip().lower()

            if response in ["ja", "yes", "y", "j"]:
                # Akzeptanz speichern
                try:
                    tos_file.touch()
                    self.console.display_success("✅ Bedingungen akzeptiert. Viel Erfolg!")
                    self.console.console.print()
                    return True
                except Exception as e:
                    self.console.display_warning(f"Konnte Akzeptanz nicht speichern: {e}")
                    return True  # Trotzdem weitermachen

            elif response in ["nein", "no", "n"]:
                self.console.console.print()
                self.console.console.print("[yellow]ℹ️  Du hast die Bedingungen nicht akzeptiert.[/yellow]")
                self.console.console.print("[yellow]   CE365 Agent wird beendet.[/yellow]")
                self.console.console.print()
                self.console.console.print("[dim]Bei Fragen: https://github.com/yourusername/ce365-agent/issues[/dim]")
                self.console.console.print()
                return False

            else:
                self.console.console.print("[red]❌ Bitte antworte mit 'ja' oder 'nein'[/red]\n")

    async def _check_license(self):
        """
        Prüft Lizenz beim Start (wenn License Key gesetzt)

        Features:
        - Online-Validierung via Backend
        - Offline-Fallback mit gecachter Lizenz
        - Edition-Info anzeigen
        """
        settings = get_settings()

        # Edition wurde in __init__ downgraded (Pro ohne Credentials)
        if self._edition_downgraded:
            self.console.display_error(
                "❌ Pro Edition erfordert einen gültigen Lizenzschlüssel und Lizenzserver.\n"
                "   Setze LICENSE_KEY und LICENSE_SERVER_URL in der .env Datei.\n"
                "   Oder nutze EDITION=community für die kostenlose Version."
            )
            import sys
            sys.exit(1)

        # Community braucht keine Lizenz
        if settings.edition == "community":
            self.console.display_info("📦 Edition: Community (keine Lizenz erforderlich)")
            return

        try:
            self.console.console.print("[dim]🔑 Validiere Lizenz...[/dim]")

            # Lizenz validieren
            result = await validate_license(
                license_key=settings.license_key,
                license_server_url=settings.license_server_url,
                timeout=5
            )

            if not result["valid"]:
                self.console.display_error(f"❌ Ungültige Lizenz: {result.get('error', 'Unknown error')}")
                self.console.console.print()
                self.console.console.print("[yellow]Bitte kontaktiere den Support oder prüfe deine Lizenz.[/yellow]")
                self.console.console.print()
                import sys
                sys.exit(1)

            # Edition-Info anzeigen
            edition_names = {
                "community": "Community",
                "pro": "Pro",
            }

            edition_display = edition_names.get(result["edition"], result["edition"])

            self.console.display_success(f"✓ Lizenz gültig: {edition_display}")

            # Offline-Hinweis wenn gecachte Lizenz verwendet
            if result.get("_offline"):
                self.console.display_warning("⚠️  Offline-Modus (gecachte Lizenz)")

            # Ablaufdatum anzeigen
            if result.get("expires_at") and result["expires_at"] != "never":
                from datetime import datetime
                expires_at = datetime.fromisoformat(result["expires_at"])
                self.console.display_info(f"Gültig bis: {expires_at.strftime('%d.%m.%Y')}")

            # Max Systems anzeigen
            if result.get("max_systems") and result["max_systems"] > 0:
                self.console.display_info(f"Max. Systeme: {result['max_systems']}")

        except Exception as e:
            self.console.display_error(f"❌ Lizenz-Check fehlgeschlagen: {str(e)}")
            self.console.console.print()
            import sys
            sys.exit(1)

    async def _display_initial_system_status(self):
        """
        Zeigt automatischen System-Statusbericht beim Start

        Ruft auf:
        - get_system_info (OS, Hardware, Disk)
        - check_backup_status (Backup-Zustand)
        - check_security_status (Firewall, Antivirus)
        """
        try:
            self.console.display_info("🔍 Erstelle System-Statusbericht...")
            self.console.display_info("")

            # 1. System Info
            system_info_tool = self.tool_registry.get_tool("get_system_info")
            if system_info_tool:
                result = await system_info_tool.execute()
                self.console.display_tool_result("get_system_info", result)
                self.console.display_info("")

            # 2. Backup Status
            backup_tool = self.tool_registry.get_tool("check_backup_status")
            if backup_tool:
                result = await backup_tool.execute()
                self.console.display_tool_result("check_backup_status", result)
                self.console.display_info("")

            # 3. Security Status
            security_tool = self.tool_registry.get_tool("check_security_status")
            if security_tool:
                result = await security_tool.execute()
                self.console.display_tool_result("check_security_status", result)
                self.console.display_info("")

            self.console.display_success("✅ System-Statusbericht abgeschlossen")
            self.console.display_info("💬 Wie kann ich dir helfen?")

        except Exception as e:
            self.console.display_warning(f"⚠️  Statusbericht konnte nicht vollständig erstellt werden: {str(e)}")

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
        if self.pii_detector:
            anonymized_input, detections = self.pii_detector.anonymize(user_input)

            # User-Warning anzeigen wenn PII gefunden
            if detections and self.pii_detector.show_warnings:
                warning = self.pii_detector.format_detection_warning(detections)
                self.console.display_warning(warning)

            # Anonymisierten Input verwenden (für Claude API & Learning System)
            processed_input = anonymized_input if detections else user_input
        else:
            # PII Detection deaktiviert
            processed_input = user_input

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

            # BUGFIX: XML-Tags aus Tool-Namen entfernen (Claude API Bug)
            if '"' in tool_name or '<' in tool_name or '>' in tool_name:
                # Tool-Name ist korrupt, extrahiere nur den ersten Teil
                tool_name = tool_name.split('"')[0].split('<')[0].strip()
                self.console.display_warning(f"Tool-Name korrigiert zu: {tool_name}")

            # Tool ausführen mit Spinner
            with self.console.show_spinner(f"🔧 Executing {tool_name}"):
                success, result = await self.executor.execute_tool(tool_name, tool_input)

            # Ergebnis anzeigen
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
    # SESSION MANAGEMENT (Pro)
    # ==========================================

    async def _start_session(self):
        """Startet Session auf Lizenzserver (Pro)"""
        settings = get_settings()
        if not settings.license_server_url:
            return

        try:
            import httpx
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.post(
                    f"{settings.license_server_url}/api/license/session/start",
                    json={
                        "license_key": settings.license_key,
                        "system_fingerprint": "",
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        self._session_token = data["session_token"]
                        # Heartbeat starten
                        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
                    else:
                        self.console.display_error(
                            f"Session konnte nicht gestartet werden: {data.get('error', '')}"
                        )
                        import sys
                        sys.exit(1)
        except Exception as e:
            self.console.display_warning(f"Session-Start fehlgeschlagen: {e}")

    async def _heartbeat_loop(self):
        """Sendet Heartbeat alle 5 Minuten"""
        settings = get_settings()
        while True:
            try:
                await asyncio.sleep(300)  # 5 Minuten
                if not self._session_token:
                    break

                import httpx
                async with httpx.AsyncClient(timeout=5) as client:
                    await client.post(
                        f"{settings.license_server_url}/api/license/session/heartbeat",
                        json={"session_token": self._session_token},
                    )
            except asyncio.CancelledError:
                break
            except Exception:
                pass  # Heartbeat-Fehler ignorieren

    async def _release_session(self):
        """Gibt Session auf Lizenzserver frei"""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None

        if not self._session_token:
            return

        settings = get_settings()
        if not settings.license_server_url:
            return

        try:
            import httpx
            async with httpx.AsyncClient(timeout=5) as client:
                await client.post(
                    f"{settings.license_server_url}/api/license/session/release",
                    json={"session_token": self._session_token},
                )
        except Exception:
            pass  # Bei Exit ignorieren

        self._session_token = None

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

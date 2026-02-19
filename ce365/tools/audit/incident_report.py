"""
CE365 Agent - SOAP Incident Report Tool

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
Licensed under Source Available License

Generiert professionelle IT-Dokumentation im SOAP-Format
aus der aktuellen Session.
"""

import platform
from datetime import datetime
from typing import Dict, Any, Optional
from ce365.tools.base import AuditTool


class IncidentReportTool(AuditTool):
    """
    Generiert einen SOAP Incident Report aus der aktuellen Session.

    SOAP = Subjective, Objective, Assessment, Plan
    Etabliertes Dokumentationsformat fuer IT-Service-Reports.
    """

    def __init__(
        self,
        session=None,
        changelog=None,
        state_machine=None,
        bot=None,
    ):
        super().__init__()
        self._session = session
        self._changelog = changelog
        self._state_machine = state_machine
        self._bot = bot

    @property
    def name(self) -> str:
        return "generate_incident_report"

    @property
    def description(self) -> str:
        return (
            "Generiert einen professionellen Incident Report aus der aktuellen Session. "
            "Formate: 'soap' (S/O/A/P Sektionen) oder 'markdown' (vollstaendiger IT Report). "
            "Nutze dies: 1) Nach abgeschlossener Diagnose/Reparatur, 2) Fuer Kunden-Dokumentation, "
            "3) Fuer Audit-Nachweise, 4) Wenn der Techniker einen Report anfordert. "
            "Optional mit Audit-Log (Changelog-Eintraege)."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "format": {
                    "type": "string",
                    "enum": ["markdown", "soap"],
                    "description": "Report-Format: 'soap' fuer strukturierte S/O/A/P Sektionen, 'markdown' fuer vollstaendigen IT Report",
                    "default": "soap",
                },
                "include_audit_log": {
                    "type": "boolean",
                    "description": "Changelog-Eintraege (durchgefuehrte Aktionen) anhaengen",
                    "default": True,
                },
            },
            "required": [],
        }

    async def execute(self, **kwargs) -> str:
        report_format = kwargs.get("format", "soap")
        include_audit_log = kwargs.get("include_audit_log", True)

        try:
            if report_format == "soap":
                return self._generate_soap_report(include_audit_log)
            else:
                return self._generate_markdown_report(include_audit_log)
        except Exception as e:
            return f"Fehler beim Generieren des Reports: {str(e)}"

    # ------------------------------------------------------------------
    # Data helpers
    # ------------------------------------------------------------------

    def _get_session_id(self) -> str:
        if self._session:
            return self._session.session_id
        return "N/A"

    def _get_session_date(self) -> str:
        if self._session:
            return self._session.created_at.strftime("%d.%m.%Y %H:%M")
        return datetime.now().strftime("%d.%m.%Y %H:%M")

    def _get_problem_description(self) -> str:
        if self._bot and self._bot.problem_description:
            return self._bot.problem_description
        # Fallback: erste User-Message
        if self._session and self._session.messages:
            for msg in self._session.messages:
                if msg.get("role") == "user" and isinstance(msg.get("content"), str):
                    return msg["content"]
        return "Nicht dokumentiert"

    def _get_root_cause(self) -> str:
        if self._bot and self._bot.diagnosed_root_cause:
            return self._bot.diagnosed_root_cause
        return "Nicht ermittelt"

    def _get_os_info(self) -> str:
        if self._bot and self._bot.detected_os_type:
            os_type = self._bot.detected_os_type
            os_version = self._bot.detected_os_version or ""
            return f"{os_type} {os_version}".strip()
        # Fallback: aktuelles System
        sys_name = platform.system()
        if sys_name == "Darwin":
            sys_name = "macOS"
        return f"{sys_name} {platform.release()}"

    def _get_error_codes(self) -> Optional[str]:
        if self._bot and self._bot.error_codes:
            return self._bot.error_codes
        return None

    def _get_workflow_state(self) -> str:
        if self._state_machine:
            return self._state_machine.current_state.value
        return "unknown"

    def _get_changelog_entries(self) -> list:
        if self._changelog:
            return self._changelog.entries
        return []

    def _get_session_duration(self) -> str:
        if self._bot:
            delta = datetime.now() - self._bot.session_start_time
            minutes = int(delta.total_seconds() / 60)
            if minutes < 1:
                return "<1 min"
            if minutes < 60:
                return f"{minutes} min"
            hours = minutes // 60
            rest = minutes % 60
            return f"{hours}h {rest}min"
        return "N/A"

    def _get_technician(self) -> str:
        return "Steve (CE365 Agent)"

    # ------------------------------------------------------------------
    # SOAP Report
    # ------------------------------------------------------------------

    def _generate_soap_report(self, include_audit_log: bool) -> str:
        lines = []

        lines.append("=" * 60)
        lines.append("SOAP INCIDENT REPORT")
        lines.append("=" * 60)
        lines.append(f"Session:    {self._get_session_id()}")
        lines.append(f"Datum:      {self._get_session_date()}")
        lines.append(f"Techniker:  {self._get_technician()}")
        lines.append(f"System:     {self._get_os_info()}")
        lines.append(f"Dauer:      {self._get_session_duration()}")
        lines.append(f"Status:     {self._get_workflow_state()}")

        error_codes = self._get_error_codes()
        if error_codes:
            lines.append(f"Error-Codes: {error_codes}")

        lines.append("=" * 60)

        # S — Subjective
        lines.append("")
        lines.append("S — SUBJECTIVE (Gemeldetes Problem)")
        lines.append("-" * 60)
        lines.append(self._get_problem_description())

        # O — Objective
        lines.append("")
        lines.append("O — OBJECTIVE (Messwerte & Befunde)")
        lines.append("-" * 60)
        lines.extend(self._build_objective_section())

        # A — Assessment
        lines.append("")
        lines.append("A — ASSESSMENT (Diagnose)")
        lines.append("-" * 60)
        root_cause = self._get_root_cause()
        lines.append(f"Root Cause: {root_cause}")

        if self._state_machine and self._state_machine.repair_plan:
            lines.append("")
            lines.append("Reparatur-Plan:")
            lines.append(self._state_machine.repair_plan)

        # P — Plan
        lines.append("")
        lines.append("P — PLAN (Durchgefuehrte / Geplante Massnahmen)")
        lines.append("-" * 60)
        lines.extend(self._build_plan_section())

        # Audit Log
        if include_audit_log:
            changelog_entries = self._get_changelog_entries()
            if changelog_entries:
                lines.append("")
                lines.append("=" * 60)
                lines.append("AUDIT LOG")
                lines.append("=" * 60)
                for i, entry in enumerate(changelog_entries, 1):
                    status = "OK" if entry.success else "FEHLER"
                    lines.append(f"  {i}. [{entry.timestamp[:19]}] {entry.tool_name} — {status}")

        lines.append("")
        lines.append("=" * 60)
        lines.append("Ende des Reports")
        lines.append("=" * 60)

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Markdown Report
    # ------------------------------------------------------------------

    def _generate_markdown_report(self, include_audit_log: bool) -> str:
        lines = []

        lines.append("# IT Incident Report")
        lines.append("")
        lines.append("| Feld | Wert |")
        lines.append("|------|------|")
        lines.append(f"| **Session** | `{self._get_session_id()}` |")
        lines.append(f"| **Datum** | {self._get_session_date()} |")
        lines.append(f"| **Techniker** | {self._get_technician()} |")
        lines.append(f"| **System** | {self._get_os_info()} |")
        lines.append(f"| **Dauer** | {self._get_session_duration()} |")
        lines.append(f"| **Status** | {self._get_workflow_state()} |")

        error_codes = self._get_error_codes()
        if error_codes:
            lines.append(f"| **Error-Codes** | `{error_codes}` |")

        lines.append("")
        lines.append("---")

        # Problem
        lines.append("")
        lines.append("## Gemeldetes Problem")
        lines.append("")
        lines.append(self._get_problem_description())

        # Befunde
        lines.append("")
        lines.append("## Befunde & Messwerte")
        lines.append("")
        lines.extend(self._build_objective_section())

        # Diagnose
        lines.append("")
        lines.append("## Diagnose (Root Cause)")
        lines.append("")
        lines.append(self._get_root_cause())

        if self._state_machine and self._state_machine.repair_plan:
            lines.append("")
            lines.append("### Reparatur-Plan")
            lines.append("")
            lines.append(self._state_machine.repair_plan)

        # Massnahmen
        lines.append("")
        lines.append("## Durchgefuehrte Massnahmen")
        lines.append("")
        lines.extend(self._build_plan_section())

        # Ergebnis
        lines.append("")
        lines.append("## Ergebnis")
        lines.append("")
        state = self._get_workflow_state()
        if state == "completed":
            lines.append("Problem wurde erfolgreich behoben.")
        elif state in ("executing", "locked"):
            lines.append("Reparatur laeuft / teilweise durchgefuehrt.")
        elif state == "plan_ready":
            lines.append("Reparatur-Plan erstellt, Freigabe ausstehend.")
        else:
            lines.append("Diagnose-Phase (keine Reparatur durchgefuehrt).")

        # Audit Log
        if include_audit_log:
            changelog_entries = self._get_changelog_entries()
            if changelog_entries:
                lines.append("")
                lines.append("---")
                lines.append("")
                lines.append("## Audit Log")
                lines.append("")
                lines.append("| # | Zeitstempel | Aktion | Status |")
                lines.append("|---|-------------|--------|--------|")
                for i, entry in enumerate(changelog_entries, 1):
                    status = "OK" if entry.success else "FEHLER"
                    lines.append(
                        f"| {i} | {entry.timestamp[:19]} | {entry.tool_name} | {status} |"
                    )

        lines.append("")
        lines.append("---")
        lines.append("*Generiert von CE365 Agent*")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Shared section builders
    # ------------------------------------------------------------------

    def _build_objective_section(self) -> list:
        """Baut die Objective/Befunde Sektion aus Audit-Tool-Ergebnissen."""
        lines = []

        changelog_entries = self._get_changelog_entries()
        audit_entries = [e for e in changelog_entries if not self._is_repair_tool(e.tool_name)]

        if audit_entries:
            for entry in audit_entries:
                # Kurzzusammenfassung des Tool-Ergebnisses
                result_preview = entry.result[:200].replace("\n", " ")
                if len(entry.result) > 200:
                    result_preview += "..."
                lines.append(f"- **{entry.tool_name}**: {result_preview}")
        else:
            # Fallback: Session-Messages durchsuchen nach Tool Results
            if self._session:
                tool_count = 0
                for msg in self._session.messages:
                    content = msg.get("content")
                    if isinstance(content, list):
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "tool_result":
                                tool_count += 1
                if tool_count > 0:
                    lines.append(f"- {tool_count} Tool-Ausfuehrungen in dieser Session")
                else:
                    lines.append("- Keine automatisierten Messwerte erfasst")
            else:
                lines.append("- Keine automatisierten Messwerte erfasst")

        return lines

    def _build_plan_section(self) -> list:
        """Baut die Plan/Massnahmen Sektion aus Changelog-Entries."""
        lines = []

        changelog_entries = self._get_changelog_entries()
        repair_entries = [e for e in changelog_entries if self._is_repair_tool(e.tool_name)]

        if repair_entries:
            for i, entry in enumerate(repair_entries, 1):
                status = "Erfolgreich" if entry.success else "Fehlgeschlagen"
                lines.append(f"{i}. **{entry.tool_name}** — {status}")
                # Kurze Beschreibung der Eingabe
                if entry.tool_input:
                    params = ", ".join(
                        f"{k}={v}" for k, v in entry.tool_input.items() if v
                    )
                    if params:
                        lines.append(f"   Parameter: {params}")
        else:
            lines.append("Keine Repair-Aktionen durchgefuehrt.")

        # Geplante aber nicht ausgefuehrte Schritte
        if self._state_machine:
            approved = set(self._state_machine.approved_steps)
            executed = set(self._state_machine.executed_steps)
            pending = approved - executed
            if pending:
                lines.append("")
                lines.append(f"Ausstehende Schritte: {sorted(pending)}")

        return lines

    @staticmethod
    def _is_repair_tool(tool_name: str) -> bool:
        """Heuristik: ist ein Tool ein Repair-Tool basierend auf dem Namen."""
        repair_keywords = [
            "repair", "fix", "reset", "flush", "cleanup", "clean",
            "install", "disable", "enable", "restore", "trigger",
            "schedule", "service_manager", "sfc", "disk_cleanup",
        ]
        tool_lower = tool_name.lower()
        return any(kw in tool_lower for kw in repair_keywords)

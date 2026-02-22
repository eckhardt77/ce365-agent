"""
Tests fuer IncidentReportTool — Severity, Duration, Vorher/Nachher, Kunde/Ticket, Auto-Empfehlungen
"""

import pytest
from unittest.mock import MagicMock
from ce365.tools.audit.incident_report import IncidentReportTool
from ce365.storage.changelog import ChangelogEntry


def _make_entry(
    tool_name="test_tool",
    result="OK",
    success=True,
    duration_ms=0,
    snapshot_before="",
    snapshot_after="",
):
    return ChangelogEntry(
        timestamp="2026-02-22T14:00:00",
        tool_name=tool_name,
        tool_input={},
        result=result,
        success=success,
        duration_ms=duration_ms,
        snapshot_before=snapshot_before,
        snapshot_after=snapshot_after,
    )


@pytest.fixture
def mock_bot():
    bot = MagicMock()
    bot.problem_description = "PC ist langsam"
    bot.diagnosed_root_cause = "Festplatte 97% voll"
    bot.detected_os_type = "windows"
    bot.detected_os_version = "Windows 11"
    bot.error_codes = None
    bot.customer_name = None
    bot.ticket_id = None
    from datetime import datetime
    bot.session_start_time = datetime(2026, 2, 22, 14, 0, 0)
    return bot


@pytest.fixture
def mock_changelog():
    changelog = MagicMock()
    changelog.entries = []
    return changelog


@pytest.fixture
def report_tool(mock_bot, mock_changelog):
    return IncidentReportTool(
        session=None,
        changelog=mock_changelog,
        state_machine=None,
        bot=mock_bot,
    )


class TestSeverityClassification:
    """Tests fuer _classify_severity"""

    def test_critical_keywords(self):
        assert IncidentReportTool._classify_severity("Disk error: critical failure") == "KRITISCH"
        assert IncidentReportTool._classify_severity("Firewall deaktiviert") == "KRITISCH"
        assert IncidentReportTool._classify_severity("Disk 95% voll") == "KRITISCH"

    def test_warning_keywords(self):
        assert IncidentReportTool._classify_severity("7 Updates ausstehend") == "WARNUNG"
        assert IncidentReportTool._classify_severity("Software veraltet") == "WARNUNG"
        assert IncidentReportTool._classify_severity("DNS langsam") == "WARNUNG"

    def test_ok(self):
        assert IncidentReportTool._classify_severity("Alles in Ordnung") == "OK"
        assert IncidentReportTool._classify_severity("Firewall aktiv, SIP aktiv") == "OK"


class TestFormatDuration:
    """Tests fuer _format_duration"""

    def test_zero(self):
        assert IncidentReportTool._format_duration(0) == ""

    def test_milliseconds(self):
        assert IncidentReportTool._format_duration(500) == "500ms"

    def test_seconds(self):
        assert IncidentReportTool._format_duration(1500) == "1.5s"
        assert IncidentReportTool._format_duration(3200) == "3.2s"


class TestCustomerTicket:
    """Tests fuer Kunde/Ticket im Report"""

    @pytest.mark.asyncio
    async def test_soap_with_customer_ticket(self, report_tool, mock_bot):
        mock_bot.customer_name = "Mustermann GmbH"
        mock_bot.ticket_id = "INC-2026-0042"

        report = await report_tool.execute(format="soap")
        assert "Kunde:      Mustermann GmbH" in report
        assert "Ticket-ID:  INC-2026-0042" in report

    @pytest.mark.asyncio
    async def test_markdown_with_customer_ticket(self, report_tool, mock_bot):
        mock_bot.customer_name = "Mustermann GmbH"
        mock_bot.ticket_id = "INC-2026-0042"

        report = await report_tool.execute(format="markdown")
        assert "| **Kunde** | Mustermann GmbH |" in report
        assert "| **Ticket-ID** | `INC-2026-0042` |" in report

    @pytest.mark.asyncio
    async def test_soap_without_customer_ticket(self, report_tool):
        report = await report_tool.execute(format="soap")
        assert "Kunde:" not in report
        assert "Ticket-ID:" not in report

    @pytest.mark.asyncio
    async def test_override_customer_via_param(self, report_tool, mock_bot):
        mock_bot.customer_name = "Alt GmbH"
        report = await report_tool.execute(
            format="soap",
            customer_name="Neu GmbH",
        )
        assert "Kunde:      Neu GmbH" in report

    @pytest.mark.asyncio
    async def test_override_ticket_via_param(self, report_tool, mock_bot):
        report = await report_tool.execute(
            format="soap",
            ticket_id="TICKET-999",
        )
        assert "Ticket-ID:  TICKET-999" in report


class TestDurationInReport:
    """Tests fuer Duration-Anzeige im Report"""

    @pytest.mark.asyncio
    async def test_soap_audit_log_duration(self, report_tool, mock_changelog):
        mock_changelog.entries = [
            _make_entry("get_system_info", "System OK", duration_ms=1200),
        ]
        report = await report_tool.execute(format="soap", include_audit_log=True)
        assert "(1.2s)" in report

    @pytest.mark.asyncio
    async def test_markdown_audit_log_duration(self, report_tool, mock_changelog):
        mock_changelog.entries = [
            _make_entry("get_system_info", "System OK", duration_ms=500),
        ]
        report = await report_tool.execute(format="markdown", include_audit_log=True)
        assert "| Dauer |" in report
        assert "500ms" in report


class TestSeverityInReport:
    """Tests fuer Severity-Tags in Objective-Sektion"""

    @pytest.mark.asyncio
    async def test_soap_severity_tags(self, report_tool, mock_changelog):
        mock_changelog.entries = [
            _make_entry("check_disk_health", "Disk error: critical failure"),
            _make_entry("check_security", "Firewall aktiv, alles OK"),
            _make_entry("check_updates", "7 Updates ausstehend"),
        ]
        report = await report_tool.execute(format="soap")
        assert "[KRITISCH]" in report
        assert "[OK]" in report
        assert "[WARNUNG]" in report

    @pytest.mark.asyncio
    async def test_markdown_severity_table(self, report_tool, mock_changelog):
        mock_changelog.entries = [
            _make_entry("check_disk_health", "Disk error: critical"),
        ]
        report = await report_tool.execute(format="markdown")
        assert "| Severity |" in report
        assert "KRITISCH" in report


class TestSnapshotsInReport:
    """Tests fuer Vorher/Nachher im Plan-Sektion"""

    @pytest.mark.asyncio
    async def test_soap_snapshots(self, report_tool, mock_changelog):
        mock_changelog.entries = [
            _make_entry(
                "cleanup_disk",
                "45 GB freigeraeumt",
                duration_ms=3200,
                snapshot_before="Disk 97% belegt",
                snapshot_after="Disk 72% belegt",
            ),
        ]
        report = await report_tool.execute(format="soap")
        assert "Vorher: Disk 97% belegt" in report
        assert "Nachher: Disk 72% belegt" in report

    @pytest.mark.asyncio
    async def test_markdown_snapshots_table(self, report_tool, mock_changelog):
        mock_changelog.entries = [
            _make_entry(
                "cleanup_disk",
                "OK",
                duration_ms=3200,
                snapshot_before="Disk 97%",
                snapshot_after="Disk 72%",
            ),
        ]
        report = await report_tool.execute(format="markdown")
        assert "| Vorher | Nachher |" in report
        assert "Disk 97%" in report
        assert "Disk 72%" in report


class TestAutoRecommendations:
    """Tests fuer automatische Empfehlungen"""

    @pytest.mark.asyncio
    async def test_disk_full_recommendation(self, report_tool, mock_changelog):
        mock_changelog.entries = [
            _make_entry("get_system_info", "Disk 95% belegt, 5 GB frei"),
        ]
        report = await report_tool.execute(format="soap")
        assert "EMPFEHLUNGEN" in report
        assert "Disk-Bereinigung" in report

    @pytest.mark.asyncio
    async def test_updates_pending_recommendation(self, report_tool, mock_changelog):
        mock_changelog.entries = [
            _make_entry("check_system_updates", "7 Updates ausstehend"),
        ]
        report = await report_tool.execute(format="soap")
        assert "Update" in report

    @pytest.mark.asyncio
    async def test_security_disabled_recommendation(self, report_tool, mock_changelog):
        mock_changelog.entries = [
            _make_entry("check_security_status", "Firewall deaktiviert"),
        ]
        report = await report_tool.execute(format="soap")
        assert "Sicherheitsfeatures" in report

    @pytest.mark.asyncio
    async def test_disk_health_warning_recommendation(self, report_tool, mock_changelog):
        mock_changelog.entries = [
            _make_entry("check_disk_health", "SMART warning: Reallocated Sectors"),
        ]
        report = await report_tool.execute(format="soap")
        assert "Verschleiss" in report

    @pytest.mark.asyncio
    async def test_no_issues_recommendation(self, report_tool, mock_changelog):
        mock_changelog.entries = [
            _make_entry("get_system_info", "Alles in Ordnung"),
        ]
        report = await report_tool.execute(format="soap")
        assert "gutem Zustand" in report

    @pytest.mark.asyncio
    async def test_markdown_recommendations_section(self, report_tool, mock_changelog):
        mock_changelog.entries = [
            _make_entry("get_system_info", "Disk 95% belegt"),
        ]
        report = await report_tool.execute(format="markdown")
        assert "## Empfehlungen" in report

    @pytest.mark.asyncio
    async def test_backup_missing_recommendation(self, report_tool, mock_changelog):
        mock_changelog.entries = [
            _make_entry("check_backup_status", "Kein Backup konfiguriert"),
        ]
        report = await report_tool.execute(format="soap")
        assert "Backup-Strategie" in report

    @pytest.mark.asyncio
    async def test_deduplicate_recommendations(self, report_tool, mock_changelog):
        mock_changelog.entries = [
            _make_entry("get_system_info", "Disk 95% belegt"),
            _make_entry("cleanup_disk", "Disk 95% belegt, Cleanup noetig"),
        ]
        report = await report_tool.execute(format="soap")
        # Should only appear once despite two entries triggering it
        count = report.count("Disk-Bereinigung")
        assert count == 1

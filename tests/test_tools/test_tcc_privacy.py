"""
Tests fuer TCCPrivacyAuditTool

Testet:
- Tool-Metadaten (name, description, input_schema)
- Anthropic Tool Format
- TCC.db Parsing
- User/System TCC Checks
- Platform-Check (nur macOS)
"""

import pytest
from unittest.mock import patch, MagicMock
from ce365.tools.audit.tcc_privacy import TCCPrivacyAuditTool, TCC_SERVICES, AUTH_VALUES


class TestToolMetadata:
    """Tests fuer Tool-Metadaten und Schema"""

    def setup_method(self):
        self.tool = TCCPrivacyAuditTool()

    def test_name(self):
        assert self.tool.name == "audit_tcc_privacy"

    def test_description_not_empty(self):
        assert len(self.tool.description) > 50

    def test_description_mentions_tcc(self):
        assert "TCC" in self.tool.description

    def test_description_mentions_kamera(self):
        assert "Kamera" in self.tool.description

    def test_tool_type_is_audit(self):
        assert self.tool.tool_type == "audit"

    def test_input_schema_no_properties(self):
        schema = self.tool.input_schema
        assert schema["properties"] == {}

    def test_input_schema_no_required(self):
        schema = self.tool.input_schema
        assert schema["required"] == []

    def test_anthropic_tool_format(self):
        tool_def = self.tool.to_anthropic_tool()
        assert "name" in tool_def
        assert "description" in tool_def
        assert "input_schema" in tool_def
        assert tool_def["name"] == "audit_tcc_privacy"


class TestTCCConstants:
    """Tests fuer TCC-Konstanten"""

    def test_services_not_empty(self):
        assert len(TCC_SERVICES) > 0

    def test_critical_services_present(self):
        assert "kTCCServiceCamera" in TCC_SERVICES
        assert "kTCCServiceMicrophone" in TCC_SERVICES
        assert "kTCCServiceScreenCapture" in TCC_SERVICES
        assert "kTCCServiceAccessibility" in TCC_SERVICES
        assert "kTCCServiceSystemPolicyAllFiles" in TCC_SERVICES

    def test_auth_values_cover_common(self):
        assert 0 in AUTH_VALUES  # Verweigert
        assert 2 in AUTH_VALUES  # Erlaubt

    def test_auth_value_format(self):
        for key, (icon, label) in AUTH_VALUES.items():
            assert isinstance(icon, str)
            assert isinstance(label, str)


class TestTCCParsing:
    """Tests fuer TCC Output Parsing"""

    def setup_method(self):
        self.tool = TCCPrivacyAuditTool()

    def test_parse_valid_output(self):
        output = (
            "kTCCServiceCamera|com.zoom.us|2\n"
            "kTCCServiceMicrophone|com.zoom.us|2\n"
            "kTCCServiceScreenCapture|com.teamviewer.TeamViewer|0"
        )
        entries = self.tool._parse_tcc_output(output)
        assert len(entries) == 3
        assert entries[0] == ("kTCCServiceCamera", "com.zoom.us", 2)
        assert entries[2] == ("kTCCServiceScreenCapture", "com.teamviewer.TeamViewer", 0)

    def test_parse_empty_output(self):
        entries = self.tool._parse_tcc_output("")
        assert entries == []

    def test_parse_malformed_line(self):
        output = "kTCCServiceCamera|com.zoom.us"
        entries = self.tool._parse_tcc_output(output)
        assert entries == []

    def test_parse_invalid_auth_value(self):
        output = "kTCCServiceCamera|com.zoom.us|abc"
        entries = self.tool._parse_tcc_output(output)
        assert len(entries) == 1
        assert entries[0][2] == -1


class TestUserTCC:
    """Tests fuer User TCC.db"""

    def setup_method(self):
        self.tool = TCCPrivacyAuditTool()

    @patch("ce365.tools.audit.tcc_privacy.os.path.exists")
    def test_user_db_not_found(self, mock_exists):
        mock_exists.return_value = False
        lines = self.tool._check_user_tcc()
        assert any("nicht gefunden" in l for l in lines)

    @patch("ce365.tools.audit.tcc_privacy._run_cmd")
    @patch("ce365.tools.audit.tcc_privacy.os.path.exists")
    def test_user_db_with_entries(self, mock_exists, mock_cmd):
        mock_exists.return_value = True
        mock_cmd.return_value = "kTCCServiceCamera|com.zoom.us|2\nkTCCServiceMicrophone|com.slack.Slack|2"
        lines = self.tool._check_user_tcc()
        assert any("Kamera" in l for l in lines)
        assert any("zoom" in l.lower() or "Zoom" in l for l in lines)

    @patch("ce365.tools.audit.tcc_privacy._run_cmd")
    @patch("ce365.tools.audit.tcc_privacy.os.path.exists")
    def test_user_db_empty(self, mock_exists, mock_cmd):
        mock_exists.return_value = True
        mock_cmd.return_value = ""
        lines = self.tool._check_user_tcc()
        assert any("Keine Eintraege" in l or "verweigert" in l.lower() for l in lines)


class TestSystemTCC:
    """Tests fuer System TCC.db"""

    def setup_method(self):
        self.tool = TCCPrivacyAuditTool()

    @patch("ce365.tools.audit.tcc_privacy.os.path.exists")
    def test_system_db_not_found(self, mock_exists):
        mock_exists.return_value = False
        lines = self.tool._check_system_tcc()
        assert any("nicht gefunden" in l or "Root" in l for l in lines)


class TestPlatformCheck:
    """Tests fuer Platform-Erkennung"""

    @pytest.mark.asyncio
    @patch("ce365.tools.audit.tcc_privacy.platform")
    async def test_windows_not_supported(self, mock_platform):
        mock_platform.system.return_value = "Windows"
        tool = TCCPrivacyAuditTool()
        result = await tool.execute()
        assert "nur auf macOS" in result

    @pytest.mark.asyncio
    @patch("ce365.tools.audit.tcc_privacy.platform")
    @patch("ce365.tools.audit.tcc_privacy.os.path.exists")
    @patch("ce365.tools.audit.tcc_privacy._run_cmd")
    async def test_macos_runs(self, mock_cmd, mock_exists, mock_platform):
        mock_platform.system.return_value = "Darwin"
        mock_exists.return_value = False
        mock_cmd.return_value = ""
        tool = TCCPrivacyAuditTool()
        result = await tool.execute()
        assert "TCC PRIVACY AUDIT" in result

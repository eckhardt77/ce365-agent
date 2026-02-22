"""
Tests fuer SIPGatekeeperAuditTool

Testet:
- Tool-Metadaten (name, description, input_schema)
- Anthropic Tool Format
- SIP-Check mit Mock-Daten
- Gatekeeper-Check mit Mock-Daten
- XProtect/MRT-Check
- Notarization-Check
- Platform-Check (nur macOS)
"""

import pytest
from unittest.mock import patch, MagicMock
from ce365.tools.audit.sip_gatekeeper import SIPGatekeeperAuditTool


class TestToolMetadata:
    """Tests fuer Tool-Metadaten und Schema"""

    def setup_method(self):
        self.tool = SIPGatekeeperAuditTool()

    def test_name(self):
        assert self.tool.name == "audit_sip_gatekeeper"

    def test_description_not_empty(self):
        assert len(self.tool.description) > 50

    def test_description_mentions_sip(self):
        assert "SIP" in self.tool.description

    def test_description_mentions_gatekeeper(self):
        assert "Gatekeeper" in self.tool.description

    def test_tool_type_is_audit(self):
        assert self.tool.tool_type == "audit"

    def test_input_schema_has_check_apps(self):
        schema = self.tool.input_schema
        assert "check_apps" in schema["properties"]
        assert schema["properties"]["check_apps"]["type"] == "boolean"

    def test_input_schema_no_required(self):
        schema = self.tool.input_schema
        assert schema["required"] == []

    def test_anthropic_tool_format(self):
        tool_def = self.tool.to_anthropic_tool()
        assert "name" in tool_def
        assert "description" in tool_def
        assert "input_schema" in tool_def
        assert tool_def["name"] == "audit_sip_gatekeeper"


class TestSIPCheck:
    """Tests fuer SIP-Pruefung"""

    def setup_method(self):
        self.tool = SIPGatekeeperAuditTool()

    @patch("ce365.tools.audit.sip_gatekeeper._run_cmd")
    def test_sip_enabled(self, mock_cmd):
        mock_cmd.return_value = "System Integrity Protection status: enabled."
        lines = self.tool._check_sip()
        assert any("AKTIVIERT" in l for l in lines)

    @patch("ce365.tools.audit.sip_gatekeeper._run_cmd")
    def test_sip_disabled(self, mock_cmd):
        mock_cmd.side_effect = [
            "System Integrity Protection status: disabled.",
            "",
        ]
        lines = self.tool._check_sip()
        assert any("DEAKTIVIERT" in l for l in lines)

    @patch("ce365.tools.audit.sip_gatekeeper._run_cmd")
    def test_sip_authenticated_root_enabled(self, mock_cmd):
        mock_cmd.side_effect = [
            "System Integrity Protection status: enabled.",
            "Authenticated Root status: enabled",
        ]
        lines = self.tool._check_sip()
        assert any("Authenticated Root" in l and "AKTIVIERT" in l for l in lines)

    @patch("ce365.tools.audit.sip_gatekeeper._run_cmd")
    def test_sip_empty_output(self, mock_cmd):
        mock_cmd.side_effect = ["", ""]
        lines = self.tool._check_sip()
        assert any("nicht ermittelt" in l for l in lines)


class TestGatekeeperCheck:
    """Tests fuer Gatekeeper-Pruefung"""

    def setup_method(self):
        self.tool = SIPGatekeeperAuditTool()

    @patch("ce365.tools.audit.sip_gatekeeper._run_cmd")
    def test_gatekeeper_enabled(self, mock_cmd):
        mock_cmd.return_value = "assessments enabled"
        lines = self.tool._check_gatekeeper()
        assert any("AKTIVIERT" in l for l in lines)

    @patch("ce365.tools.audit.sip_gatekeeper._run_cmd")
    def test_gatekeeper_disabled(self, mock_cmd):
        mock_cmd.side_effect = ["assessments disabled", ""]
        lines = self.tool._check_gatekeeper()
        assert any("DEAKTIVIERT" in l for l in lines)

    @patch("ce365.tools.audit.sip_gatekeeper._run_cmd")
    def test_auto_rearm_enabled(self, mock_cmd):
        mock_cmd.side_effect = ["assessments enabled", "1"]
        lines = self.tool._check_gatekeeper()
        assert any("Auto-Rearm" in l and "AKTIVIERT" in l for l in lines)

    @patch("ce365.tools.audit.sip_gatekeeper._run_cmd")
    def test_auto_rearm_disabled(self, mock_cmd):
        mock_cmd.side_effect = ["assessments enabled", "0"]
        lines = self.tool._check_gatekeeper()
        assert any("Auto-Rearm" in l and "DEAKTIVIERT" in l for l in lines)


class TestXProtectMRT:
    """Tests fuer XProtect und MRT"""

    def setup_method(self):
        self.tool = SIPGatekeeperAuditTool()

    @patch("ce365.tools.audit.sip_gatekeeper._run_cmd")
    def test_xprotect_found(self, mock_cmd):
        mock_cmd.return_value = (
            "  Install Date: 2026-01-15\n"
            "  XProtect PlistConfigData:\n"
            "    Version: 5678\n"
        )
        lines = self.tool._check_xprotect_mrt()
        assert any("XProtect" in l for l in lines)

    @patch("ce365.tools.audit.sip_gatekeeper._run_cmd")
    def test_xprotect_empty(self, mock_cmd):
        mock_cmd.return_value = ""
        lines = self.tool._check_xprotect_mrt()
        assert any("nicht verfuegbar" in l.lower() for l in lines)

    @patch("ce365.tools.audit.sip_gatekeeper._run_cmd")
    def test_mrt_found(self, mock_cmd):
        mock_cmd.return_value = (
            "  MRT Malware Removal Tool:\n"
            "    Version: 1.98\n"
        )
        lines = self.tool._check_xprotect_mrt()
        assert any("MRT" in l for l in lines)


class TestNotarization:
    """Tests fuer Notarization-Check"""

    def setup_method(self):
        self.tool = SIPGatekeeperAuditTool()

    @patch("ce365.tools.audit.sip_gatekeeper.os.listdir")
    @patch("ce365.tools.audit.sip_gatekeeper.os.path.isdir")
    @patch("ce365.tools.audit.sip_gatekeeper._run_cmd")
    def test_notarized_app(self, mock_cmd, mock_isdir, mock_listdir):
        mock_isdir.return_value = True
        mock_listdir.return_value = ["Safari.app", "Mail.app"]
        mock_cmd.return_value = "accepted\nsource=Notarized Developer ID"
        lines = self.tool._check_notarization()
        assert any("Notarisiert" in l for l in lines)

    @patch("ce365.tools.audit.sip_gatekeeper.os.listdir")
    @patch("ce365.tools.audit.sip_gatekeeper.os.path.isdir")
    @patch("ce365.tools.audit.sip_gatekeeper._run_cmd")
    def test_rejected_app(self, mock_cmd, mock_isdir, mock_listdir):
        mock_isdir.return_value = True
        mock_listdir.return_value = ["Sketchy.app"]
        mock_cmd.return_value = "rejected"
        lines = self.tool._check_notarization()
        assert any("Abgelehnt" in l for l in lines)

    @patch("ce365.tools.audit.sip_gatekeeper.os.path.isdir")
    def test_no_applications_dir(self, mock_isdir):
        mock_isdir.return_value = False
        lines = self.tool._check_notarization()
        assert any("nicht gefunden" in l for l in lines)


class TestPlatformCheck:
    """Tests fuer Platform-Erkennung"""

    @pytest.mark.asyncio
    @patch("ce365.tools.audit.sip_gatekeeper.platform")
    async def test_windows_not_supported(self, mock_platform):
        mock_platform.system.return_value = "Windows"
        tool = SIPGatekeeperAuditTool()
        result = await tool.execute()
        assert "nur auf macOS" in result

    @pytest.mark.asyncio
    @patch("ce365.tools.audit.sip_gatekeeper.platform")
    async def test_linux_not_supported(self, mock_platform):
        mock_platform.system.return_value = "Linux"
        tool = SIPGatekeeperAuditTool()
        result = await tool.execute()
        assert "nur auf macOS" in result

    @pytest.mark.asyncio
    @patch("ce365.tools.audit.sip_gatekeeper.platform")
    @patch("ce365.tools.audit.sip_gatekeeper._run_cmd")
    async def test_macos_runs(self, mock_cmd, mock_platform):
        mock_platform.system.return_value = "Darwin"
        mock_cmd.return_value = ""
        tool = SIPGatekeeperAuditTool()
        result = await tool.execute(check_apps=False)
        assert "SIP & GATEKEEPER" in result

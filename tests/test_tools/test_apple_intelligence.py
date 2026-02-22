"""
Tests fuer AppleIntelligenceAuditTool

Testet:
- Tool-Metadaten (name, description, input_schema)
- Anthropic Tool Format
- Apple Intelligence Verfuegbarkeits-Check
- Siri-Status Check
- Shortcuts-Auflistung
- Automator-Workflows
- Platform-Check (nur macOS)
"""

import pytest
from unittest.mock import patch
from ce365.tools.audit.apple_intelligence import AppleIntelligenceAuditTool


class TestToolMetadata:
    """Tests fuer Tool-Metadaten und Schema"""

    def setup_method(self):
        self.tool = AppleIntelligenceAuditTool()

    def test_name(self):
        assert self.tool.name == "audit_apple_intelligence"

    def test_description_not_empty(self):
        assert len(self.tool.description) > 50

    def test_description_mentions_apple_intelligence(self):
        assert "Apple Intelligence" in self.tool.description

    def test_description_mentions_shortcuts(self):
        assert "Shortcuts" in self.tool.description or "Kurzbefehle" in self.tool.description

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
        assert tool_def["name"] == "audit_apple_intelligence"


class TestAppleIntelligenceCheck:
    """Tests fuer Apple Intelligence Verfuegbarkeit"""

    def setup_method(self):
        self.tool = AppleIntelligenceAuditTool()

    @patch("ce365.tools.audit.apple_intelligence._run_cmd")
    def test_apple_silicon_detected(self, mock_cmd):
        mock_cmd.side_effect = [
            "Apple M2 Pro",
            "15.2",
            "1",
        ]
        lines = self.tool._check_apple_intelligence()
        assert any("Apple Silicon" in l or "kompatibel" in l for l in lines)

    @patch("ce365.tools.audit.apple_intelligence._run_cmd")
    def test_intel_mac_detected(self, mock_cmd):
        mock_cmd.side_effect = [
            "Intel(R) Core(TM) i9-9980HK",
            "14.7",
            "",
        ]
        lines = self.tool._check_apple_intelligence()
        assert any("Intel" in l or "Nicht verfuegbar" in l for l in lines)

    @patch("ce365.tools.audit.apple_intelligence._run_cmd")
    def test_macos_too_old(self, mock_cmd):
        mock_cmd.side_effect = [
            "Apple M1",
            "14.7",
            "",
        ]
        lines = self.tool._check_apple_intelligence()
        assert any("macOS < 15" in l or "Nicht verfuegbar" in l for l in lines)

    @patch("ce365.tools.audit.apple_intelligence._run_cmd")
    def test_assistant_enabled(self, mock_cmd):
        mock_cmd.side_effect = [
            "Apple M2",
            "15.2",
            "1",
        ]
        lines = self.tool._check_apple_intelligence()
        assert any("Aktiviert" in l for l in lines)

    @patch("ce365.tools.audit.apple_intelligence._run_cmd")
    def test_assistant_disabled(self, mock_cmd):
        mock_cmd.side_effect = [
            "Apple M2",
            "15.2",
            "0",
        ]
        lines = self.tool._check_apple_intelligence()
        assert any("Deaktiviert" in l for l in lines)


class TestSiriCheck:
    """Tests fuer Siri-Status"""

    def setup_method(self):
        self.tool = AppleIntelligenceAuditTool()

    @patch("ce365.tools.audit.apple_intelligence._run_cmd")
    def test_siri_menu_visible(self, mock_cmd):
        mock_cmd.return_value = '{\n    StatusMenuVisible = 1;\n    VoiceTriggerEnabled = 0;\n}'
        lines = self.tool._check_siri()
        assert any("Menueleiste" in l and "Sichtbar" in l for l in lines)

    @patch("ce365.tools.audit.apple_intelligence._run_cmd")
    def test_hey_siri_enabled(self, mock_cmd):
        mock_cmd.return_value = '{\n    VoiceTriggerEnabled = 1;\n}'
        lines = self.tool._check_siri()
        assert any("Hey Siri" in l and "Aktiviert" in l for l in lines)

    @patch("ce365.tools.audit.apple_intelligence._run_cmd")
    def test_siri_empty(self, mock_cmd):
        mock_cmd.return_value = ""
        lines = self.tool._check_siri()
        assert any("nicht lesbar" in l or "nicht ermittelbar" in l for l in lines)


class TestShortcuts:
    """Tests fuer Shortcuts-Auflistung"""

    def setup_method(self):
        self.tool = AppleIntelligenceAuditTool()

    @patch("ce365.tools.audit.apple_intelligence._run_cmd")
    def test_shortcuts_found(self, mock_cmd):
        mock_cmd.return_value = "Morning Routine\nBackup Files\nSend Report"
        lines = self.tool._check_shortcuts()
        assert any("3" in l for l in lines)
        assert any("Morning Routine" in l for l in lines)

    @patch("ce365.tools.audit.apple_intelligence._run_cmd")
    def test_shortcuts_empty(self, mock_cmd):
        mock_cmd.return_value = ""
        lines = self.tool._check_shortcuts()
        assert any("Keine Kurzbefehle" in l for l in lines)

    @patch("ce365.tools.audit.apple_intelligence._run_cmd")
    def test_many_shortcuts_truncated(self, mock_cmd):
        shortcuts = "\n".join([f"Shortcut {i}" for i in range(30)])
        mock_cmd.return_value = shortcuts
        lines = self.tool._check_shortcuts()
        assert any("30" in l for l in lines)
        assert any("weitere" in l for l in lines)


class TestAutomator:
    """Tests fuer Automator-Workflows"""

    def setup_method(self):
        self.tool = AppleIntelligenceAuditTool()

    @patch("ce365.tools.audit.apple_intelligence.os.listdir")
    @patch("ce365.tools.audit.apple_intelligence.os.path.isdir")
    def test_workflows_found(self, mock_isdir, mock_listdir):
        mock_isdir.side_effect = [True, False, False]
        mock_listdir.return_value = ["Convert PDF.workflow", "Resize Images.workflow", "notes.txt"]
        lines = self.tool._check_automator()
        assert any("Convert PDF" in l for l in lines)
        assert any("Resize Images" in l for l in lines)
        assert any("2" in l for l in lines)

    @patch("ce365.tools.audit.apple_intelligence.os.path.isdir")
    def test_no_workflows(self, mock_isdir):
        mock_isdir.return_value = False
        lines = self.tool._check_automator()
        assert any("Keine Automator" in l for l in lines)


class TestPlatformCheck:
    """Tests fuer Platform-Erkennung"""

    @pytest.mark.asyncio
    @patch("ce365.tools.audit.apple_intelligence.platform")
    async def test_windows_not_supported(self, mock_platform):
        mock_platform.system.return_value = "Windows"
        tool = AppleIntelligenceAuditTool()
        result = await tool.execute()
        assert "nur auf macOS" in result

    @pytest.mark.asyncio
    @patch("ce365.tools.audit.apple_intelligence.platform")
    @patch("ce365.tools.audit.apple_intelligence._run_cmd")
    @patch("ce365.tools.audit.apple_intelligence.os.path.isdir")
    async def test_macos_runs(self, mock_isdir, mock_cmd, mock_platform):
        mock_platform.system.return_value = "Darwin"
        mock_cmd.return_value = ""
        mock_isdir.return_value = False
        tool = AppleIntelligenceAuditTool()
        result = await tool.execute()
        assert "APPLE INTELLIGENCE" in result

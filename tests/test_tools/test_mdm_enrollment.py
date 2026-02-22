"""
Tests fuer MDMEnrollmentAuditTool

Testet:
- Tool-Metadaten (name, description, input_schema)
- Anthropic Tool Format
- Enrollment-Status Check
- DEP-Status Check
- Profil-Auflistung
- Platform-Check (macOS + Windows-Hinweis)
"""

import pytest
from unittest.mock import patch
from ce365.tools.audit.mdm_enrollment import MDMEnrollmentAuditTool


class TestToolMetadata:
    """Tests fuer Tool-Metadaten und Schema"""

    def setup_method(self):
        self.tool = MDMEnrollmentAuditTool()

    def test_name(self):
        assert self.tool.name == "audit_mdm_enrollment"

    def test_description_not_empty(self):
        assert len(self.tool.description) > 50

    def test_description_mentions_mdm(self):
        assert "MDM" in self.tool.description

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
        assert tool_def["name"] == "audit_mdm_enrollment"


class TestEnrollmentStatus:
    """Tests fuer Enrollment-Status"""

    def setup_method(self):
        self.tool = MDMEnrollmentAuditTool()

    @patch("ce365.tools.audit.mdm_enrollment._run_cmd")
    def test_enrolled_yes(self, mock_cmd):
        mock_cmd.return_value = "MDM enrollment: Yes (User Approved)\nMDM server: https://mdm.example.com"
        lines = self.tool._check_enrollment_status()
        assert any("✅" in l for l in lines)

    @patch("ce365.tools.audit.mdm_enrollment._run_cmd")
    def test_enrolled_no(self, mock_cmd):
        mock_cmd.return_value = "MDM enrollment: No"
        lines = self.tool._check_enrollment_status()
        assert any("ℹ️" in l for l in lines)

    @patch("ce365.tools.audit.mdm_enrollment._run_cmd")
    def test_enrollment_empty(self, mock_cmd):
        mock_cmd.return_value = ""
        lines = self.tool._check_enrollment_status()
        assert any("Kein MDM" in l for l in lines)

    @patch("ce365.tools.audit.mdm_enrollment._run_cmd")
    def test_enrollment_with_server(self, mock_cmd):
        mock_cmd.return_value = "MDM server URL: https://mdm.example.com\nEnrolled: Yes"
        lines = self.tool._check_enrollment_status()
        assert any("🔗" in l for l in lines)


class TestDEPStatus:
    """Tests fuer DEP/Automated Device Enrollment"""

    def setup_method(self):
        self.tool = MDMEnrollmentAuditTool()

    @patch("ce365.tools.audit.mdm_enrollment._run_cmd")
    def test_dep_enrolled(self, mock_cmd):
        mock_cmd.return_value = "DEP enrollment: active\nAutomated Device Enrollment: Yes"
        lines = self.tool._check_dep_status()
        assert any("DEP-enrolled" in l for l in lines)

    @patch("ce365.tools.audit.mdm_enrollment._run_cmd")
    def test_dep_not_enrolled(self, mock_cmd):
        mock_cmd.return_value = ""
        lines = self.tool._check_dep_status()
        assert any("Keine Enrollment" in l or "Kein DEP" in l for l in lines)


class TestProfiles:
    """Tests fuer Profil-Auflistung"""

    def setup_method(self):
        self.tool = MDMEnrollmentAuditTool()

    @patch("ce365.tools.audit.mdm_enrollment._run_cmd")
    def test_profiles_found(self, mock_cmd):
        mock_cmd.return_value = "ProfileIdentifier: com.example.wifi\nDisplayName: WiFi Config"
        lines = self.tool._list_profiles()
        assert any("com.example" in l.lower() or "wifi" in l.lower() for l in lines)

    @patch("ce365.tools.audit.mdm_enrollment._run_cmd")
    def test_profiles_empty(self, mock_cmd):
        mock_cmd.return_value = ""
        lines = self.tool._list_profiles()
        assert any("Keine Konfigurationsprofile" in l for l in lines)


class TestProfileDetails:
    """Tests fuer Profil-Details"""

    def setup_method(self):
        self.tool = MDMEnrollmentAuditTool()

    @patch("ce365.tools.audit.mdm_enrollment._run_cmd")
    def test_profile_with_certificate(self, mock_cmd):
        mock_cmd.return_value = "Certificate: Apple Root CA\nExpiration: 2027-01-01"
        lines = self.tool._check_profile_details()
        assert any("🔑" in l for l in lines)
        assert any("⏰" in l for l in lines)

    @patch("ce365.tools.audit.mdm_enrollment._run_cmd")
    def test_profile_details_empty(self, mock_cmd):
        mock_cmd.return_value = ""
        lines = self.tool._check_profile_details()
        assert any("Keine Konfigurationsprofile" in l for l in lines)


class TestPlatformCheck:
    """Tests fuer Platform-Erkennung"""

    @pytest.mark.asyncio
    @patch("ce365.tools.audit.mdm_enrollment.platform")
    async def test_windows_shows_hint(self, mock_platform):
        mock_platform.system.return_value = "Windows"
        tool = MDMEnrollmentAuditTool()
        result = await tool.execute()
        assert "Intune" in result or "dsregcmd" in result

    @pytest.mark.asyncio
    @patch("ce365.tools.audit.mdm_enrollment.platform")
    async def test_linux_not_supported(self, mock_platform):
        mock_platform.system.return_value = "Linux"
        tool = MDMEnrollmentAuditTool()
        result = await tool.execute()
        assert "nur auf macOS" in result

    @pytest.mark.asyncio
    @patch("ce365.tools.audit.mdm_enrollment.platform")
    @patch("ce365.tools.audit.mdm_enrollment._run_cmd")
    async def test_macos_runs(self, mock_cmd, mock_platform):
        mock_platform.system.return_value = "Darwin"
        mock_cmd.return_value = ""
        tool = MDMEnrollmentAuditTool()
        result = await tool.execute()
        assert "MDM & ENROLLMENT" in result

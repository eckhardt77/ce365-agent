"""
Tests fuer AnalyzeMemoryDumpsTool

Testet:
- Tool-Metadaten (name, description, input_schema)
- Anthropic Tool Format
- Windows-Analyse mit Mock-Daten
- macOS-Analyse mit Mock-Daten
- Bugcheck-Datenbank
- Crash-Frequenz-Bewertung
- Empfehlungs-Logik
"""

import pytest
from unittest.mock import patch, MagicMock
from ce365.tools.audit.memory_dump import AnalyzeMemoryDumpsTool, BUGCHECK_DB


class TestToolMetadata:
    """Tests fuer Tool-Metadaten und Schema"""

    def setup_method(self):
        self.tool = AnalyzeMemoryDumpsTool()

    def test_name(self):
        assert self.tool.name == "analyze_memory_dumps"

    def test_description_not_empty(self):
        assert len(self.tool.description) > 50

    def test_description_mentions_bsod(self):
        assert "BSOD" in self.tool.description or "Blue Screen" in self.tool.description

    def test_tool_type_is_audit(self):
        assert self.tool.tool_type == "audit"

    def test_input_schema_has_max_dumps(self):
        schema = self.tool.input_schema
        assert "max_dumps" in schema["properties"]
        assert schema["properties"]["max_dumps"]["type"] == "integer"

    def test_input_schema_no_required(self):
        schema = self.tool.input_schema
        assert schema["required"] == []

    def test_anthropic_tool_format(self):
        tool_def = self.tool.to_anthropic_tool()
        assert "name" in tool_def
        assert "description" in tool_def
        assert "input_schema" in tool_def
        assert tool_def["name"] == "analyze_memory_dumps"


class TestBugcheckDatabase:
    """Tests fuer die Bugcheck-Code-Datenbank"""

    def test_db_not_empty(self):
        assert len(BUGCHECK_DB) > 0

    def test_common_codes_present(self):
        expected = [
            "0x0000000A",  # IRQL_NOT_LESS_OR_EQUAL
            "0x00000050",  # PAGE_FAULT_IN_NONPAGED_AREA
            "0x000000EF",  # CRITICAL_PROCESS_DIED
            "0x00000124",  # WHEA_UNCORRECTABLE_ERROR
        ]
        for code in expected:
            assert code in BUGCHECK_DB, f"Code {code} fehlt in BUGCHECK_DB"

    def test_entry_has_required_fields(self):
        for code, entry in BUGCHECK_DB.items():
            assert "name" in entry, f"Code {code}: 'name' fehlt"
            assert "cause" in entry, f"Code {code}: 'cause' fehlt"
            assert "action" in entry, f"Code {code}: 'action' fehlt"

    def test_codes_are_hex_format(self):
        for code in BUGCHECK_DB:
            assert code.startswith("0x"), f"Code {code} hat kein 0x Prefix"
            assert len(code) == 10, f"Code {code} hat nicht 10 Zeichen"

    def test_irql_not_less_or_equal(self):
        entry = BUGCHECK_DB["0x0000000A"]
        assert entry["name"] == "IRQL_NOT_LESS_OR_EQUAL"
        assert "Treiber" in entry["cause"]

    def test_whea_uncorrectable(self):
        entry = BUGCHECK_DB["0x00000124"]
        assert entry["name"] == "WHEA_UNCORRECTABLE_ERROR"
        assert "Hardware" in entry["cause"]

    def test_critical_process_died(self):
        entry = BUGCHECK_DB["0x000000EF"]
        assert entry["name"] == "CRITICAL_PROCESS_DIED"
        assert "SFC" in entry["action"]


class TestWindowsAnalysis:
    """Tests fuer Windows-spezifische Analyse (mit Mocks)"""

    def setup_method(self):
        self.tool = AnalyzeMemoryDumpsTool()

    @pytest.mark.asyncio
    @patch("ce365.tools.audit.memory_dump.platform")
    @patch("ce365.tools.audit.memory_dump._run_cmd")
    async def test_windows_dispatch(self, mock_cmd, mock_platform):
        mock_platform.system.return_value = "Windows"
        mock_cmd.return_value = ""
        result = await self.tool.execute(max_dumps=3)
        assert "MEMORY DUMP ANALYSE" in result

    @patch("ce365.tools.audit.memory_dump._run_cmd")
    def test_list_minidumps_with_files(self, mock_cmd):
        mock_cmd.return_value = (
            "C:\\Windows\\Minidump\\012226-12345-01.dmp|2026-01-22 14:32|256\n"
            "C:\\Windows\\Minidump\\011926-67890-01.dmp|2026-01-19 09:15|256"
        )
        lines = self.tool._list_minidumps(5)
        assert any("012226-12345-01.dmp" in l for l in lines)
        assert any("256 KB" in l for l in lines)

    @patch("ce365.tools.audit.memory_dump._run_cmd")
    def test_list_minidumps_empty(self, mock_cmd):
        mock_cmd.return_value = ""
        lines = self.tool._list_minidumps(5)
        assert any("Keine Minidump" in l for l in lines)

    @patch("ce365.tools.audit.memory_dump._run_cmd")
    def test_check_full_dump_exists(self, mock_cmd):
        mock_cmd.return_value = "EXISTS|2026-01-22 14:32|1.2"
        lines = self.tool._check_full_dump()
        assert any("MEMORY.DMP" in l for l in lines)
        assert any("1.2 GB" in l for l in lines)

    @patch("ce365.tools.audit.memory_dump._run_cmd")
    def test_check_full_dump_missing(self, mock_cmd):
        mock_cmd.return_value = "NONE"
        lines = self.tool._check_full_dump()
        assert any("Nicht vorhanden" in l for l in lines)

    @patch("ce365.tools.audit.memory_dump._run_cmd")
    def test_analyze_bugchecks_known_code(self, mock_cmd):
        mock_cmd.return_value = "2026-01-22 14:32|0x0000000A|Some error message"
        lines = self.tool._analyze_bugchecks(5)
        assert any("IRQL_NOT_LESS_OR_EQUAL" in l for l in lines)
        assert any("Treiber" in l for l in lines)

    @patch("ce365.tools.audit.memory_dump._run_cmd")
    def test_analyze_bugchecks_unknown_code(self, mock_cmd):
        mock_cmd.return_value = "2026-01-22 14:32|0x0000BEEF|Unknown error"
        lines = self.tool._analyze_bugchecks(5)
        assert any("0x0000BEEF" in l for l in lines)
        assert any("WinDbg" in l for l in lines)

    @patch("ce365.tools.audit.memory_dump._run_cmd")
    def test_analyze_bugchecks_empty(self, mock_cmd):
        mock_cmd.return_value = ""
        lines = self.tool._analyze_bugchecks(5)
        assert any("Keine BugCheck" in l for l in lines)

    @patch("ce365.tools.audit.memory_dump._run_cmd")
    def test_crash_frequency_critical(self, mock_cmd):
        mock_cmd.return_value = "5|8|12"
        lines = self.tool._crash_frequency()
        assert any("5 Crashes" in l for l in lines)
        assert any("Kritisch" in l for l in lines)

    @patch("ce365.tools.audit.memory_dump._run_cmd")
    def test_crash_frequency_elevated(self, mock_cmd):
        mock_cmd.return_value = "1|6|10"
        lines = self.tool._crash_frequency()
        assert any("Erhoehte" in l for l in lines)

    @patch("ce365.tools.audit.memory_dump._run_cmd")
    def test_crash_frequency_none(self, mock_cmd):
        mock_cmd.return_value = "0|0|0"
        lines = self.tool._crash_frequency()
        assert any("Keine Crashes" in l for l in lines)

    @patch("ce365.tools.audit.memory_dump._run_cmd")
    def test_kernel_power_events(self, mock_cmd):
        mock_cmd.return_value = "2026-01-22 14:32|Unexpected restart"
        lines = self.tool._kernel_power_events(5)
        assert any("Event 41" in l for l in lines)

    @patch("ce365.tools.audit.memory_dump._run_cmd")
    def test_kernel_power_empty(self, mock_cmd):
        mock_cmd.return_value = ""
        lines = self.tool._kernel_power_events(5)
        assert any("Keine Kernel-Power" in l for l in lines)

    @patch("ce365.tools.audit.memory_dump._run_cmd")
    def test_dump_config_minidump(self, mock_cmd):
        mock_cmd.return_value = "3|%SystemRoot%\\Minidump|%SystemRoot%\\MEMORY.DMP"
        lines = self.tool._dump_configuration()
        assert any("Small Memory Dump" in l for l in lines)

    @patch("ce365.tools.audit.memory_dump._run_cmd")
    def test_dump_config_disabled_warning(self, mock_cmd):
        mock_cmd.return_value = "0||"
        lines = self.tool._dump_configuration()
        assert any("DEAKTIVIERT" in l for l in lines)

    def test_recommendations_driver_codes(self):
        self.tool._found_codes = ["0x0000000A", "0x000000D1"]
        lines = self.tool._generate_recommendations()
        assert any("Treiber" in l for l in lines)

    def test_recommendations_hardware_codes(self):
        self.tool._found_codes = ["0x00000124"]
        lines = self.tool._generate_recommendations()
        assert any("RAM-Test" in l or "memtest" in l for l in lines)

    def test_recommendations_integrity_codes(self):
        self.tool._found_codes = ["0x000000EF"]
        lines = self.tool._generate_recommendations()
        assert any("SFC" in l for l in lines)

    def test_recommendations_no_crashes(self):
        self.tool._found_codes = []
        lines = self.tool._generate_recommendations()
        assert any("stabil" in l for l in lines)

    def test_recommendations_many_crashes(self):
        self.tool._found_codes = ["0x0000000A", "0x00000050", "0x000000EF"]
        lines = self.tool._generate_recommendations()
        assert any("Systemwiederherstellung" in l for l in lines)


class TestMacOSAnalysis:
    """Tests fuer macOS-spezifische Analyse (mit Mocks)"""

    def setup_method(self):
        self.tool = AnalyzeMemoryDumpsTool()

    @pytest.mark.asyncio
    @patch("ce365.tools.audit.memory_dump.platform")
    @patch("ce365.tools.audit.memory_dump._run_cmd")
    async def test_macos_dispatch(self, mock_cmd, mock_platform):
        mock_platform.system.return_value = "Darwin"
        mock_cmd.return_value = ""
        result = await self.tool.execute(max_dumps=3)
        assert "macOS" in result

    @patch("ce365.tools.audit.memory_dump._run_cmd")
    def test_list_panic_reports_found(self, mock_cmd):
        mock_cmd.return_value = (
            "-rw-r--r--  1 root  wheel  12345 Jan 22 14:32 panic-2026-01-22.ips\n"
            "-rw-r--r--  1 root  wheel  11234 Jan 19 09:15 panic-2026-01-19.ips"
        )
        lines = self.tool._list_panic_reports(5)
        assert any("panic" in l for l in lines)

    @patch("ce365.tools.audit.memory_dump._run_cmd")
    def test_list_panic_reports_empty(self, mock_cmd):
        mock_cmd.return_value = ""
        lines = self.tool._list_panic_reports(5)
        assert any("Keine Panic" in l for l in lines)

    @patch("ce365.tools.audit.memory_dump._run_cmd")
    def test_shutdown_cause_power_failure(self, mock_cmd):
        mock_cmd.return_value = "2026-01-22 14:32:00 Previous shutdown cause: 0"
        lines = self.tool._check_shutdown_cause()
        assert any("Power-Fehler" in l or "Stromausfall" in l for l in lines)

    @patch("ce365.tools.audit.memory_dump._run_cmd")
    def test_shutdown_cause_empty(self, mock_cmd):
        mock_cmd.return_value = ""
        lines = self.tool._check_shutdown_cause()
        assert any("Keine Shutdown" in l for l in lines)


class TestUnsupportedOS:
    """Test fuer nicht unterstuetztes Betriebssystem"""

    @pytest.mark.asyncio
    @patch("ce365.tools.audit.memory_dump.platform")
    async def test_linux_not_supported(self, mock_platform):
        mock_platform.system.return_value = "Linux"
        tool = AnalyzeMemoryDumpsTool()
        result = await tool.execute()
        assert "Nicht unterstuetzt" in result


class TestDefaultParameters:
    """Tests fuer Default-Parameter"""

    def setup_method(self):
        self.tool = AnalyzeMemoryDumpsTool()

    @pytest.mark.asyncio
    @patch("ce365.tools.audit.memory_dump.platform")
    @patch("ce365.tools.audit.memory_dump._run_cmd")
    async def test_default_max_dumps(self, mock_cmd, mock_platform):
        mock_platform.system.return_value = "Windows"
        mock_cmd.return_value = ""
        # Sollte nicht crashen ohne Parameter
        result = await self.tool.execute()
        assert "MEMORY DUMP ANALYSE" in result

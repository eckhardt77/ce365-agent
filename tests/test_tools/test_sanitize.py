"""
Tests für Input Sanitization

Testet Schutz gegen Command Injection in PowerShell, AppleScript, Paths.
"""

import pytest
from techcare.tools.sanitize import (
    sanitize_powershell_string,
    sanitize_applescript_string,
    validate_program_name,
    validate_file_path,
    validate_description,
    validate_integer,
)


class TestPowerShellSanitization:
    """Tests für PowerShell String Sanitization"""

    def test_normal_string(self):
        assert sanitize_powershell_string("hello world") == "hello world"

    def test_single_quote_escape(self):
        assert sanitize_powershell_string("it's a test") == "it''s a test"

    def test_multiple_quotes(self):
        assert sanitize_powershell_string("a'b'c") == "a''b''c"

    def test_empty_string(self):
        assert sanitize_powershell_string("") == ""

    def test_injection_attempt(self):
        # PowerShell injection: '; Invoke-Expression "malicious"
        result = sanitize_powershell_string("'; Invoke-Expression 'malicious")
        assert "'" not in result or "''" in result


class TestAppleScriptSanitization:
    """Tests für AppleScript String Sanitization"""

    def test_normal_string(self):
        assert sanitize_applescript_string("hello world") == "hello world"

    def test_double_quote_escape(self):
        assert sanitize_applescript_string('say "hello"') == 'say \\"hello\\"'

    def test_backslash_escape(self):
        assert sanitize_applescript_string("path\\to\\file") == "path\\\\to\\\\file"

    def test_combined_escapes(self):
        result = sanitize_applescript_string('test\\path "with quotes"')
        assert result == 'test\\\\path \\"with quotes\\"'

    def test_empty_string(self):
        assert sanitize_applescript_string("") == ""


class TestProgramNameValidation:
    """Tests für Program Name Validation"""

    def test_valid_names(self):
        assert validate_program_name("Firefox") == "Firefox"
        assert validate_program_name("Google Chrome") == "Google Chrome"
        assert validate_program_name("my-app") == "my-app"
        assert validate_program_name("app_v2.0") == "app_v2.0"
        assert validate_program_name("App (x64)") == "App (x64)"

    def test_strips_whitespace(self):
        assert validate_program_name("  Firefox  ") == "Firefox"

    def test_empty_name_raises(self):
        with pytest.raises(ValueError, match="empty"):
            validate_program_name("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="empty"):
            validate_program_name("   ")

    def test_injection_characters_rejected(self):
        with pytest.raises(ValueError, match="Invalid"):
            validate_program_name("app; rm -rf /")

        with pytest.raises(ValueError, match="Invalid"):
            validate_program_name("app | cat /etc/passwd")

        with pytest.raises(ValueError, match="Invalid"):
            validate_program_name("app & malicious")

        with pytest.raises(ValueError, match="Invalid"):
            validate_program_name("app`whoami`")


class TestFilePathValidation:
    """Tests für File Path Validation"""

    def test_valid_paths(self):
        assert validate_file_path("/usr/local/bin") == "/usr/local/bin"
        assert validate_file_path("C:\\Users\\test") == "C:\\Users\\test"
        assert validate_file_path("./relative/path") == "./relative/path"

    def test_strips_whitespace(self):
        assert validate_file_path("  /usr/bin  ") == "/usr/bin"

    def test_empty_path_raises(self):
        with pytest.raises(ValueError, match="empty"):
            validate_file_path("")

    def test_semicolon_injection(self):
        with pytest.raises(ValueError, match="dangerous"):
            validate_file_path("/tmp; rm -rf /")

    def test_pipe_injection(self):
        with pytest.raises(ValueError, match="dangerous"):
            validate_file_path("/tmp | cat /etc/shadow")

    def test_ampersand_injection(self):
        with pytest.raises(ValueError, match="dangerous"):
            validate_file_path("/tmp & echo pwned")

    def test_backtick_injection(self):
        with pytest.raises(ValueError, match="dangerous"):
            validate_file_path("/tmp/`whoami`")

    def test_dollar_injection(self):
        with pytest.raises(ValueError, match="dangerous"):
            validate_file_path("/tmp/$(whoami)")

    def test_newline_injection(self):
        with pytest.raises(ValueError, match="dangerous"):
            validate_file_path("/tmp\nrm -rf /")


class TestDescriptionValidation:
    """Tests für Description Validation"""

    def test_normal_description(self):
        assert validate_description("System-Wartung") == "System-Wartung"

    def test_empty_returns_default(self):
        assert validate_description("") == "TechCare"
        assert validate_description(None) == "TechCare"

    def test_strips_dangerous_chars(self):
        result = validate_description("test;rm -rf /")
        assert ";" not in result

    def test_max_length(self):
        long_text = "x" * 300
        result = validate_description(long_text, max_length=200)
        assert len(result) <= 200


class TestIntegerValidation:
    """Tests für Integer Validation"""

    def test_valid_integer(self):
        assert validate_integer(42) == 42
        assert validate_integer("42") == 42
        assert validate_integer(0) == 0

    def test_min_val(self):
        assert validate_integer(5, min_val=0) == 5
        with pytest.raises(ValueError, match="below minimum"):
            validate_integer(-1, min_val=0)

    def test_max_val(self):
        assert validate_integer(5, max_val=10) == 5
        with pytest.raises(ValueError, match="above maximum"):
            validate_integer(11, max_val=10)

    def test_min_and_max(self):
        assert validate_integer(5, min_val=1, max_val=10) == 5
        with pytest.raises(ValueError):
            validate_integer(0, min_val=1, max_val=10)

    def test_invalid_type(self):
        with pytest.raises(ValueError, match="Invalid integer"):
            validate_integer("abc")

        with pytest.raises(ValueError, match="Invalid integer"):
            validate_integer(None)

    def test_float_truncation(self):
        assert validate_integer(3.9) == 3

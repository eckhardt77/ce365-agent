"""
Tests für Command-Gating — /connect und /mcp Edition-Checks
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from ce365.core.license import check_edition_features


class TestConnectGating:
    """/connect erfordert ssh_remote Feature (Core oder Scale)"""

    def test_free_has_no_ssh_remote(self):
        assert check_edition_features("free", "ssh_remote") is False

    def test_core_has_ssh_remote(self):
        assert check_edition_features("core", "ssh_remote") is True

    def test_scale_has_ssh_remote(self):
        assert check_edition_features("scale", "ssh_remote") is True

    @pytest.mark.asyncio
    async def test_connect_blocked_for_free(self):
        """_cmd_connect zeigt Fehlermeldung für Free Edition"""
        from ce365.core.commands import _cmd_connect

        bot = MagicMock()
        bot.console = MagicMock()
        bot.console.display_error = MagicMock()

        settings_mock = MagicMock()
        settings_mock.edition = "free"

        with patch("ce365.config.settings.get_settings", return_value=settings_mock):
            await _cmd_connect(bot, "example.com")

        bot.console.display_error.assert_called_once()
        error_msg = bot.console.display_error.call_args[0][0]
        assert "MSP Core" in error_msg or "Remote" in error_msg


class TestMcpGating:
    """/mcp erfordert mcp_integration Feature (nur Scale)"""

    def test_free_has_no_mcp(self):
        assert check_edition_features("free", "mcp_integration") is False

    def test_core_has_no_mcp(self):
        assert check_edition_features("core", "mcp_integration") is False

    def test_scale_has_mcp(self):
        assert check_edition_features("scale", "mcp_integration") is True

    @pytest.mark.asyncio
    async def test_mcp_blocked_for_free(self):
        """_cmd_mcp zeigt Fehlermeldung für Free Edition"""
        from ce365.core.commands import _cmd_mcp

        bot = MagicMock()
        bot.console = MagicMock()
        bot.console.display_error = MagicMock()

        settings_mock = MagicMock()
        settings_mock.edition = "free"

        with patch("ce365.config.settings.get_settings", return_value=settings_mock):
            await _cmd_mcp(bot, "list")

        bot.console.display_error.assert_called_once()
        error_msg = bot.console.display_error.call_args[0][0]
        assert "Scale" in error_msg or "MCP" in error_msg

    @pytest.mark.asyncio
    async def test_mcp_blocked_for_core(self):
        """_cmd_mcp zeigt Fehlermeldung für Core Edition"""
        from ce365.core.commands import _cmd_mcp

        bot = MagicMock()
        bot.console = MagicMock()
        bot.console.display_error = MagicMock()

        settings_mock = MagicMock()
        settings_mock.edition = "core"

        with patch("ce365.config.settings.get_settings", return_value=settings_mock):
            await _cmd_mcp(bot, "list")

        bot.console.display_error.assert_called_once()


class TestSlashCommandHandler:
    """SlashCommandHandler registriert alle Standard-Commands"""

    def test_handler_has_connect_command(self):
        from ce365.core.commands import SlashCommandHandler
        handler = SlashCommandHandler()
        assert "connect" in handler._commands

    def test_handler_has_mcp_command(self):
        from ce365.core.commands import SlashCommandHandler
        handler = SlashCommandHandler()
        assert "mcp" in handler._commands

    def test_handler_has_help_command(self):
        from ce365.core.commands import SlashCommandHandler
        handler = SlashCommandHandler()
        assert "help" in handler._commands

    def test_is_command_detects_slash(self):
        from ce365.core.commands import SlashCommandHandler
        handler = SlashCommandHandler()
        assert handler.is_command("/help") is True
        assert handler.is_command("/connect example.com") is True

    def test_is_command_detects_alias(self):
        from ce365.core.commands import SlashCommandHandler
        handler = SlashCommandHandler()
        assert handler.is_command("stats") is True
        assert handler.is_command("privacy") is True

    def test_is_command_rejects_normal_text(self):
        from ce365.core.commands import SlashCommandHandler
        handler = SlashCommandHandler()
        assert handler.is_command("hello world") is False
        assert handler.is_command("mein PC ist langsam") is False

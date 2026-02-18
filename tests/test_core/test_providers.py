"""
Tests für Multi-Provider Abstraktion

Testet Provider-Factory, Tool-Format-Translation, Response-Normalisierung.
"""

import pytest
from unittest.mock import patch, MagicMock
from ce365.core.providers import (
    create_provider,
    AnthropicProvider,
    OpenAIProvider,
    OpenRouterProvider,
    LLMProvider,
    DEFAULT_MODELS,
)


class TestProviderFactory:
    """Tests für Provider Factory"""

    def test_create_anthropic_provider(self):
        with patch("anthropic.Anthropic"):
            provider = create_provider("anthropic", "sk-ant-test")
        assert isinstance(provider, AnthropicProvider)

    def test_create_openai_provider(self):
        with patch("openai.OpenAI"):
            provider = create_provider("openai", "sk-test")
        assert isinstance(provider, OpenAIProvider)

    def test_create_openrouter_provider(self):
        with patch("openai.OpenAI"):
            provider = create_provider("openrouter", "sk-or-test")
        assert isinstance(provider, OpenRouterProvider)

    def test_unknown_provider_raises(self):
        with pytest.raises(ValueError, match="Unbekannter Provider"):
            create_provider("unknown", "key")

    def test_case_insensitive(self):
        with patch("anthropic.Anthropic"):
            provider = create_provider("ANTHROPIC", "sk-ant-test")
        assert isinstance(provider, AnthropicProvider)

    def test_default_models(self):
        assert "anthropic" in DEFAULT_MODELS
        assert "openai" in DEFAULT_MODELS
        assert "openrouter" in DEFAULT_MODELS

    def test_custom_model(self):
        with patch("anthropic.Anthropic"):
            provider = create_provider("anthropic", "sk-ant-test", model="claude-opus-4-6")
        assert provider.model == "claude-opus-4-6"


class TestTokenTracking:
    """Tests für Token-Tracking"""

    def test_initial_tokens_zero(self):
        with patch("anthropic.Anthropic"):
            provider = create_provider("anthropic", "sk-ant-test")
        usage = provider.get_token_usage()
        assert usage["input_tokens"] == 0
        assert usage["output_tokens"] == 0
        assert usage["total_tokens"] == 0

    def test_reset_tokens(self):
        with patch("anthropic.Anthropic"):
            provider = create_provider("anthropic", "sk-ant-test")
        provider.input_tokens = 100
        provider.output_tokens = 50
        provider.reset_token_usage()
        assert provider.get_token_usage()["total_tokens"] == 0


class TestOpenAIToolConversion:
    """Tests für Anthropic → OpenAI Tool-Format-Konvertierung"""

    def test_convert_tools(self):
        with patch("openai.OpenAI"):
            provider = create_provider("openai", "sk-test")

        anthropic_tools = [
            {
                "name": "get_system_info",
                "description": "System-Informationen abrufen",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            }
        ]

        oai_tools = provider._convert_tools(anthropic_tools)

        assert len(oai_tools) == 1
        assert oai_tools[0]["type"] == "function"
        assert oai_tools[0]["function"]["name"] == "get_system_info"
        assert oai_tools[0]["function"]["description"] == "System-Informationen abrufen"
        assert oai_tools[0]["function"]["parameters"]["type"] == "object"

    def test_convert_string_messages(self):
        with patch("openai.OpenAI"):
            provider = create_provider("openai", "sk-test")

        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ]

        oai_messages = provider._convert_messages(messages)

        assert len(oai_messages) == 2
        assert oai_messages[0]["role"] == "user"
        assert oai_messages[0]["content"] == "Hello"
        assert oai_messages[1]["role"] == "assistant"

    def test_convert_tool_results(self):
        with patch("openai.OpenAI"):
            provider = create_provider("openai", "sk-test")

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "call_123",
                        "content": "OS: macOS 15",
                    }
                ],
            }
        ]

        oai_messages = provider._convert_messages(messages)

        assert len(oai_messages) == 1
        assert oai_messages[0]["role"] == "tool"
        assert oai_messages[0]["tool_call_id"] == "call_123"
        assert oai_messages[0]["content"] == "OS: macOS 15"


class TestResponseNormalization:
    """Tests für OpenAI → Anthropic Response-Normalisierung"""

    def test_normalize_text_response(self):
        with patch("openai.OpenAI"):
            provider = create_provider("openai", "sk-test")

        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Hello World"
        mock_choice.message.tool_calls = None
        mock_choice.finish_reason = "stop"
        mock_response.choices = [mock_choice]

        result = provider._normalize_response(mock_response)

        assert result.stop_reason == "end_turn"
        assert len(result.content) == 1
        assert result.content[0].type == "text"
        assert result.content[0].text == "Hello World"

    def test_normalize_tool_call_response(self):
        with patch("openai.OpenAI"):
            provider = create_provider("openai", "sk-test")

        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = None

        mock_tc = MagicMock()
        mock_tc.id = "call_456"
        mock_tc.function.name = "get_system_info"
        mock_tc.function.arguments = '{}'
        mock_choice.message.tool_calls = [mock_tc]
        mock_choice.finish_reason = "tool_calls"
        mock_response.choices = [mock_choice]

        result = provider._normalize_response(mock_response)

        assert result.stop_reason == "tool_use"
        assert len(result.content) == 1
        assert result.content[0].type == "tool_use"
        assert result.content[0].name == "get_system_info"
        assert result.content[0].id == "call_456"

"""
CE365 Agent - Multi-Provider LLM Abstraction

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
Licensed under Source Available License

Unterstützt: Anthropic (Claude), OpenAI (GPT), OpenRouter (viele Modelle)
BYOK (Bring Your Own Key) Modell.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class ProviderResponse:
    """Normalisierte Antwort aller Provider"""
    stop_reason: str  # "end_turn" oder "tool_use"
    content: List[Any]  # Content Blocks
    usage: Dict[str, int] = field(default_factory=lambda: {
        "input_tokens": 0,
        "output_tokens": 0,
    })


class LLMProvider(ABC):
    """Abstrakte Basisklasse für LLM Provider"""

    def __init__(self):
        self.input_tokens = 0
        self.output_tokens = 0

    @abstractmethod
    def create_message(
        self,
        messages: List[Dict[str, Any]],
        system: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 4096,
    ) -> Any:
        """API Call mit Tool Use Support"""
        ...

    def get_token_usage(self) -> Dict[str, int]:
        """Aktuelle Token-Nutzung"""
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.input_tokens + self.output_tokens,
        }

    def reset_token_usage(self):
        """Token Counter zurücksetzen"""
        self.input_tokens = 0
        self.output_tokens = 0


class AnthropicProvider(LLMProvider):
    """Anthropic Claude Provider"""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5-20250929"):
        super().__init__()
        from anthropic import Anthropic
        self.client = Anthropic(api_key=api_key)
        self.model = model

    def create_message(
        self,
        messages: List[Dict[str, Any]],
        system: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 4096,
    ) -> Any:
        params = {
            "model": self.model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": messages,
        }

        if tools:
            params["tools"] = tools

        try:
            response = self.client.messages.create(**params)

            if hasattr(response, "usage"):
                self.input_tokens += response.usage.input_tokens
                self.output_tokens += response.usage.output_tokens

            return response

        except Exception as e:
            raise Exception(f"Anthropic API Error: {str(e)}")


class OpenAIProvider(LLMProvider):
    """OpenAI GPT Provider"""

    def __init__(self, api_key: str, model: str = "gpt-4o", base_url: str = None):
        super().__init__()
        from openai import OpenAI
        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self.client = OpenAI(**kwargs)
        self.model = model

    def create_message(
        self,
        messages: List[Dict[str, Any]],
        system: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 4096,
    ) -> Any:
        # OpenAI Messages Format: system message als erste Message
        oai_messages = [{"role": "system", "content": system}]
        oai_messages.extend(self._convert_messages(messages))

        params = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": oai_messages,
        }

        if tools:
            params["tools"] = self._convert_tools(tools)

        try:
            response = self.client.chat.completions.create(**params)

            # Token Tracking
            if response.usage:
                self.input_tokens += response.usage.prompt_tokens
                self.output_tokens += response.usage.completion_tokens

            # Normalisiere Response zu Anthropic-kompatiblem Format
            return self._normalize_response(response)

        except Exception as e:
            raise Exception(f"OpenAI API Error: {str(e)}")

    def _convert_messages(self, messages: List[Dict[str, Any]]) -> List[Dict]:
        """Konvertiert Anthropic Messages → OpenAI Format"""
        oai_messages = []

        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            # String content
            if isinstance(content, str):
                oai_messages.append({"role": role, "content": content})
                continue

            # List content (Anthropic style)
            if isinstance(content, list):
                # Tool results
                if any(isinstance(c, dict) and c.get("type") == "tool_result" for c in content):
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "tool_result":
                            oai_messages.append({
                                "role": "tool",
                                "tool_call_id": item["tool_use_id"],
                                "content": item.get("content", ""),
                            })
                    continue

                # Text + tool_use blocks (assistant response)
                text_parts = []
                tool_calls = []

                for block in content:
                    if hasattr(block, "type"):
                        if block.type == "text":
                            text_parts.append(block.text)
                        elif block.type == "tool_use":
                            import json
                            tool_calls.append({
                                "id": block.id,
                                "type": "function",
                                "function": {
                                    "name": block.name,
                                    "arguments": json.dumps(block.input),
                                },
                            })

                assistant_msg = {
                    "role": "assistant",
                    "content": "\n".join(text_parts) if text_parts else None,
                }
                if tool_calls:
                    assistant_msg["tool_calls"] = tool_calls
                oai_messages.append(assistant_msg)
                continue

            # Fallback
            oai_messages.append({"role": role, "content": str(content)})

        return oai_messages

    def _convert_tools(self, anthropic_tools: List[Dict]) -> List[Dict]:
        """Konvertiert Anthropic Tool-Definitionen → OpenAI Functions Format"""
        oai_tools = []
        for tool in anthropic_tools:
            oai_tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("input_schema", {}),
                },
            })
        return oai_tools

    def _normalize_response(self, response) -> Any:
        """Normalisiert OpenAI Response → Anthropic-kompatibles Format"""
        choice = response.choices[0]
        message = choice.message

        # Erstelle Anthropic-kompatible Content Blocks
        content = []

        if message.content:
            content.append(_TextBlock(text=message.content))

        if message.tool_calls:
            import json
            for tc in message.tool_calls:
                content.append(_ToolUseBlock(
                    id=tc.id,
                    name=tc.function.name,
                    input=json.loads(tc.function.arguments),
                ))

        # Stop reason mapping
        stop_reason = "end_turn"
        if choice.finish_reason == "tool_calls":
            stop_reason = "tool_use"

        return _NormalizedResponse(
            stop_reason=stop_reason,
            content=content,
        )


class OpenRouterProvider(OpenAIProvider):
    """OpenRouter Provider (OpenAI-kompatible API)"""

    def __init__(self, api_key: str, model: str = "anthropic/claude-sonnet-4-5-20250929"):
        super().__init__(
            api_key=api_key,
            model=model,
            base_url="https://openrouter.ai/api/v1",
        )


# Interne Hilfsklassen für normalisierte Responses
class _TextBlock:
    def __init__(self, text: str):
        self.type = "text"
        self.text = text


class _ToolUseBlock:
    def __init__(self, id: str, name: str, input: dict):
        self.type = "tool_use"
        self.id = id
        self.name = name
        self.input = input


class _NormalizedResponse:
    def __init__(self, stop_reason: str, content: list):
        self.stop_reason = stop_reason
        self.content = content


# Provider Factory
DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-4-5-20250929",
    "openai": "gpt-4o",
    "openrouter": "anthropic/claude-sonnet-4-5-20250929",
}


def create_provider(provider_name: str, api_key: str, model: str = None) -> LLMProvider:
    """
    Factory für LLM Provider

    Args:
        provider_name: "anthropic", "openai", "openrouter"
        api_key: API Key für den Provider
        model: Optionales Model (sonst Default)

    Returns:
        LLMProvider Instanz
    """
    provider_name = provider_name.lower()
    model = model or DEFAULT_MODELS.get(provider_name)

    if provider_name == "anthropic":
        return AnthropicProvider(api_key=api_key, model=model)
    elif provider_name == "openai":
        return OpenAIProvider(api_key=api_key, model=model)
    elif provider_name == "openrouter":
        return OpenRouterProvider(api_key=api_key, model=model)
    else:
        raise ValueError(f"Unbekannter Provider: {provider_name}. Unterstützt: anthropic, openai, openrouter")

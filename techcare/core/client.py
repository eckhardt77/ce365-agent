from typing import List, Dict, Any, Optional
from anthropic import Anthropic
from techcare.config.settings import get_settings


class AnthropicClient:
    """Wrapper für Anthropic API"""

    def __init__(self):
        settings = get_settings()
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.claude_model
        self.input_tokens = 0
        self.output_tokens = 0

    def create_message(
        self,
        messages: List[Dict[str, Any]],
        system: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 4096,
    ) -> Any:
        """
        Claude API Call mit Tool Use Support

        Args:
            messages: Conversation History
            system: System Prompt
            tools: Tool-Definitionen (optional)
            max_tokens: Max Tokens für Response

        Returns:
            Anthropic Message Object
        """
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

            # Token Tracking
            if hasattr(response, "usage"):
                self.input_tokens += response.usage.input_tokens
                self.output_tokens += response.usage.output_tokens

            return response

        except Exception as e:
            raise Exception(f"Anthropic API Error: {str(e)}")

    def get_token_usage(self) -> Dict[str, int]:
        """Aktuelle Token-Nutzung zurückgeben"""
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.input_tokens + self.output_tokens,
        }

    def reset_token_usage(self):
        """Token Counter zurücksetzen"""
        self.input_tokens = 0
        self.output_tokens = 0

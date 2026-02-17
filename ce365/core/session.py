import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime


class Session:
    """Session Management für CE365 Agent"""

    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.created_at = datetime.now()
        self.messages: List[Dict[str, Any]] = []

    def add_message(self, role: str, content: Any):
        """
        Nachricht zur History hinzufügen

        Args:
            role: "user" oder "assistant"
            content: Text oder List[Dict] (für Tool Use)
        """
        message = {"role": role, "content": content}
        self.messages.append(message)

    def get_messages(self) -> List[Dict[str, Any]]:
        """Conversation History für API Call"""
        return self.messages.copy()

    def get_last_message(self) -> Optional[Dict[str, Any]]:
        """Letzte Nachricht zurückgeben"""
        return self.messages[-1] if self.messages else None

    def clear_messages(self):
        """History löschen"""
        self.messages = []

    def __repr__(self):
        return f"Session(id={self.session_id}, messages={len(self.messages)})"

"""
Tests für Session Management

Testet Session-Erstellung, Message History und Verwaltung.
"""

import pytest
from ce365.core.session import Session


class TestSessionInit:
    """Tests für Session-Initialisierung"""

    def test_creates_with_uuid(self, session):
        assert session.session_id is not None
        assert len(session.session_id) == 36  # UUID format

    def test_creates_with_custom_id(self):
        s = Session(session_id="custom-id-123")
        assert s.session_id == "custom-id-123"

    def test_empty_messages(self, session):
        assert session.messages == []

    def test_created_at_set(self, session):
        assert session.created_at is not None


class TestMessageManagement:
    """Tests für Nachrichten-Verwaltung"""

    def test_add_user_message(self, session):
        session.add_message("user", "Hello")
        assert len(session.messages) == 1
        assert session.messages[0]["role"] == "user"
        assert session.messages[0]["content"] == "Hello"

    def test_add_assistant_message(self, session):
        session.add_message("assistant", "Hi there")
        assert session.messages[0]["role"] == "assistant"

    def test_add_complex_content(self, session):
        content = [
            {"type": "text", "text": "Let me check..."},
            {"type": "tool_use", "id": "t1", "name": "check_logs", "input": {}}
        ]
        session.add_message("assistant", content)
        assert session.messages[0]["content"] == content

    def test_multiple_messages(self, session):
        session.add_message("user", "Hi")
        session.add_message("assistant", "Hello!")
        session.add_message("user", "Check my system")
        assert len(session.messages) == 3


class TestMessageRetrieval:
    """Tests für Nachrichten-Abruf"""

    def test_get_messages_returns_copy(self, session):
        session.add_message("user", "Test")
        messages = session.get_messages()
        messages.clear()
        assert len(session.messages) == 1  # Original unverändert

    def test_get_last_message(self, session):
        session.add_message("user", "First")
        session.add_message("assistant", "Second")
        last = session.get_last_message()
        assert last["content"] == "Second"

    def test_get_last_message_empty(self, session):
        assert session.get_last_message() is None

    def test_clear_messages(self, session):
        session.add_message("user", "Test")
        session.add_message("assistant", "Reply")
        session.clear_messages()
        assert len(session.messages) == 0


class TestRepr:
    """Tests für String-Repräsentation"""

    def test_repr_format(self, session):
        repr_str = repr(session)
        assert "Session" in repr_str
        assert session.session_id in repr_str
        assert "messages=0" in repr_str

    def test_repr_with_messages(self, session):
        session.add_message("user", "Hi")
        session.add_message("assistant", "Hello")
        assert "messages=2" in repr(session)

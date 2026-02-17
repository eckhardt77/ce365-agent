"""
Tests für ToolRegistry

Testet Tool Registration, Lookup und Definition Export.
"""

import pytest
from ce365.tools.registry import ToolRegistry


class TestToolRegistration:
    """Tests für Tool Registration"""

    def test_register_audit_tool(self, tool_registry, mock_audit_tool):
        tool_registry.register(mock_audit_tool)
        assert len(tool_registry) == 1
        assert tool_registry.is_audit_tool("mock_audit")

    def test_register_repair_tool(self, tool_registry, mock_repair_tool):
        tool_registry.register(mock_repair_tool)
        assert len(tool_registry) == 1
        assert tool_registry.is_repair_tool("mock_repair")

    def test_duplicate_registration_raises(self, tool_registry, mock_audit_tool):
        tool_registry.register(mock_audit_tool)
        with pytest.raises(ValueError, match="bereits registriert"):
            tool_registry.register(mock_audit_tool)

    def test_register_both_types(self, tool_registry, mock_audit_tool, mock_repair_tool):
        tool_registry.register(mock_audit_tool)
        tool_registry.register(mock_repair_tool)
        assert len(tool_registry) == 2


class TestToolLookup:
    """Tests für Tool Lookup"""

    def test_get_existing_tool(self, tool_registry, mock_audit_tool):
        tool_registry.register(mock_audit_tool)
        tool = tool_registry.get_tool("mock_audit")
        assert tool is not None
        assert tool.name == "mock_audit"

    def test_get_nonexistent_tool(self, tool_registry):
        assert tool_registry.get_tool("nonexistent") is None

    def test_get_all_tools(self, tool_registry, mock_audit_tool, mock_repair_tool):
        tool_registry.register(mock_audit_tool)
        tool_registry.register(mock_repair_tool)
        all_tools = tool_registry.get_all_tools()
        assert len(all_tools) == 2

    def test_get_audit_tools(self, tool_registry, mock_audit_tool, mock_repair_tool):
        tool_registry.register(mock_audit_tool)
        tool_registry.register(mock_repair_tool)
        audit_tools = tool_registry.get_audit_tools()
        assert len(audit_tools) == 1
        assert audit_tools[0].name == "mock_audit"

    def test_get_repair_tools(self, tool_registry, mock_audit_tool, mock_repair_tool):
        tool_registry.register(mock_audit_tool)
        tool_registry.register(mock_repair_tool)
        repair_tools = tool_registry.get_repair_tools()
        assert len(repair_tools) == 1
        assert repair_tools[0].name == "mock_repair"


class TestToolCategories:
    """Tests für Tool-Kategorisierung"""

    def test_is_audit_tool(self, tool_registry, mock_audit_tool):
        tool_registry.register(mock_audit_tool)
        assert tool_registry.is_audit_tool("mock_audit") is True
        assert tool_registry.is_audit_tool("nonexistent") is False

    def test_is_repair_tool(self, tool_registry, mock_repair_tool):
        tool_registry.register(mock_repair_tool)
        assert tool_registry.is_repair_tool("mock_repair") is True
        assert tool_registry.is_repair_tool("nonexistent") is False

    def test_audit_not_repair(self, tool_registry, mock_audit_tool):
        tool_registry.register(mock_audit_tool)
        assert tool_registry.is_repair_tool("mock_audit") is False


class TestToolDefinitions:
    """Tests für Anthropic API Tool Definitions"""

    def test_get_definitions(self, tool_registry, mock_audit_tool):
        tool_registry.register(mock_audit_tool)
        definitions = tool_registry.get_tool_definitions()
        assert len(definitions) == 1
        assert definitions[0]["name"] == "mock_audit"
        assert "description" in definitions[0]
        assert "input_schema" in definitions[0]

    def test_empty_registry_definitions(self, tool_registry):
        assert tool_registry.get_tool_definitions() == []


class TestRepr:
    """Tests für String-Repräsentation"""

    def test_repr(self, tool_registry, mock_audit_tool, mock_repair_tool):
        tool_registry.register(mock_audit_tool)
        tool_registry.register(mock_repair_tool)
        repr_str = repr(tool_registry)
        assert "tools=2" in repr_str
        assert "audit=1" in repr_str
        assert "repair=1" in repr_str

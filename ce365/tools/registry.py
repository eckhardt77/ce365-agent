from typing import Dict, List, Optional
from ce365.tools.base import BaseTool, AuditTool, RepairTool


class ToolRegistry:
    """
    Zentrale Registry für alle Tools

    Verwaltet:
    - Tool Registration
    - Tool Lookup
    - Tool Definitions für Anthropic API
    """

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._audit_tools: List[str] = []
        self._repair_tools: List[str] = []

    def register(self, tool: BaseTool):
        """
        Tool registrieren

        Args:
            tool: Tool-Instanz
        """
        tool_name = tool.name

        if tool_name in self._tools:
            raise ValueError(f"Tool '{tool_name}' bereits registriert")

        self._tools[tool_name] = tool

        # Kategorisieren
        if isinstance(tool, AuditTool):
            self._audit_tools.append(tool_name)
        elif isinstance(tool, RepairTool):
            self._repair_tools.append(tool_name)

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Tool nach Name holen"""
        return self._tools.get(name)

    def get_all_tools(self) -> List[BaseTool]:
        """Alle registrierten Tools"""
        return list(self._tools.values())

    def get_audit_tools(self) -> List[BaseTool]:
        """Nur Audit-Tools"""
        return [self._tools[name] for name in self._audit_tools]

    def get_repair_tools(self) -> List[BaseTool]:
        """Nur Repair-Tools"""
        return [self._tools[name] for name in self._repair_tools]

    def get_tool_definitions(self) -> List[Dict]:
        """
        Tool-Definitionen für Anthropic API

        Returns:
            List[Dict]: Tools im Anthropic Format
        """
        return [tool.to_anthropic_tool() for tool in self._tools.values()]

    def is_repair_tool(self, tool_name: str) -> bool:
        """Check ob Tool ein Repair-Tool ist"""
        return tool_name in self._repair_tools

    def is_audit_tool(self, tool_name: str) -> bool:
        """Check ob Tool ein Audit-Tool ist"""
        return tool_name in self._audit_tools

    def unregister(self, tool_name: str) -> bool:
        """
        Tool de-registrieren (fuer dynamische MCP-Tools).

        Returns:
            True wenn Tool entfernt wurde
        """
        if tool_name not in self._tools:
            return False

        del self._tools[tool_name]

        if tool_name in self._audit_tools:
            self._audit_tools.remove(tool_name)
        if tool_name in self._repair_tools:
            self._repair_tools.remove(tool_name)

        return True

    def __len__(self):
        return len(self._tools)

    def __repr__(self):
        return (
            f"ToolRegistry(tools={len(self._tools)}, "
            f"audit={len(self._audit_tools)}, "
            f"repair={len(self._repair_tools)})"
        )

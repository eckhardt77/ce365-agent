"""
CE365 Agent - MCP Proxy Tool

Proxy-Tool das MCP-Server-Tools in die CE365 ToolRegistry einbindet.
Leitet Tool-Calls transparent an den MCP-Server weiter.
"""

from typing import Dict, Any
from ce365.tools.base import AuditTool
from ce365.integrations.mcp_client import MCPClient, MCPToolDefinition


class MCPProxyTool(AuditTool):
    """
    Proxy-Tool fuer MCP-Server-Tools.

    Wird dynamisch aus MCPToolDefinition erstellt.
    Leitet execute() Aufrufe an den MCP-Server weiter.
    """

    def __init__(
        self,
        mcp_tool: MCPToolDefinition,
        mcp_client: MCPClient,
        prefix: str = "",
        server_name: str = "",
    ):
        super().__init__()
        self._mcp_tool = mcp_tool
        self._mcp_client = mcp_client
        self._prefix = prefix
        self._server_name = server_name

    @property
    def name(self) -> str:
        if self._prefix:
            return f"{self._prefix}{self._mcp_tool.name}"
        return self._mcp_tool.name

    @property
    def description(self) -> str:
        server_info = f" [MCP: {self._server_name}]" if self._server_name else " [MCP]"
        return f"{self._mcp_tool.description}{server_info}"

    @property
    def input_schema(self) -> Dict[str, Any]:
        schema = self._mcp_tool.input_schema
        if not schema:
            return {"type": "object", "properties": {}, "required": []}
        return schema

    async def execute(self, **kwargs) -> str:
        """Tool-Call an MCP-Server weiterleiten"""
        if not self._mcp_client.connected:
            return f"MCP-Server '{self._server_name}' nicht verbunden"

        result = await self._mcp_client.call_tool(
            name=self._mcp_tool.name,
            args=kwargs,
        )

        if result.success:
            return result.content or "(Kein Inhalt)"
        else:
            return f"MCP-Fehler: {result.error}"

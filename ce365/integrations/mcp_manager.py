"""
CE365 Agent - MCP Connection Manager

Verwaltet Verbindungen zu MCP-Servern.
Laedt Server-Konfiguration aus ~/.ce365/mcp_servers.json.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any

from ce365.integrations.mcp_client import MCPClient, MCPToolDefinition
from ce365.integrations.mcp_proxy_tool import MCPProxyTool


@dataclass
class MCPServerConfig:
    """Konfiguration fuer einen MCP-Server"""
    name: str
    url: str
    auth_token: str = ""
    tool_prefix: str = ""
    auto_connect: bool = False


class MCPManager:
    """
    Verwaltet MCP-Server-Verbindungen.

    Konfiguration: ~/.ce365/mcp_servers.json
    Format:
    {
        "servers": [
            {
                "name": "freshdesk",
                "url": "http://localhost:8080/mcp",
                "auth_token": "...",
                "tool_prefix": "fd_",
                "auto_connect": false
            }
        ]
    }
    """

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path.home() / ".ce365" / "mcp_servers.json"
        self._servers: Dict[str, MCPServerConfig] = {}
        self._clients: Dict[str, MCPClient] = {}
        self._proxy_tools: Dict[str, List[MCPProxyTool]] = {}  # server_name -> tools
        self._load_config()

    def _load_config(self):
        """Server-Konfiguration laden"""
        if not self.config_path.exists():
            return

        try:
            data = json.loads(self.config_path.read_text(encoding="utf-8"))
            for server_data in data.get("servers", []):
                config = MCPServerConfig(
                    name=server_data["name"],
                    url=server_data["url"],
                    auth_token=server_data.get("auth_token", ""),
                    tool_prefix=server_data.get("tool_prefix", ""),
                    auto_connect=server_data.get("auto_connect", False),
                )
                self._servers[config.name] = config
        except Exception:
            pass  # Fehlerhafte Config ignorieren

    def get_server_names(self) -> List[str]:
        """Alle konfigurierten Server-Namen"""
        return list(self._servers.keys())

    def get_server_status(self) -> List[Dict[str, Any]]:
        """Status aller Server"""
        status = []
        for name, config in self._servers.items():
            client = self._clients.get(name)
            status.append({
                "name": name,
                "url": config.url,
                "connected": client.connected if client else False,
                "tool_count": len(self._proxy_tools.get(name, [])),
                "tool_prefix": config.tool_prefix,
            })
        return status

    async def connect(self, server_name: str) -> List[MCPProxyTool]:
        """
        Mit einem MCP-Server verbinden und seine Tools laden.

        Returns:
            Liste der Proxy-Tools die registriert werden koennen
        """
        config = self._servers.get(server_name)
        if not config:
            raise ValueError(
                f"MCP-Server '{server_name}' nicht konfiguriert. "
                f"Verfuegbar: {', '.join(self._servers.keys()) or 'keine'}"
            )

        # Bestehende Verbindung trennen
        if server_name in self._clients:
            await self.disconnect(server_name)

        # Neuen Client erstellen
        client = MCPClient(
            url=config.url,
            auth_token=config.auth_token or None,
        )

        # Verbinden
        await client.connect()
        self._clients[server_name] = client

        # Tools laden
        mcp_tools = await client.list_tools()
        proxy_tools = []
        for mcp_tool in mcp_tools:
            proxy = MCPProxyTool(
                mcp_tool=mcp_tool,
                mcp_client=client,
                prefix=config.tool_prefix,
                server_name=server_name,
            )
            proxy_tools.append(proxy)

        self._proxy_tools[server_name] = proxy_tools
        return proxy_tools

    async def disconnect(self, server_name: str) -> List[str]:
        """
        MCP-Server trennen.

        Returns:
            Liste der Tool-Namen die de-registriert werden muessen
        """
        client = self._clients.pop(server_name, None)
        if client:
            await client.disconnect()

        # Proxy-Tool-Namen sammeln fuer De-Registrierung
        tools = self._proxy_tools.pop(server_name, [])
        return [t.name for t in tools]

    async def disconnect_all(self):
        """Alle MCP-Server trennen"""
        for name in list(self._clients.keys()):
            await self.disconnect(name)

    def get_tools_for_server(self, server_name: str) -> List[MCPProxyTool]:
        """Proxy-Tools eines Servers"""
        return self._proxy_tools.get(server_name, [])

    async def auto_connect(self) -> Dict[str, List[MCPProxyTool]]:
        """Server mit auto_connect=True automatisch verbinden"""
        results = {}
        for name, config in self._servers.items():
            if config.auto_connect:
                try:
                    tools = await self.connect(name)
                    results[name] = tools
                except Exception:
                    pass  # Auto-Connect Fehler ignorieren
        return results

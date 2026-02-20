"""
CE365 Agent - MCP Client

Model Context Protocol Client fuer die Kommunikation mit MCP-Servern.
Unterstuetzt Tool-Aufrufe und Resource-Zugriff.
"""

import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

import httpx


@dataclass
class MCPToolDefinition:
    """Definition eines MCP-Tools"""
    name: str
    description: str = ""
    input_schema: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MCPToolResult:
    """Ergebnis eines MCP-Tool-Aufrufs"""
    content: str = ""
    success: bool = True
    error: str = ""
    raw_data: Optional[Dict[str, Any]] = None


@dataclass
class MCPResource:
    """Eine MCP-Resource (z.B. Ticket, Dokument)"""
    uri: str
    name: str = ""
    description: str = ""
    mime_type: str = "text/plain"


class MCPClient:
    """
    HTTP-basierter MCP-Client.

    Kommuniziert mit MCP-Servern ueber JSON-RPC 2.0 (HTTP Transport).
    Unterstuetzt:
    - tools/list — Verfuegbare Tools abfragen
    - tools/call — Tool ausfuehren
    - resources/list — Verfuegbare Resources abfragen
    - resources/read — Resource lesen
    """

    def __init__(
        self,
        url: str,
        auth_token: Optional[str] = None,
        timeout: int = 30,
    ):
        self.url = url.rstrip("/")
        self.auth_token = auth_token
        self.timeout = timeout
        self._connected: bool = False
        self._server_info: Dict[str, Any] = {}
        self._request_id: int = 0

    @property
    def connected(self) -> bool:
        return self._connected

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    def _build_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers

    async def _send_request(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """JSON-RPC 2.0 Request senden"""
        payload = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": method,
        }
        if params:
            payload["params"] = params

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.url,
                json=payload,
                headers=self._build_headers(),
            )
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                error = data["error"]
                raise RuntimeError(
                    f"MCP Error {error.get('code', '?')}: {error.get('message', 'Unknown')}"
                )

            return data.get("result", {})

    async def connect(self) -> bool:
        """
        Verbindung zum MCP-Server herstellen.
        Ruft initialize auf und prueft die Server-Capabilities.
        """
        try:
            result = await self._send_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "resources": {},
                },
                "clientInfo": {
                    "name": "ce365-agent",
                    "version": "2.0.0",
                },
            })
            self._server_info = result
            self._connected = True

            # initialized notification senden
            try:
                await self._send_request("notifications/initialized")
            except Exception:
                pass  # Notifications sind optional

            return True

        except Exception as e:
            self._connected = False
            raise ConnectionError(f"MCP-Verbindung fehlgeschlagen: {e}")

    async def list_tools(self) -> List[MCPToolDefinition]:
        """Verfuegbare Tools vom MCP-Server abfragen"""
        if not self._connected:
            raise RuntimeError("Nicht verbunden. Erst connect() aufrufen.")

        result = await self._send_request("tools/list")
        tools = []
        for tool_data in result.get("tools", []):
            tools.append(MCPToolDefinition(
                name=tool_data.get("name", ""),
                description=tool_data.get("description", ""),
                input_schema=tool_data.get("inputSchema", {}),
            ))
        return tools

    async def call_tool(
        self,
        name: str,
        args: Dict[str, Any] = None,
    ) -> MCPToolResult:
        """MCP-Tool aufrufen"""
        if not self._connected:
            raise RuntimeError("Nicht verbunden. Erst connect() aufrufen.")

        try:
            result = await self._send_request("tools/call", {
                "name": name,
                "arguments": args or {},
            })

            # Content extrahieren
            content_parts = []
            for content_block in result.get("content", []):
                if content_block.get("type") == "text":
                    content_parts.append(content_block.get("text", ""))
                elif content_block.get("type") == "resource":
                    uri = content_block.get("resource", {}).get("uri", "")
                    text = content_block.get("resource", {}).get("text", "")
                    content_parts.append(f"[Resource: {uri}]\n{text}")

            is_error = result.get("isError", False)

            return MCPToolResult(
                content="\n".join(content_parts),
                success=not is_error,
                error="" if not is_error else "\n".join(content_parts),
                raw_data=result,
            )

        except Exception as e:
            return MCPToolResult(
                content="",
                success=False,
                error=str(e),
            )

    async def list_resources(self) -> List[MCPResource]:
        """Verfuegbare Resources vom MCP-Server abfragen"""
        if not self._connected:
            raise RuntimeError("Nicht verbunden.")

        try:
            result = await self._send_request("resources/list")
            resources = []
            for res_data in result.get("resources", []):
                resources.append(MCPResource(
                    uri=res_data.get("uri", ""),
                    name=res_data.get("name", ""),
                    description=res_data.get("description", ""),
                    mime_type=res_data.get("mimeType", "text/plain"),
                ))
            return resources
        except Exception:
            return []

    async def read_resource(self, uri: str) -> str:
        """Resource vom MCP-Server lesen"""
        if not self._connected:
            raise RuntimeError("Nicht verbunden.")

        result = await self._send_request("resources/read", {"uri": uri})

        contents = result.get("contents", [])
        parts = []
        for content_block in contents:
            if "text" in content_block:
                parts.append(content_block["text"])
            elif "blob" in content_block:
                parts.append(f"[Binary data: {content_block.get('mimeType', 'unknown')}]")

        return "\n".join(parts)

    async def disconnect(self):
        """Verbindung trennen"""
        self._connected = False
        self._server_info = {}

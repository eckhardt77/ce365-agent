from abc import ABC, abstractmethod
from typing import Dict, Any, Literal
from pydantic import BaseModel


class ToolDefinition(BaseModel):
    """Anthropic Tool Definition Format"""

    name: str
    description: str
    input_schema: Dict[str, Any]


class BaseTool(ABC):
    """
    Abstract Base Class für alle Tools

    Subclasses müssen implementieren:
    - name: Tool Name (lowercase, snake_case)
    - description: Tool-Beschreibung für Claude
    - input_schema: JSON Schema für Parameter
    - execute(): Tool Execution Logic
    """

    def __init__(self):
        self.tool_type: Literal["audit", "repair"] = "audit"

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool Name"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Tool Beschreibung für Claude"""
        pass

    @property
    @abstractmethod
    def input_schema(self) -> Dict[str, Any]:
        """JSON Schema für Tool Input"""
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> str:
        """
        Tool ausführen

        Args:
            **kwargs: Tool-spezifische Parameter

        Returns:
            Execution Result als String
        """
        pass

    def to_anthropic_tool(self) -> Dict[str, Any]:
        """Anthropic Tool Use Format"""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }


class AuditTool(BaseTool):
    """
    Read-Only Tool für System-Analyse

    Audit-Tools können IMMER ausgeführt werden
    und ändern NICHTS am System
    """

    def __init__(self):
        super().__init__()
        self.tool_type = "audit"


class RepairTool(BaseTool):
    """
    Tool für System-Reparaturen

    Repair-Tools:
    - Benötigen Execution Lock (GO REPAIR Freigabe)
    - Ändern System-State
    - Werden im Changelog geloggt
    """

    def __init__(self):
        super().__init__()
        self.tool_type = "repair"
        self.requires_approval = True

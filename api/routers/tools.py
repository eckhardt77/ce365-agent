"""
TechCare Bot - Tools Router
Tool Registry & Execution
"""

from fastapi import APIRouter, Depends
from typing import List, Dict, Any

from api.models import User
from api.services.auth_service import get_current_user
from techcare.tools.registry import ToolRegistry

router = APIRouter()

# Global tool registry
tool_registry = ToolRegistry()


@router.get("/list", response_model=List[Dict[str, Any]])
async def list_tools(
    current_user: User = Depends(get_current_user)
):
    """
    List all available tools

    Returns:
        List of tool definitions (Anthropic Tool Use format)
    """
    return tool_registry.get_tool_definitions()


@router.get("/{tool_name}", response_model=Dict[str, Any])
async def get_tool(
    tool_name: str,
    current_user: User = Depends(get_current_user)
):
    """Get tool definition by name"""
    tool = tool_registry.get_tool(tool_name)

    if not tool:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool {tool_name} not found"
        )

    return {
        "name": tool.name,
        "description": tool.description,
        "type": tool.tool_type,
        "input_schema": tool.input_schema
    }

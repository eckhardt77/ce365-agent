"""
CE365 Agent - ToolCall Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class ToolCallBase(BaseModel):
    """Base ToolCall Schema"""
    tool_name: str
    tool_type: str
    tool_input: Dict[str, Any]


class ToolCallCreate(ToolCallBase):
    """ToolCall Creation Schema"""
    conversation_id: str


class ToolCallResponse(ToolCallBase):
    """ToolCall Response Schema"""
    id: str
    conversation_id: str
    tool_output: Optional[str]
    success: bool
    error_message: Optional[str]
    execution_time_ms: Optional[float]
    requires_approval: bool
    approved: bool
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True

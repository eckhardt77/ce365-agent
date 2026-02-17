"""
CE365 Agent - Message Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from api.models.message import MessageRole


class MessageBase(BaseModel):
    """Base Message Schema"""
    role: MessageRole
    content: str = Field(..., min_length=1)


class MessageCreate(MessageBase):
    """Message Creation Schema"""
    conversation_id: str


class MessageResponse(MessageBase):
    """Message Response Schema"""
    id: str
    conversation_id: str
    sequence: int
    input_tokens: Optional[int]
    output_tokens: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    """Chat Request (User sendet Nachricht)"""
    message: str = Field(..., min_length=1, max_length=10000)
    conversation_id: Optional[str] = None  # Wenn None, neue Conversation


class ChatResponse(BaseModel):
    """Chat Response (Streaming)"""
    conversation_id: str
    message_id: str
    content: str
    finished: bool = False

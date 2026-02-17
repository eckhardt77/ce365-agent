"""
TechCare Bot - Conversation Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from api.models.conversation import ConversationState


class ConversationBase(BaseModel):
    """Base Conversation Schema"""
    title: str = Field(..., min_length=1, max_length=200)
    problem_description: Optional[str] = None


class ConversationCreate(ConversationBase):
    """Conversation Creation Schema"""
    pass


class ConversationUpdate(BaseModel):
    """Conversation Update Schema"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    problem_description: Optional[str] = None
    state: Optional[ConversationState] = None


class ConversationResponse(ConversationBase):
    """Conversation Response Schema"""
    id: str
    user_id: str
    state: ConversationState
    os_type: Optional[str]
    os_version: Optional[str]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    # Message count (wird von Service gesetzt)
    message_count: Optional[int] = 0

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    """Conversation List Response"""
    conversations: List[ConversationResponse]
    total: int
    page: int
    page_size: int

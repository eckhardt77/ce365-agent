"""
TechCare Bot - Chat Router
Chat Endpoints mit SSE Streaming
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import AsyncGenerator
import json
import logging

from api.models import get_db, User, Conversation, Message
from api.models.conversation import ConversationState
from api.models.message import MessageRole
from api.schemas import (
    ConversationCreate,
    ConversationResponse,
    ConversationListResponse,
    ChatRequest,
    MessageResponse
)
from api.services.auth_service import get_current_user
from api.services.chat_service import ChatService
from api.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation_data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create new conversation"""
    # Check repair limit (Edition)
    if not current_user.can_create_repair(settings.max_repairs_per_month):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Monthly repair limit reached ({settings.max_repairs_per_month})"
        )

    # Create conversation
    conversation = Conversation(
        user_id=current_user.id,
        title=conversation_data.title,
        problem_description=conversation_data.problem_description,
        state=ConversationState.IDLE
    )

    db.add(conversation)
    current_user.increment_repairs()
    await db.commit()
    await db.refresh(conversation)

    return ConversationResponse.model_validate(conversation)


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List user's conversations"""
    offset = (page - 1) * page_size

    # Count total
    count_query = select(func.count(Conversation.id)).where(
        Conversation.user_id == current_user.id
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get conversations
    query = (
        select(Conversation)
        .where(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)
    conversations = result.scalars().all()

    # Add message count
    conversation_responses = []
    for conv in conversations:
        conv_response = ConversationResponse.model_validate(conv)

        # Count messages
        msg_count_query = select(func.count(Message.id)).where(
            Message.conversation_id == conv.id
        )
        msg_count_result = await db.execute(msg_count_query)
        conv_response.message_count = msg_count_result.scalar()

        conversation_responses.append(conv_response)

    return ConversationListResponse(
        conversations=conversation_responses,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get conversation by ID"""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    return ConversationResponse.model_validate(conversation)


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get conversation messages"""
    # Verify ownership
    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        )
    )
    conversation = conv_result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    # Get messages
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.sequence)
    )
    messages = result.scalars().all()

    return [MessageResponse.model_validate(msg) for msg in messages]


@router.post("/conversations/{conversation_id}/messages/stream")
async def chat_stream(
    conversation_id: str,
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Chat endpoint mit SSE Streaming

    Returns:
        StreamingResponse (text/event-stream)
    """
    # Verify ownership
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    # Create chat service
    chat_service = ChatService(db)

    async def event_generator() -> AsyncGenerator[str, None]:
        """SSE Event Generator"""
        try:
            # Stream response
            async for chunk in chat_service.chat_stream(
                conversation_id=conversation_id,
                user_message=chat_request.message
            ):
                # SSE Format: data: {json}\n\n
                yield f"data: {json.dumps(chunk)}\n\n"

        except Exception as e:
            logger.error(f"Chat stream error: {e}", exc_info=True)
            error_chunk = {
                "type": "error",
                "error": str(e)
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Nginx buffering ausschalten
        }
    )


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete conversation"""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    await db.delete(conversation)
    await db.commit()

    return None

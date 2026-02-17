"""
CE365 Agent - Message Model
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum, Text, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from api.models.database import Base


class MessageRole(str, enum.Enum):
    """Message Role"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(Base):
    """Message Model"""

    __tablename__ = "messages"

    # Primary Key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Foreign Key
    conversation_id = Column(
        String,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Message Content
    role = Column(SQLEnum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)

    # Token Usage (für Cost Tracking)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)

    # Sequence (für korrekte Reihenfolge)
    sequence = Column(Integer, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self):
        return f"<Message {self.role.value} - {self.content[:50]}...>"

    @property
    def total_tokens(self) -> int:
        """Total tokens (input + output)"""
        return (self.input_tokens or 0) + (self.output_tokens or 0)

    @property
    def cost_usd(self) -> float:
        """Estimated cost in USD (Claude Sonnet 4.5 pricing)"""
        # Input: $3 per 1M tokens
        # Output: $15 per 1M tokens
        input_cost = (self.input_tokens or 0) / 1_000_000 * 3
        output_cost = (self.output_tokens or 0) / 1_000_000 * 15
        return input_cost + output_cost

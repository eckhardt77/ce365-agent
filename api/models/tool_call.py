"""
TechCare Bot - ToolCall Model
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
import uuid

from api.models.database import Base


class ToolCall(Base):
    """ToolCall Model - Audit Trail für alle Tool-Aufrufe"""

    __tablename__ = "tool_calls"

    # Primary Key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Foreign Key
    conversation_id = Column(
        String,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Tool Info
    tool_name = Column(String, nullable=False, index=True)
    tool_type = Column(String, nullable=False)  # audit, repair

    # Tool Input/Output
    tool_input = Column(JSONB, nullable=False)
    tool_output = Column(Text, nullable=True)

    # Execution Info
    success = Column(Boolean, default=False, nullable=False)
    error_message = Column(Text, nullable=True)
    execution_time_ms = Column(Float, nullable=True)

    # Approval (für Repair Tools)
    requires_approval = Column(Boolean, default=False, nullable=False)
    approved = Column(Boolean, default=False, nullable=False)
    approved_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="tool_calls")

    def __repr__(self):
        return f"<ToolCall {self.tool_name} - {'✓' if self.success else '✗'}>"

    @property
    def duration_seconds(self) -> float:
        """Execution time in seconds"""
        if self.execution_time_ms:
            return self.execution_time_ms / 1000
        return 0.0

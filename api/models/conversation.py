"""
CE365 Agent - Conversation Model
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from api.models.database import Base


class ConversationState(str, enum.Enum):
    """Conversation State (Workflow State Machine)"""
    IDLE = "idle"
    AUDIT = "audit"
    ANALYSIS = "analysis"
    PLAN_READY = "plan_ready"
    LOCKED = "locked"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


class Conversation(Base):
    """Conversation Model"""

    __tablename__ = "conversations"

    # Primary Key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Foreign Key
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Metadata
    title = Column(String, nullable=False, default="Neuer Fall")
    problem_description = Column(Text, nullable=True)

    # State Machine
    state = Column(
        SQLEnum(ConversationState),
        default=ConversationState.IDLE,
        nullable=False
    )

    # System Info (detected)
    os_type = Column(String, nullable=True)  # windows, macos, linux
    os_version = Column(String, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at"
    )
    tool_calls = relationship(
        "ToolCall",
        back_populates="conversation",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Conversation {self.id} - {self.title}>"

    def can_execute_tool(self, tool_type: str) -> bool:
        """Check if tool can be executed in current state"""
        if tool_type == "audit":
            # Audit tools immer erlaubt (außer COMPLETED/FAILED)
            return self.state not in [ConversationState.COMPLETED, ConversationState.FAILED]
        elif tool_type == "repair":
            # Repair tools nur in LOCKED/EXECUTING
            return self.state in [ConversationState.LOCKED, ConversationState.EXECUTING]
        return False

    def transition_to(self, new_state: ConversationState):
        """Transition to new state"""
        # Validate transition (vereinfacht)
        valid_transitions = {
            ConversationState.IDLE: [ConversationState.AUDIT],
            ConversationState.AUDIT: [ConversationState.ANALYSIS, ConversationState.COMPLETED],
            ConversationState.ANALYSIS: [ConversationState.PLAN_READY, ConversationState.AUDIT],
            ConversationState.PLAN_READY: [ConversationState.LOCKED, ConversationState.AUDIT],
            ConversationState.LOCKED: [ConversationState.EXECUTING],
            ConversationState.EXECUTING: [ConversationState.COMPLETED, ConversationState.FAILED],
            ConversationState.COMPLETED: [],
            ConversationState.FAILED: [ConversationState.AUDIT]
        }

        if new_state not in valid_transitions.get(self.state, []):
            raise ValueError(f"Invalid state transition: {self.state} -> {new_state}")

        self.state = new_state

        # Set completed_at if completed
        if new_state == ConversationState.COMPLETED:
            self.completed_at = func.now()

"""
TechCare Bot - User Model
"""

from sqlalchemy import Column, String, Boolean, DateTime, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from api.models.database import Base


class User(Base):
    """User Model"""

    __tablename__ = "users"

    # Primary Key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Credentials
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)

    # Profile
    name = Column(String, nullable=False)
    company = Column(String, nullable=True)

    # Role & Permissions
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)

    # Usage Tracking (für Edition Limits)
    repairs_this_month = Column(Integer, default=0, nullable=False)
    last_repair_reset = Column(DateTime, default=func.now(), nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    last_login_at = Column(DateTime, nullable=True)

    # Relationships
    conversations = relationship(
        "Conversation",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User {self.email}>"

    def reset_repairs_if_needed(self):
        """Reset repairs counter if new month"""
        now = datetime.utcnow()
        if self.last_repair_reset.month != now.month or self.last_repair_reset.year != now.year:
            self.repairs_this_month = 0
            self.last_repair_reset = now

    def can_create_repair(self, max_repairs: int = None) -> bool:
        """Check if user can create new repair (Edition limit)"""
        if max_repairs is None:
            return True  # Unlimited
        self.reset_repairs_if_needed()
        return self.repairs_this_month < max_repairs

    def increment_repairs(self):
        """Increment repair counter"""
        self.reset_repairs_if_needed()
        self.repairs_this_month += 1

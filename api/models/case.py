"""
CE365 Agent - Case Model (Learning System)
"""

from sqlalchemy import Column, String, DateTime, Text, Integer, Float, Boolean
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
import uuid

from api.models.database import Base


class Case(Base):
    """Case Model - Gespeicherte Fälle für Learning System"""

    __tablename__ = "cases"

    # Primary Key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Problem Info
    problem_description = Column(Text, nullable=False)
    problem_keywords = Column(ARRAY(String), nullable=False, index=True)
    root_cause = Column(Text, nullable=False)

    # System Info
    os_type = Column(String, nullable=False, index=True)  # windows, macos, linux
    os_version = Column(String, nullable=True)

    # Solution
    solution_plan = Column(Text, nullable=False)
    solution_steps = Column(JSONB, nullable=False)  # List of steps
    tools_used = Column(ARRAY(String), nullable=False)

    # Metrics
    success = Column(Boolean, default=True, nullable=False)
    execution_time_minutes = Column(Integer, nullable=True)
    complexity_score = Column(Float, nullable=True)  # 0.0 - 1.0

    # Reuse Tracking
    reuse_count = Column(Integer, default=0, nullable=False)
    success_count = Column(Integer, default=0, nullable=False)

    # Embedding (für Similarity Search)
    # Wird via pgvector extension genutzt (optional)
    # embedding = Column(Vector(1536), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    last_reused_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Case {self.id} - {self.problem_description[:50]}...>"

    @property
    def success_rate(self) -> float:
        """Success rate (0.0 - 1.0)"""
        if self.reuse_count == 0:
            return 1.0  # Initial case
        return self.success_count / self.reuse_count

    def increment_reuse(self, success: bool):
        """Increment reuse counter"""
        self.reuse_count += 1
        if success:
            self.success_count += 1
        self.last_reused_at = func.now()

"""
CE365 License Server - Database Models
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class License(Base):
    """Lizenz-Datenbank Model"""
    __tablename__ = "licenses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(255), unique=True, nullable=False, index=True)
    edition = Column(String(50), nullable=False, default="pro")  # "community", "pro"
    customer_name = Column(String(255), nullable=False)
    customer_email = Column(String(255), default="")
    max_seats = Column(Integer, default=1)
    expires_at = Column(DateTime, nullable=True)  # None = never
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, default="")


class Session(Base):
    """Aktive Sessions Model"""
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    license_key = Column(String(255), nullable=False, index=True)
    session_token = Column(String(255), unique=True, nullable=False)
    system_fingerprint = Column(String(255), default="")
    started_at = Column(DateTime, default=datetime.utcnow)
    last_heartbeat = Column(DateTime, default=datetime.utcnow)
    released_at = Column(DateTime, nullable=True)

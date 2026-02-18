"""
CE365 License Server - Configuration
"""

import os
from pathlib import Path

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./license.db")

# HMAC Secret für Session-Token
SESSION_SECRET = os.getenv("SESSION_SECRET", "change-me-in-production")

# Session Timeout (Minuten)
SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "10"))

# Heartbeat Interval (Minuten)
HEARTBEAT_INTERVAL_MINUTES = int(os.getenv("HEARTBEAT_INTERVAL_MINUTES", "5"))

# Server
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "9000"))

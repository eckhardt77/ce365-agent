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

# Admin API Key (für CRUD-Endpoints)
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "")

# Stripe
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRICE_ID_PRO = os.getenv("STRIPE_PRICE_ID_PRO", "")  # Pro Monthly Price ID
SITE_URL = os.getenv("SITE_URL", "https://agent.ce365.de")

# Server
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "9000"))

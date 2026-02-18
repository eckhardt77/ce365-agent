"""
CE365 License Server

FastAPI-basierter Lizenzserver mit Session-Management.
Deployed auf bestehendem VPS.

Endpoints:
- POST /api/license/validate — Lizenz prüfen
- POST /api/license/session/start — Session starten
- POST /api/license/session/heartbeat — Heartbeat senden
- POST /api/license/session/release — Session freigeben
"""

import hashlib
import hmac
import uuid
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from models import Base, License, Session as SessionModel
from config import DATABASE_URL, SESSION_SECRET, SESSION_TIMEOUT_MINUTES


# Database Setup
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/Shutdown"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="CE365 License Server",
    version="1.0.0",
    lifespan=lifespan,
)


# === Request/Response Models ===

class ValidateRequest(BaseModel):
    license_key: str
    system_fingerprint: str = ""


class ValidateResponse(BaseModel):
    valid: bool
    edition: str = ""
    expires_at: str = "never"
    max_seats: int = 0
    customer_name: str = ""
    error: str = ""


class SessionStartRequest(BaseModel):
    license_key: str
    system_fingerprint: str = ""


class SessionStartResponse(BaseModel):
    success: bool
    session_token: str = ""
    error: str = ""


class HeartbeatRequest(BaseModel):
    session_token: str


class HeartbeatResponse(BaseModel):
    success: bool
    error: str = ""


class SessionReleaseRequest(BaseModel):
    session_token: str


class SessionReleaseResponse(BaseModel):
    success: bool
    error: str = ""


# === Helper ===

def generate_session_token(license_key: str) -> str:
    """Generiert einen sicheren Session-Token"""
    raw = f"{license_key}:{uuid.uuid4().hex}:{datetime.utcnow().isoformat()}"
    return hmac.new(
        SESSION_SECRET.encode(),
        raw.encode(),
        hashlib.sha256,
    ).hexdigest()


async def cleanup_expired_sessions(db: AsyncSession, license_key: str):
    """Bereinigt abgelaufene Sessions (Heartbeat > Timeout)"""
    cutoff = datetime.utcnow() - timedelta(minutes=SESSION_TIMEOUT_MINUTES)
    result = await db.execute(
        select(SessionModel).where(
            and_(
                SessionModel.license_key == license_key,
                SessionModel.released_at.is_(None),
                SessionModel.last_heartbeat < cutoff,
            )
        )
    )
    for session in result.scalars().all():
        session.released_at = datetime.utcnow()
    await db.commit()


async def count_active_sessions(db: AsyncSession, license_key: str) -> int:
    """Zählt aktive Sessions für einen Lizenzschlüssel"""
    cutoff = datetime.utcnow() - timedelta(minutes=SESSION_TIMEOUT_MINUTES)
    result = await db.execute(
        select(SessionModel).where(
            and_(
                SessionModel.license_key == license_key,
                SessionModel.released_at.is_(None),
                SessionModel.last_heartbeat >= cutoff,
            )
        )
    )
    return len(result.scalars().all())


# === Endpoints ===

@app.post("/api/license/validate", response_model=ValidateResponse)
async def validate_license(request: ValidateRequest):
    """Lizenz validieren"""
    async with async_session() as db:
        result = await db.execute(
            select(License).where(License.key == request.license_key)
        )
        license = result.scalar_one_or_none()

        if not license:
            return ValidateResponse(valid=False, error="Lizenzschlüssel nicht gefunden")

        if not license.active:
            return ValidateResponse(valid=False, error="Lizenz deaktiviert")

        # Ablaufdatum prüfen
        if license.expires_at and datetime.utcnow() > license.expires_at:
            return ValidateResponse(valid=False, error="Lizenz abgelaufen")

        expires_str = license.expires_at.isoformat() if license.expires_at else "never"

        return ValidateResponse(
            valid=True,
            edition=license.edition,
            expires_at=expires_str,
            max_seats=license.max_seats,
            customer_name=license.customer_name,
        )


@app.post("/api/license/session/start", response_model=SessionStartResponse)
async def start_session(request: SessionStartRequest):
    """Session starten (1 aktive Session pro Seat)"""
    async with async_session() as db:
        # Lizenz prüfen
        result = await db.execute(
            select(License).where(License.key == request.license_key)
        )
        license = result.scalar_one_or_none()

        if not license or not license.active:
            return SessionStartResponse(success=False, error="Ungültige Lizenz")

        if license.expires_at and datetime.utcnow() > license.expires_at:
            return SessionStartResponse(success=False, error="Lizenz abgelaufen")

        # Abgelaufene Sessions bereinigen
        await cleanup_expired_sessions(db, request.license_key)

        # Aktive Sessions zählen
        active_count = await count_active_sessions(db, request.license_key)

        if active_count >= license.max_seats:
            return SessionStartResponse(
                success=False,
                error=f"Alle {license.max_seats} Seat(s) belegt. "
                      "Ein anderer Techniker nutzt diese Lizenz bereits.",
            )

        # Neue Session erstellen
        token = generate_session_token(request.license_key)
        new_session = SessionModel(
            license_key=request.license_key,
            session_token=token,
            system_fingerprint=request.system_fingerprint,
        )
        db.add(new_session)
        await db.commit()

        return SessionStartResponse(success=True, session_token=token)


@app.post("/api/license/session/heartbeat", response_model=HeartbeatResponse)
async def session_heartbeat(request: HeartbeatRequest):
    """Session-Heartbeat (alle 5 Minuten)"""
    async with async_session() as db:
        result = await db.execute(
            select(SessionModel).where(
                and_(
                    SessionModel.session_token == request.session_token,
                    SessionModel.released_at.is_(None),
                )
            )
        )
        session = result.scalar_one_or_none()

        if not session:
            return HeartbeatResponse(success=False, error="Session nicht gefunden oder abgelaufen")

        session.last_heartbeat = datetime.utcnow()
        await db.commit()

        return HeartbeatResponse(success=True)


@app.post("/api/license/session/release", response_model=SessionReleaseResponse)
async def release_session(request: SessionReleaseRequest):
    """Session freigeben"""
    async with async_session() as db:
        result = await db.execute(
            select(SessionModel).where(
                and_(
                    SessionModel.session_token == request.session_token,
                    SessionModel.released_at.is_(None),
                )
            )
        )
        session = result.scalar_one_or_none()

        if not session:
            return SessionReleaseResponse(success=False, error="Session nicht gefunden")

        session.released_at = datetime.utcnow()
        await db.commit()

        return SessionReleaseResponse(success=True)


@app.get("/health")
async def health():
    """Health Check"""
    return {"status": "ok", "service": "CE365 License Server"}


if __name__ == "__main__":
    import uvicorn
    from config import HOST, PORT
    uvicorn.run(app, host=HOST, port=PORT)

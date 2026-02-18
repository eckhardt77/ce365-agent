"""
CE365 License Server

FastAPI-basierter Lizenzserver mit Session-Management + Admin-API + Stripe.

Endpoints:
- POST /api/license/validate — Lizenz prüfen
- POST /api/license/session/start — Session starten
- POST /api/license/session/heartbeat — Heartbeat senden
- POST /api/license/session/release — Session freigeben
- POST /api/admin/license/create — Lizenz erstellen (Admin)
- GET  /api/admin/license/list — Lizenzen auflisten (Admin)
- PATCH /api/admin/license/{key}/deactivate — Lizenz deaktivieren (Admin)
- POST /api/stripe/create-checkout — Stripe Checkout Session erstellen
- POST /api/stripe/webhook — Stripe Webhook (nach Bezahlung)
"""

import hashlib
import hmac
import secrets
import string
import uuid
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from models import Base, License, Session as SessionModel
from config import (
    DATABASE_URL, SESSION_SECRET, SESSION_TIMEOUT_MINUTES,
    ADMIN_API_KEY, STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET,
    STRIPE_PRICE_ID_PRO, SITE_URL,
)


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
    version="1.1.0",
    lifespan=lifespan,
)

# CORS für Website
app.add_middleware(
    CORSMiddleware,
    allow_origins=[SITE_URL, "https://agent.ce365.de"],
    allow_methods=["*"],
    allow_headers=["*"],
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
    return {"status": "ok", "service": "CE365 License Server", "version": "1.1.0"}


# === Admin Helper ===

def verify_admin_key(x_admin_key: str = Header(default="")):
    """Admin-API-Key prüfen"""
    if not ADMIN_API_KEY:
        raise HTTPException(status_code=500, detail="ADMIN_API_KEY nicht konfiguriert")
    if not hmac.compare_digest(x_admin_key, ADMIN_API_KEY):
        raise HTTPException(status_code=403, detail="Ungültiger Admin-Key")


def generate_license_key() -> str:
    """Generiert einen Lizenzschlüssel: CE365-PRO-XXXX-XXXX-XXXX"""
    chars = string.ascii_uppercase + string.digits
    parts = ["".join(secrets.choice(chars) for _ in range(4)) for _ in range(3)]
    return f"CE365-PRO-{parts[0]}-{parts[1]}-{parts[2]}"


# === Admin API Models ===

class AdminCreateLicenseRequest(BaseModel):
    customer_name: str
    customer_email: str = ""
    edition: str = "pro"
    max_seats: int = 1
    expires_in_days: int = 365
    notes: str = ""


class AdminLicenseResponse(BaseModel):
    key: str
    edition: str
    customer_name: str
    customer_email: str
    max_seats: int
    expires_at: Optional[str]
    active: bool
    created_at: str


# === Admin Endpoints ===

@app.post("/api/admin/license/create", response_model=AdminLicenseResponse)
async def admin_create_license(
    request: AdminCreateLicenseRequest,
    x_admin_key: str = Header(default=""),
):
    """Neue Lizenz erstellen (Admin)"""
    verify_admin_key(x_admin_key)

    license_key = generate_license_key()
    expires_at = datetime.utcnow() + timedelta(days=request.expires_in_days)

    async with async_session() as db:
        new_license = License(
            key=license_key,
            edition=request.edition,
            customer_name=request.customer_name,
            customer_email=request.customer_email,
            max_seats=request.max_seats,
            expires_at=expires_at,
            notes=request.notes,
        )
        db.add(new_license)
        await db.commit()
        await db.refresh(new_license)

        return AdminLicenseResponse(
            key=new_license.key,
            edition=new_license.edition,
            customer_name=new_license.customer_name,
            customer_email=new_license.customer_email,
            max_seats=new_license.max_seats,
            expires_at=expires_at.isoformat(),
            active=True,
            created_at=new_license.created_at.isoformat(),
        )


@app.get("/api/admin/license/list")
async def admin_list_licenses(
    x_admin_key: str = Header(default=""),
):
    """Alle Lizenzen auflisten (Admin)"""
    verify_admin_key(x_admin_key)

    async with async_session() as db:
        result = await db.execute(select(License).order_by(License.created_at.desc()))
        licenses = result.scalars().all()

        return [
            AdminLicenseResponse(
                key=lic.key,
                edition=lic.edition,
                customer_name=lic.customer_name,
                customer_email=lic.customer_email,
                max_seats=lic.max_seats,
                expires_at=lic.expires_at.isoformat() if lic.expires_at else None,
                active=lic.active,
                created_at=lic.created_at.isoformat(),
            )
            for lic in licenses
        ]


@app.patch("/api/admin/license/{key}/deactivate")
async def admin_deactivate_license(
    key: str,
    x_admin_key: str = Header(default=""),
):
    """Lizenz deaktivieren (Admin)"""
    verify_admin_key(x_admin_key)

    async with async_session() as db:
        result = await db.execute(select(License).where(License.key == key))
        license = result.scalar_one_or_none()

        if not license:
            raise HTTPException(status_code=404, detail="Lizenz nicht gefunden")

        license.active = False
        await db.commit()

        return {"success": True, "key": key, "active": False}


# === Stripe Integration ===

@app.post("/api/stripe/create-checkout")
async def create_checkout_session(
    seats: int = 1,
):
    """Stripe Checkout Session erstellen"""
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Stripe nicht konfiguriert")

    import stripe
    stripe.api_key = STRIPE_SECRET_KEY

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price": STRIPE_PRICE_ID_PRO,
                "quantity": seats,
            }],
            mode="subscription",
            success_url=f"{SITE_URL}/danke?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{SITE_URL}/#pricing",
            metadata={
                "seats": str(seats),
            },
        )
        return {"checkout_url": session.url}
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/stripe/webhook")
async def stripe_webhook(request: Request):
    """Stripe Webhook — erstellt Lizenz nach erfolgreicher Bezahlung"""
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="Webhook Secret nicht konfiguriert")

    import stripe
    stripe.api_key = STRIPE_SECRET_KEY

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        raise HTTPException(status_code=400, detail="Ungültige Signatur")

    if event["type"] == "checkout.session.completed":
        session_data = event["data"]["object"]
        customer_email = session_data.get("customer_details", {}).get("email", "")
        customer_name = session_data.get("customer_details", {}).get("name", customer_email)
        seats = int(session_data.get("metadata", {}).get("seats", "1"))
        stripe_customer_id = session_data.get("customer", "")
        stripe_subscription_id = session_data.get("subscription", "")

        # Neue Lizenz erstellen
        license_key = generate_license_key()
        expires_at = datetime.utcnow() + timedelta(days=365)

        async with async_session() as db:
            new_license = License(
                key=license_key,
                edition="pro",
                customer_name=customer_name,
                customer_email=customer_email,
                max_seats=seats,
                expires_at=expires_at,
                notes=f"Stripe: {stripe_customer_id} / {stripe_subscription_id}",
            )
            db.add(new_license)
            await db.commit()

        # TODO: E-Mail mit Lizenzschlüssel an Kunden senden
        print(f"[STRIPE] Neue Lizenz erstellt: {license_key} für {customer_email}")

    return {"received": True}


# === Checkout Status (für Thank-You-Seite) ===

@app.get("/api/stripe/checkout-status")
async def checkout_status(session_id: str):
    """Checkout-Status abrufen (für Thank-You-Seite)"""
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Stripe nicht konfiguriert")

    import stripe
    stripe.api_key = STRIPE_SECRET_KEY

    try:
        session = stripe.checkout.Session.retrieve(session_id)
        customer_email = session.get("customer_details", {}).get("email", "")

        # Lizenz anhand der E-Mail finden
        async with async_session() as db:
            result = await db.execute(
                select(License)
                .where(License.customer_email == customer_email)
                .order_by(License.created_at.desc())
            )
            license = result.scalars().first()

            if license:
                return {
                    "status": "complete",
                    "license_key": license.key,
                    "customer_email": customer_email,
                    "expires_at": license.expires_at.isoformat() if license.expires_at else None,
                }

        return {"status": "pending", "customer_email": customer_email}

    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    from config import HOST, PORT
    uvicorn.run(app, host=HOST, port=PORT)

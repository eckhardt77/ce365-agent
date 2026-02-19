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
- POST /api/newsletter/subscribe — Newsletter-Anmeldung (Brevo)
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
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from models import Base, License, Session as SessionModel
import httpx

from config import (
    DATABASE_URL, SESSION_SECRET, SESSION_TIMEOUT_MINUTES,
    ADMIN_API_KEY, STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET,
    STRIPE_PRICE_ID_PRO, SITE_URL, BREVO_API_KEY, BREVO_LIST_ID,
    RELEASES_DIR, LATEST_VERSION,
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


class AdminEditLicenseRequest(BaseModel):
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    max_seats: Optional[int] = None
    expires_in_days: Optional[int] = None
    notes: Optional[str] = None


class AdminLicenseResponse(BaseModel):
    key: str
    edition: str
    customer_name: str
    customer_email: str
    max_seats: int
    expires_at: Optional[str]
    active: bool
    created_at: str
    notes: str = ""
    active_sessions: int = 0


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
    search: str = "",
):
    """Alle Lizenzen auflisten (Admin), optional mit Suche"""
    verify_admin_key(x_admin_key)

    async with async_session() as db:
        query = select(License).order_by(License.created_at.desc())

        if search:
            search_term = f"%{search}%"
            query = select(License).where(
                License.key.ilike(search_term)
                | License.customer_name.ilike(search_term)
                | License.customer_email.ilike(search_term)
            ).order_by(License.created_at.desc())

        result = await db.execute(query)
        licenses = result.scalars().all()

        response = []
        for lic in licenses:
            active_count = await count_active_sessions(db, lic.key)
            response.append(AdminLicenseResponse(
                key=lic.key,
                edition=lic.edition,
                customer_name=lic.customer_name,
                customer_email=lic.customer_email,
                max_seats=lic.max_seats,
                expires_at=lic.expires_at.isoformat() if lic.expires_at else None,
                active=lic.active,
                created_at=lic.created_at.isoformat(),
                notes=lic.notes or "",
                active_sessions=active_count,
            ))
        return response


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


@app.patch("/api/admin/license/{key}/reactivate")
async def admin_reactivate_license(
    key: str,
    x_admin_key: str = Header(default=""),
):
    """Lizenz reaktivieren (Admin)"""
    verify_admin_key(x_admin_key)

    async with async_session() as db:
        result = await db.execute(select(License).where(License.key == key))
        license = result.scalar_one_or_none()

        if not license:
            raise HTTPException(status_code=404, detail="Lizenz nicht gefunden")

        license.active = True
        await db.commit()

        return {"success": True, "key": key, "active": True}


@app.patch("/api/admin/license/{key}/edit")
async def admin_edit_license(
    key: str,
    request: AdminEditLicenseRequest,
    x_admin_key: str = Header(default=""),
):
    """Lizenz bearbeiten (Admin)"""
    verify_admin_key(x_admin_key)

    async with async_session() as db:
        result = await db.execute(select(License).where(License.key == key))
        license = result.scalar_one_or_none()

        if not license:
            raise HTTPException(status_code=404, detail="Lizenz nicht gefunden")

        if request.customer_name is not None:
            license.customer_name = request.customer_name
        if request.customer_email is not None:
            license.customer_email = request.customer_email
        if request.max_seats is not None:
            license.max_seats = request.max_seats
        if request.expires_in_days is not None:
            license.expires_at = datetime.utcnow() + timedelta(days=request.expires_in_days)
        if request.notes is not None:
            license.notes = request.notes

        await db.commit()

        return {
            "success": True,
            "key": key,
            "customer_name": license.customer_name,
            "customer_email": license.customer_email,
            "max_seats": license.max_seats,
            "expires_at": license.expires_at.isoformat() if license.expires_at else None,
            "notes": license.notes,
        }


@app.get("/api/admin/sessions")
async def admin_list_sessions(
    x_admin_key: str = Header(default=""),
):
    """Alle aktiven Sessions auflisten (Admin)"""
    verify_admin_key(x_admin_key)

    cutoff = datetime.utcnow() - timedelta(minutes=SESSION_TIMEOUT_MINUTES)

    async with async_session() as db:
        result = await db.execute(
            select(SessionModel).where(
                and_(
                    SessionModel.released_at.is_(None),
                    SessionModel.last_heartbeat >= cutoff,
                )
            ).order_by(SessionModel.last_heartbeat.desc())
        )
        sessions = result.scalars().all()

        response = []
        for s in sessions:
            # Kundennamen zur Session holen
            lic_result = await db.execute(
                select(License).where(License.key == s.license_key)
            )
            lic = lic_result.scalar_one_or_none()

            response.append({
                "license_key": s.license_key,
                "customer_name": lic.customer_name if lic else "—",
                "customer_email": lic.customer_email if lic else "",
                "started_at": s.started_at.isoformat(),
                "last_heartbeat": s.last_heartbeat.isoformat(),
                "system_fingerprint": s.system_fingerprint or "",
            })

        return response


@app.delete("/api/admin/sessions/{license_key}")
async def admin_kill_sessions(
    license_key: str,
    x_admin_key: str = Header(default=""),
):
    """Alle Sessions einer Lizenz beenden (Admin)"""
    verify_admin_key(x_admin_key)

    async with async_session() as db:
        result = await db.execute(
            select(SessionModel).where(
                and_(
                    SessionModel.license_key == license_key,
                    SessionModel.released_at.is_(None),
                )
            )
        )
        sessions = result.scalars().all()
        count = len(sessions)

        for s in sessions:
            s.released_at = datetime.utcnow()

        await db.commit()

        return {"success": True, "killed": count}


@app.get("/api/admin/stats")
async def admin_stats(
    x_admin_key: str = Header(default=""),
):
    """Dashboard-Statistiken (Admin)"""
    verify_admin_key(x_admin_key)

    cutoff = datetime.utcnow() - timedelta(minutes=SESSION_TIMEOUT_MINUTES)

    async with async_session() as db:
        # Aktive Lizenzen
        result = await db.execute(select(License).where(License.active == True))
        active_licenses = result.scalars().all()

        # Inaktive Lizenzen
        result = await db.execute(select(License).where(License.active == False))
        inactive_count = len(result.scalars().all())

        # Seats gesamt
        total_seats = sum(lic.max_seats for lic in active_licenses)

        # MRR (Monthly Recurring Revenue)
        mrr = sum(lic.max_seats * 99.0 for lic in active_licenses)

        # Abgelaufene Lizenzen
        now = datetime.utcnow()
        expired_count = sum(
            1 for lic in active_licenses
            if lic.expires_at and now > lic.expires_at
        )

        # Aktive Sessions
        result = await db.execute(
            select(SessionModel).where(
                and_(
                    SessionModel.released_at.is_(None),
                    SessionModel.last_heartbeat >= cutoff,
                )
            )
        )
        active_sessions = len(result.scalars().all())

        # Alle Lizenzen gesamt
        result = await db.execute(select(License))
        total_count = len(result.scalars().all())

        return {
            "total_licenses": total_count,
            "active_licenses": len(active_licenses),
            "inactive_licenses": inactive_count,
            "expired_licenses": expired_count,
            "total_seats": total_seats,
            "active_sessions": active_sessions,
            "mrr": mrr,
        }


# === Stripe Integration ===

@app.post("/api/stripe/create-checkout")
async def create_checkout_session(
    seats: int = 1,
    lang: str = "de",
):
    """Stripe Checkout Session erstellen"""
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Stripe nicht konfiguriert")

    import stripe
    stripe.api_key = STRIPE_SECRET_KEY

    # Locale + Danke-Seite je nach Sprache
    if lang == "en":
        success_url = f"{SITE_URL}/en/danke?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{SITE_URL}/en/#pricing"
        locale = "en"
    else:
        success_url = f"{SITE_URL}/danke?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{SITE_URL}/#pricing"
        locale = "de"

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price": STRIPE_PRICE_ID_PRO,
                "quantity": seats,
            }],
            mode="subscription",
            locale=locale,
            success_url=success_url,
            cancel_url=cancel_url,
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

        # Kunde zu Brevo hinzufügen
        await add_to_brevo(customer_email, customer_name, "customer")
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


# === Brevo (Newsletter) ===

async def add_to_brevo(email: str, name: str = "", source: str = "website"):
    """Kontakt zu Brevo-Liste hinzufügen"""
    if not BREVO_API_KEY:
        print(f"[BREVO] Skipped (kein API-Key): {email}")
        return

    first_name = name.split(" ")[0] if name else ""
    last_name = " ".join(name.split(" ")[1:]) if name and " " in name else ""

    async with httpx.AsyncClient() as client:
        try:
            await client.post(
                "https://api.brevo.com/v3/contacts",
                headers={
                    "api-key": BREVO_API_KEY,
                    "Content-Type": "application/json",
                },
                json={
                    "email": email,
                    "attributes": {
                        "VORNAME": first_name,
                        "NACHNAME": last_name,
                        "SOURCE": source,
                    },
                    "listIds": [BREVO_LIST_ID],
                    "updateEnabled": True,
                },
            )
            print(f"[BREVO] Kontakt hinzugefügt: {email} (source={source})")
        except Exception as e:
            print(f"[BREVO] Fehler: {e}")


class NewsletterRequest(BaseModel):
    email: str
    name: str = ""


@app.post("/api/newsletter/subscribe")
async def newsletter_subscribe(request: NewsletterRequest):
    """Newsletter-Anmeldung"""
    if not request.email or "@" not in request.email:
        raise HTTPException(status_code=400, detail="Ungültige E-Mail-Adresse")

    await add_to_brevo(request.email, request.name, "newsletter")
    return {"success": True}


# ============================================================
# UPDATE / DOWNLOAD / RELEASE ENDPOINTS
# ============================================================

from fastapi import UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pathlib import Path
import json as json_module
import shutil


@app.get("/api/update/check")
async def update_check(version: str = "0.0.0", platform: str = ""):
    """
    Update-Check: Gibt zurück ob eine neue Version verfügbar ist.

    GET /api/update/check?version=1.9.0&platform=macos-arm64
    """
    from packaging.version import Version

    try:
        current = Version(version)
        latest = Version(LATEST_VERSION)
        update_available = latest > current
    except Exception:
        update_available = version != LATEST_VERSION

    # Download-URL zusammenbauen
    download_url = ""
    if update_available and platform:
        ext = ".exe" if platform.startswith("win") else ""
        filename = f"ce365-pro-{LATEST_VERSION}-{platform}{ext}"
        download_url = f"/api/update/download/{platform}"

    return {
        "latest_version": LATEST_VERSION,
        "current_version": version,
        "update_available": update_available,
        "download_url": download_url,
        "platform": platform,
    }


@app.get("/api/update/download/{platform}")
async def update_download(platform: str, license_key: str = ""):
    """
    Binary-Download für Pro-User.

    GET /api/update/download/macos-arm64?license_key=CE365-PRO-XXXX
    """
    # Lizenz prüfen
    if not license_key:
        raise HTTPException(status_code=401, detail="License key required")

    async with async_session() as session:
        result = await session.execute(
            select(License).where(
                and_(License.key == license_key, License.is_active == True)
            )
        )
        license_obj = result.scalar_one_or_none()

    if not license_obj:
        raise HTTPException(status_code=403, detail="Invalid or inactive license")

    # Binary finden
    ext = ".exe" if platform.startswith("win") else ""
    filename = f"ce365-pro-{LATEST_VERSION}-{platform}{ext}"
    filepath = RELEASES_DIR / LATEST_VERSION / filename

    if not filepath.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Release not found: {filename}"
        )

    # Download-Counter (optional, nicht-blockierend)
    try:
        stats_file = RELEASES_DIR / "download_stats.json"
        stats = {}
        if stats_file.exists():
            stats = json_module.loads(stats_file.read_text())
        key = f"{LATEST_VERSION}/{platform}"
        stats[key] = stats.get(key, 0) + 1
        stats_file.write_text(json_module.dumps(stats, indent=2))
    except Exception:
        pass

    return FileResponse(
        path=str(filepath),
        filename=filename,
        media_type="application/octet-stream",
    )


@app.post("/api/admin/release/upload")
async def release_upload(
    file: UploadFile = File(...),
    version: str = Form(...),
    platform: str = Form(...),
    x_admin_key: str = Header(None),
):
    """
    Release-Binary hochladen (Admin).

    POST /api/admin/release/upload
    Headers: X-Admin-Key: {admin_key}
    Body: multipart/form-data (file, version, platform)
    """
    if not ADMIN_API_KEY or x_admin_key != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid admin key")

    # Dateiname bestimmen
    ext = ".exe" if platform.startswith("win") else ""
    filename = f"ce365-pro-{version}-{platform}{ext}"

    # Verzeichnis erstellen
    release_dir = RELEASES_DIR / version
    release_dir.mkdir(parents=True, exist_ok=True)

    # Datei speichern
    filepath = release_dir / filename
    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    file_size = filepath.stat().st_size

    print(f"[RELEASE] Uploaded: {filename} ({file_size / 1024 / 1024:.1f} MB)")

    return {
        "success": True,
        "filename": filename,
        "version": version,
        "platform": platform,
        "size_bytes": file_size,
        "path": str(filepath),
    }


@app.get("/api/admin/releases")
async def list_releases(x_admin_key: str = Header(None)):
    """Alle Releases auflisten (Admin)"""
    if not ADMIN_API_KEY or x_admin_key != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid admin key")

    releases = []

    if RELEASES_DIR.exists():
        for version_dir in sorted(RELEASES_DIR.iterdir(), reverse=True):
            if version_dir.is_dir() and not version_dir.name.startswith("."):
                files = []
                for f in version_dir.iterdir():
                    if f.is_file():
                        files.append({
                            "filename": f.name,
                            "size_bytes": f.stat().st_size,
                            "modified": f.stat().st_mtime,
                        })
                releases.append({
                    "version": version_dir.name,
                    "files": files,
                })

    # Download-Statistiken laden
    stats = {}
    stats_file = RELEASES_DIR / "download_stats.json"
    if stats_file.exists():
        try:
            stats = json_module.loads(stats_file.read_text())
        except Exception:
            pass

    return {
        "latest_version": LATEST_VERSION,
        "releases": releases,
        "download_stats": stats,
    }


@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard():
    """Admin-Dashboard UI"""
    import os
    dashboard_path = os.path.join(os.path.dirname(__file__), "admin.html")
    with open(dashboard_path, "r") as f:
        return HTMLResponse(content=f.read())


if __name__ == "__main__":
    import uvicorn
    from config import HOST, PORT
    uvicorn.run(app, host=HOST, port=PORT)

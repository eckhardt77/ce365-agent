"""
TechCare Bot - FastAPI Backend
Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from api.config import settings
from api.middleware.logging import LoggingMiddleware
from api.middleware.rate_limit import RateLimitMiddleware
from api.routers import chat, users, tools, learning, auth, health
from api.models.database import init_db, close_db

# Logging Setup
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle: Startup & Shutdown"""
    # Startup
    logger.info("🚀 TechCare Bot API starting...")
    logger.info(f"Edition: {settings.edition.upper()}")
    logger.info(f"Environment: {settings.environment}")

    # Database initialisieren
    await init_db()
    logger.info("✓ Database initialized")

    # License validieren (falls nicht Free)
    if settings.edition != "free":
        from api.services.license_service import validate_license
        license_valid = await validate_license(settings.license_key)
        if not license_valid:
            logger.error("❌ Invalid license key!")
            # In production: raise Exception
        else:
            logger.info(f"✓ License validated: {settings.edition}")

    yield

    # Shutdown
    logger.info("🛑 TechCare Bot API shutting down...")
    await close_db()
    logger.info("✓ Database connections closed")


# FastAPI App
app = FastAPI(
    title="TechCare Bot API",
    version="1.0.0",
    description="AI-powered IT-Wartungsassistent",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.environment == "development" else None,
    redoc_url="/api/redoc" if settings.environment == "development" else None,
)


# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gzip Compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Custom Middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware)


# Exception Handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global Exception Handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "detail": str(exc) if settings.environment == "development" else "An error occurred"
        }
    )


# API Routers
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(tools.router, prefix="/api/tools", tags=["Tools"])
app.include_router(learning.router, prefix="/api/learning", tags=["Learning"])


# Root Endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "TechCare Bot API",
        "version": "1.0.0",
        "edition": settings.edition,
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development"
    )

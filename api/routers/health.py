"""
CE365 Agent - Health Router
Health Check Endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis.asyncio as aioredis

from api.models import get_db
from api.config import settings

router = APIRouter()


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Health Check Endpoint

    Prüft:
    - API erreichbar
    - Database verbindung
    - Redis verbindung
    """
    health_status = {
        "status": "healthy",
        "edition": settings.edition,
        "checks": {}
    }

    # Database Check
    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"

    # Redis Check
    try:
        redis_client = aioredis.from_url(settings.redis_url)
        await redis_client.ping()
        await redis_client.close()
        health_status["checks"]["redis"] = "healthy"
    except Exception as e:
        health_status["checks"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"

    return health_status


@router.get("/version")
async def version():
    """Version Info"""
    return {
        "version": "1.0.0",
        "edition": settings.edition,
        "environment": settings.environment
    }

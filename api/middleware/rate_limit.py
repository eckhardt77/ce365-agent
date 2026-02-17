"""
TechCare Bot - Rate Limit Middleware
Simple in-memory rate limiting
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import time
from collections import defaultdict
import logging

from api.config import settings

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple Rate Limiting Middleware

    Uses in-memory storage (für Production: Redis nutzen)
    """

    def __init__(self, app):
        super().__init__(app)
        self.requests = defaultdict(list)  # IP -> [timestamp, timestamp, ...]

    async def dispatch(self, request: Request, call_next):
        """Rate limit check"""
        if not settings.rate_limit_enabled:
            return await call_next(request)

        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        # Skip rate limiting für Health Check
        if request.url.path in ["/api/health", "/health"]:
            return await call_next(request)

        # Current time
        now = time.time()
        window_start = now - settings.rate_limit_window

        # Clean old requests
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if req_time > window_start
        ]

        # Check rate limit
        if len(self.requests[client_ip]) >= settings.rate_limit_requests:
            logger.warning(f"Rate limit exceeded for {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Max {settings.rate_limit_requests} requests per {settings.rate_limit_window} seconds"
            )

        # Add current request
        self.requests[client_ip].append(now)

        # Call next
        response = await call_next(request)

        # Add rate limit headers
        remaining = settings.rate_limit_requests - len(self.requests[client_ip])
        response.headers["X-RateLimit-Limit"] = str(settings.rate_limit_requests)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(int(now + settings.rate_limit_window))

        return response

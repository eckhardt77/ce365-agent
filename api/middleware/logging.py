"""
CE365 Agent - Logging Middleware
Request/Response Logging
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Logging Middleware für Request/Response"""

    async def dispatch(self, request: Request, call_next):
        """Log every request"""
        # Start time
        start_time = time.time()

        # Request Info
        method = request.method
        path = request.url.path
        client_host = request.client.host if request.client else "unknown"

        # Call next middleware/route
        try:
            response: Response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            logger.error(f"Request failed: {method} {path} - {str(e)}", exc_info=True)
            raise

        # Duration
        duration_ms = (time.time() - start_time) * 1000

        # Log
        log_message = f"{method} {path} - {status_code} - {duration_ms:.2f}ms - {client_host}"

        if status_code >= 500:
            logger.error(log_message)
        elif status_code >= 400:
            logger.warning(log_message)
        else:
            logger.info(log_message)

        # Add custom headers
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

        return response

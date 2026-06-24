import time
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

MAX_REQUESTS = 60   # per API key
WINDOW_SECS  = 60   # per minute


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Allows max 60 requests per minute per API key."""

    def __init__(self, app):
        super().__init__(app)
        self.requests: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request, call_next):
        api_key = request.headers.get("x-api-key", "anonymous")
        now     = time.time()

        # Drop timestamps outside the current window
        self.requests[api_key] = [
            t for t in self.requests[api_key] if now - t < WINDOW_SECS
        ]

        if len(self.requests[api_key]) >= MAX_REQUESTS:
            return JSONResponse(
                {"error": "Rate limit exceeded", "message": "Max 60 requests/minute."},
                status_code=429,
            )

        self.requests[api_key].append(now)
        return await call_next(request)

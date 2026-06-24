import os
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class AuthMiddleware(BaseHTTPMiddleware):
    """Rejects any request missing a valid x-api-key header."""

    async def dispatch(self, request, call_next):
        api_key = request.headers.get("x-api-key")
        valid_key = os.getenv("API_KEY", "dev-key-123")

        if not api_key or api_key != valid_key:
            return JSONResponse(
                {"error": "Unauthorized", "message": "Missing or invalid x-api-key header."},
                status_code=401,
            )

        return await call_next(request)

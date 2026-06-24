import json
import time
from starlette.middleware.base import BaseHTTPMiddleware


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs every request as structured JSON to stdout.
    Cloud Run automatically forwards stdout to Cloud Logging.
    """

    async def dispatch(self, request, call_next):
        start    = time.time()
        response = await call_next(request)
        duration = round((time.time() - start) * 1000, 2)

        log = {
            "severity": "INFO",
            "path":       request.url.path,
            "method":     request.method,
            "status":     response.status_code,
            "duration_ms": duration,
            # show only first 8 chars of key for security
            "api_key_prefix": (request.headers.get("x-api-key", "")[:8] + "..."),
        }

        print(json.dumps(log), flush=True)
        return response

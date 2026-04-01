import time
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from .config import settings
from .redis_cache import check_rate_limit

logger = logging.getLogger("uvicorn.error")

AI_PREFIXES = ("/api/v1/ai/",)
AI_EXACT_PATHS = {
    "/api/v1/challenges/daily",
    "/api/v1/challenges/submit",
    "/api/v1/challenges/ai-generate",
    "/api/v1/challenges/ai-check",
    "/api/v1/feihualing/start",
    "/api/v1/feihualing/submit",
}
AI_CONTAINS_PATHS = (
    "/ai-hint",
    "/ai-review",
)
WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
SKIP_PATHS = {"/health", "/", "/docs", "/openapi.json", "/redoc"}


def is_ai_request_path(path: str) -> bool:
    if any(path.startswith(prefix) for prefix in AI_PREFIXES):
        return True
    if path in AI_EXACT_PATHS:
        return True
    return any(part in path for part in AI_CONTAINS_PATHS)


class RateLimitMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if path in SKIP_PATHS or path.startswith("/uploads"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        auth = request.headers.get("authorization", "")
        identifier = auth.split()[-1][:16] if auth else client_ip

        is_ai = is_ai_request_path(path)
        is_write = request.method in WRITE_METHODS

        if is_ai:
            limit = settings.RATE_LIMIT_AI_PER_MINUTE
            bucket = f"ai:{identifier}"
        elif is_write:
            limit = settings.RATE_LIMIT_WRITE_PER_MINUTE
            bucket = f"write:{identifier}"
        else:
            limit = settings.RATE_LIMIT_PER_MINUTE
            bucket = f"read:{identifier}"

        allowed = await check_rate_limit(bucket, limit, window=60)
        if not allowed:
            logger.warning(f"速率限制触发: {bucket} on {path}")
            return JSONResponse(
                status_code=429,
                content={"detail": "请求过于频繁，请稍后再试"},
                headers={"Retry-After": "60"},
            )

        return await call_next(request)


class RequestTimingMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response: Response = await call_next(request)
        elapsed = (time.perf_counter() - start) * 1000
        response.headers["X-Response-Time"] = f"{elapsed:.1f}ms"
        
        threshold = 30000 if is_ai_request_path(request.url.path) else 2000
        if elapsed > threshold:
            logger.warning(f"慢请求: {request.method} {request.url.path} 耗时 {elapsed:.0f}ms")
        return response

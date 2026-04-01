import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from .api.v1.api import api_router
from .api.v1.endpoints.relay_ws import router as relay_ws_router
from .core.config import settings
from .core.redis_cache import init_redis, close_redis, flush_view_counts, get_redis
from .core.middleware import RateLimitMiddleware, RequestTimingMiddleware
from .core.database import engine
import traceback
import logging

logger = logging.getLogger("uvicorn.error")


class SSEAwareGZipMiddleware:
    """GZip 中间件：对 text/event-stream 响应跳过压缩，避免 SSE 事件被缓冲。"""

    def __init__(self, app: ASGIApp, minimum_size: int = 1000):
        self.app = app
        self.gzip = GZipMiddleware(app, minimum_size=minimum_size)

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.gzip(scope, receive, send)
            return

        is_sse = False

        async def send_wrapper(message):
            nonlocal is_sse
            if message["type"] == "http.response.start":
                headers = dict(
                    (k.lower(), v)
                    for k, v in (message.get("headers") or [])
                )
                if b"text/event-stream" in headers.get(b"content-type", b""):
                    is_sse = True
            if is_sse:
                await send(message)
            else:
                # 非 SSE 走原始 send，由外层 gzip 处理
                await send(message)

        if scope.get("path", "").endswith("-stream"):
            # 快速路径：已知流式端点直接绕过 GZip
            await self.app(scope, receive, send)
        else:
            await self.gzip(scope, receive, send)

_view_flush_task = None
_memory_worker_task = None
_memory_metrics_task = None


async def _periodic_flush_views():
    from .core.database import AsyncSessionLocal
    from .models.poem import Poem
    from sqlalchemy import select
    while True:
        await asyncio.sleep(30)
        try:
            pending = await flush_view_counts()
            if not pending:
                continue
            async with AsyncSessionLocal() as db:
                for poem_id, count in pending.items():
                    result = await db.execute(select(Poem).where(Poem.id == poem_id))
                    poem = result.scalar_one_or_none()
                    if poem:
                        poem.view_count = (poem.view_count or 0) + count
                await db.commit()
            logger.info(f"浏览量批量刷写: {len(pending)} 首诗词")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"浏览量刷写失败: {e}")


async def _periodic_log_memory_metrics():
    from .agent.memory import log_memory_metrics
    while True:
        await asyncio.sleep(60)
        try:
            await log_memory_metrics()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"记忆指标记录失败: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _view_flush_task, _memory_worker_task, _memory_metrics_task
    from .agent.memory import run_memory_extraction_worker
    await init_redis()
    _view_flush_task = asyncio.create_task(_periodic_flush_views())
    _memory_worker_task = asyncio.create_task(run_memory_extraction_worker())
    _memory_metrics_task = asyncio.create_task(_periodic_log_memory_metrics())
    logger.info("应用启动完成")
    yield
    if _memory_metrics_task:
        _memory_metrics_task.cancel()
        try:
            await _memory_metrics_task
        except asyncio.CancelledError:
            pass
    if _memory_worker_task:
        _memory_worker_task.cancel()
        try:
            await _memory_worker_task
        except asyncio.CancelledError:
            pass
    if _view_flush_task:
        _view_flush_task.cancel()
        try:
            await _view_flush_task
        except asyncio.CancelledError:
            pass
    try:
        pending = await flush_view_counts()
        if pending:
            from .core.database import AsyncSessionLocal
            from .models.poem import Poem
            from sqlalchemy import select
            async with AsyncSessionLocal() as db:
                for poem_id, count in pending.items():
                    result = await db.execute(select(Poem).where(Poem.id == poem_id))
                    poem = result.scalar_one_or_none()
                    if poem:
                        poem.view_count = (poem.view_count or 0) + count
                await db.commit()
    except Exception as e:
        logger.error(f"关闭时浏览量刷写失败: {e}")
    await close_redis()
    await engine.dispose()
    logger.info("应用已关闭")


app = FastAPI(title="青衿赋 API", version="1.0.0", lifespan=lifespan)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.method} {request.url}:\n{traceback.format_exc()}")
    return JSONResponse(status_code=500, content={"detail": "服务器内部错误"})

app.add_middleware(SSEAwareGZipMiddleware, minimum_size=1000)
app.add_middleware(RequestTimingMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

app.include_router(api_router, prefix="/api/v1")
app.include_router(relay_ws_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "青衿赋 API"}

@app.get("/health")
async def health():
    from .agent.memory import get_memory_extraction_metrics
    r = get_redis()
    redis_ok = False
    if r:
        try:
            await r.ping()
            redis_ok = True
        except Exception:
            pass
    memory_metrics = await get_memory_extraction_metrics()
    return {"status": "ok", "redis": redis_ok, "memory_extract": memory_metrics}

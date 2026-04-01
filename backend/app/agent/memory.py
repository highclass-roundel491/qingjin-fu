import asyncio
import hashlib
import json
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ..core.config import settings
from ..core.database import AsyncSessionLocal
from ..core.redis_cache import get_redis
from ..models.agent_memory import AgentMemory
from ..models.agent_memory_event import AgentMemoryEvent

logger = logging.getLogger("uvicorn.error")

MEMORY_CATEGORIES = {
    "preference": "用户偏好（喜欢的诗人/朝代/题材/风格）",
    "skill_level": "用户水平（初学/进阶/精通，擅长/薄弱领域）",
    "interaction": "交互习惯（喜欢详细还是简洁、偏好什么类型的解读）",
    "context": "上下文记忆（最近讨论的话题/诗人/诗词）",
    "goal": "学习目标（想学什么、准备什么考试、兴趣方向）",
}

MAX_MEMORIES_PER_USER = 30
MAX_INJECT_MEMORIES = 8

MEMORY_EVENT_STATUS_QUEUED = "queued"
MEMORY_EVENT_STATUS_PROCESSING = "processing"
MEMORY_EVENT_STATUS_RETRYING = "retrying"
MEMORY_EVENT_STATUS_DONE = "done"
MEMORY_EVENT_STATUS_FAILED = "failed"
MEMORY_EVENT_STATUS_DISCARDED = "discarded"

MEMORY_EVENT_QUEUE_KEY = "agent:memory:extract:queue"
MEMORY_EVENT_METRIC_COUNTERS_KEY = "agent:memory:extract:metrics:counters"
MEMORY_EVENT_METRIC_LATENCY_KEY = "agent:memory:extract:metrics:latency"

MEMORY_EXTRACT_BATCH_SIZE = getattr(settings, "AGENT_MEMORY_EXTRACT_BATCH_SIZE", 8)
MEMORY_EXTRACT_WORKER_CONCURRENCY = getattr(settings, "AGENT_MEMORY_EXTRACT_WORKER_CONCURRENCY", 4)
MEMORY_EXTRACT_TIMEOUT_SECONDS = getattr(settings, "AGENT_MEMORY_EXTRACT_TIMEOUT_SECONDS", 12.0)
MEMORY_EXTRACT_MAX_RETRIES = getattr(settings, "AGENT_MEMORY_EXTRACT_MAX_RETRIES", 3)
MEMORY_EXTRACT_RETRY_BASE_SECONDS = getattr(settings, "AGENT_MEMORY_EXTRACT_RETRY_BASE_SECONDS", 20)
MEMORY_EXTRACT_TRIGGER_MIN_MESSAGES = getattr(settings, "AGENT_MEMORY_EXTRACT_TRIGGER_MIN_MESSAGES", 3)
MEMORY_EXTRACT_TRIGGER_MIN_USER_CHARS = getattr(settings, "AGENT_MEMORY_EXTRACT_TRIGGER_MIN_USER_CHARS", 12)
MEMORY_EXTRACT_TRIGGER_COOLDOWN_SECONDS = getattr(settings, "AGENT_MEMORY_EXTRACT_TRIGGER_COOLDOWN_SECONDS", 90)
MEMORY_EXTRACT_MIN_IMPORTANCE = getattr(settings, "AGENT_MEMORY_EXTRACT_MIN_IMPORTANCE", 2)
MEMORY_EXTRACT_MAX_CONTENT_LENGTH = getattr(settings, "AGENT_MEMORY_EXTRACT_MAX_CONTENT_LENGTH", 120)
MEMORY_EXTRACT_MONITOR_WINDOW = getattr(settings, "AGENT_MEMORY_EXTRACT_MONITOR_WINDOW", 200)

MEMORY_EXTRACT_PROMPT = """请从以下对话中提取值得记住的用户信息。只提取**明确表达**的偏好或事实，不要推测。

可提取的类别：
- preference: 用户喜欢的诗人、朝代、题材、风格
- skill_level: 用户的诗词水平、擅长或薄弱领域
- interaction: 用户偏好的交互方式（详细/简洁、学术/通俗）
- context: 用户最近关注的话题或诗人
- goal: 用户的学习目标或兴趣方向

如果没有值得记住的信息，返回空列表。

返回严格JSON：
{
  "memories": [
    {
      "category": "preference",
      "key": "favorite_poet",
      "content": "用户表示最喜欢李白，尤其喜欢他的豪放风格",
      "importance": 3
    }
  ]
}

importance 取值 1-5：1=临时提及 2=一般偏好 3=明确表达 4=反复强调 5=核心特征

对话内容：
"""


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _sanitize_text(value: str, limit: int = 200) -> str:
    return str(value or "").strip()[:limit]


def _build_conversation_digest(conversation_messages: list[dict]) -> str:
    payload = []
    for msg in conversation_messages[-10:]:
        payload.append({
            "role": msg.get("role", ""),
            "content": _sanitize_text(msg.get("content", ""), 260),
        })
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def _get_last_user_message(conversation_messages: list[dict]) -> str:
    for msg in reversed(conversation_messages):
        if msg.get("role") == "user":
            return str(msg.get("content", "")).strip()
    return ""


async def _incr_metric(field: str, amount: int = 1):
    redis = get_redis()
    if not redis:
        return
    try:
        await redis.hincrby(MEMORY_EVENT_METRIC_COUNTERS_KEY, field, amount)
    except Exception:
        pass


async def _push_latency_metric(latency_ms: int):
    redis = get_redis()
    if not redis:
        return
    try:
        pipe = redis.pipeline()
        pipe.lpush(MEMORY_EVENT_METRIC_LATENCY_KEY, str(latency_ms))
        pipe.ltrim(MEMORY_EVENT_METRIC_LATENCY_KEY, 0, MEMORY_EXTRACT_MONITOR_WINDOW - 1)
        await pipe.execute()
    except Exception:
        pass


async def _mark_trigger_cooldown(user_id: int):
    redis = get_redis()
    if not redis:
        return
    try:
        key = f"agent:memory:trigger:cooldown:{user_id}"
        await redis.set(key, "1", ex=MEMORY_EXTRACT_TRIGGER_COOLDOWN_SECONDS)
    except Exception:
        pass


async def _is_trigger_cooling_down(user_id: int) -> bool:
    redis = get_redis()
    if not redis:
        return False
    try:
        key = f"agent:memory:trigger:cooldown:{user_id}"
        val = await redis.get(key)
        return val is not None
    except Exception:
        return False


def _has_value_signal(user_message: str) -> bool:
    text = user_message
    if len(text) >= 36:
        return True
    trigger_words = [
        "喜欢", "更想", "我想", "准备", "目标", "考试", "擅长", "不擅长",
        "希望", "偏好", "风格", "朝代", "诗人", "学习", "请你以后", "记住",
    ]
    return any(word in text for word in trigger_words)


async def should_enqueue_memory_extraction(user_id: int, conversation_messages: list[dict]) -> tuple[bool, str]:
    if not user_id:
        return False, "missing_user"
    if len(conversation_messages) < MEMORY_EXTRACT_TRIGGER_MIN_MESSAGES:
        return False, "below_min_messages"
    last_user_message = _get_last_user_message(conversation_messages)
    if len(last_user_message) < MEMORY_EXTRACT_TRIGGER_MIN_USER_CHARS:
        return False, "below_min_chars"
    if not _has_value_signal(last_user_message):
        return False, "low_value_signal"
    if await _is_trigger_cooling_down(user_id):
        return False, "cooldown"
    return True, "ok"


async def enqueue_memory_extraction_event(
    db: AsyncSession,
    user_id: int,
    conversation_messages: list[dict],
    source: str = "poem_chat",
) -> Optional[int]:
    allowed, reason = await should_enqueue_memory_extraction(user_id, conversation_messages)
    if not allowed:
        await _incr_metric("discarded", 1)
        logger.info(f"记忆抽取事件跳过: user={user_id}, reason={reason}")
        return None

    payload_messages = []
    for msg in conversation_messages[-10:]:
        payload_messages.append({
            "role": str(msg.get("role", "")),
            "content": _sanitize_text(msg.get("content", ""), 260),
        })
    dedup_seed = f"{user_id}:{_build_conversation_digest(payload_messages)}:{source}"
    dedup_key = hashlib.sha1(dedup_seed.encode("utf-8")).hexdigest()
    stmt = pg_insert(AgentMemoryEvent).values(
        user_id=user_id,
        source=source,
        dedup_key=dedup_key,
        payload={"messages": payload_messages},
        status=MEMORY_EVENT_STATUS_QUEUED,
        max_attempts=MEMORY_EXTRACT_MAX_RETRIES,
        queued_at=_now_utc(),
    ).on_conflict_do_nothing(
        index_elements=["dedup_key"],
    ).returning(AgentMemoryEvent.id)

    result = await db.execute(stmt)
    inserted_id = result.scalar_one_or_none()
    if inserted_id is None:
        existing = await db.execute(
            select(AgentMemoryEvent.id).where(AgentMemoryEvent.dedup_key == dedup_key).limit(1)
        )
        inserted_id = existing.scalar_one_or_none()
    await db.commit()
    if not inserted_id:
        return None
    await _mark_trigger_cooldown(user_id)
    await _enqueue_event_id(inserted_id)
    await _incr_metric("enqueued", 1)
    return inserted_id


async def _enqueue_event_id(event_id: int):
    redis = get_redis()
    if not redis:
        return
    try:
        await redis.rpush(MEMORY_EVENT_QUEUE_KEY, str(event_id))
    except Exception:
        pass


async def _pop_batch_event_ids(batch_size: int, wait_seconds: int = 2) -> list[int]:
    redis = get_redis()
    if not redis:
        return []
    ids: list[int] = []
    try:
        first = await redis.blpop(MEMORY_EVENT_QUEUE_KEY, timeout=wait_seconds)
        if first:
            _, value = first
            ids.append(int(value))
        remain = max(batch_size - len(ids), 0)
        if remain > 0:
            more = await redis.lpop(MEMORY_EVENT_QUEUE_KEY, remain)
            if isinstance(more, list):
                ids.extend(int(v) for v in more if v is not None)
            elif more is not None:
                ids.append(int(more))
    except Exception:
        return []
    return ids


async def get_memory_extraction_metrics(db: Optional[AsyncSession] = None) -> dict:
    redis = get_redis()
    counters = {
        "enqueued": 0,
        "processed": 0,
        "success": 0,
        "failed": 0,
        "discarded": 0,
    }
    latencies: list[int] = []
    queue_backlog = 0
    if redis:
        try:
            raw = await redis.hgetall(MEMORY_EVENT_METRIC_COUNTERS_KEY)
            for key in counters.keys():
                counters[key] = int(raw.get(key, 0) or 0)
        except Exception:
            pass
        try:
            latency_raw = await redis.lrange(MEMORY_EVENT_METRIC_LATENCY_KEY, 0, MEMORY_EXTRACT_MONITOR_WINDOW - 1)
            latencies = [int(v) for v in latency_raw if str(v).isdigit()]
        except Exception:
            latencies = []
        try:
            queue_backlog = int(await redis.llen(MEMORY_EVENT_QUEUE_KEY))
        except Exception:
            queue_backlog = 0

    if db is not None:
        try:
            pending_q = (
                select(func.count(AgentMemoryEvent.id))
                .where(AgentMemoryEvent.status.in_([MEMORY_EVENT_STATUS_QUEUED, MEMORY_EVENT_STATUS_RETRYING]))
            )
            pending_r = await db.execute(pending_q)
            queue_backlog = max(queue_backlog, int(pending_r.scalar() or 0))
        except Exception:
            pass

    sorted_latency = sorted(latencies)
    p95 = 0
    if sorted_latency:
        idx = max(int(len(sorted_latency) * 0.95) - 1, 0)
        p95 = sorted_latency[min(idx, len(sorted_latency) - 1)]
    processed = counters["processed"]
    success_rate = 0.0 if processed == 0 else (counters["success"] / processed)
    return {
        "enqueued": counters["enqueued"],
        "processed": processed,
        "success": counters["success"],
        "failed": counters["failed"],
        "discarded": counters["discarded"],
        "success_rate": round(success_rate, 4),
        "p95_latency_ms": p95,
        "queue_backlog": queue_backlog,
    }


async def log_memory_metrics():
    metrics = await get_memory_extraction_metrics()
    logger.info(
        "记忆抽取指标: "
        f"enqueued={metrics['enqueued']} "
        f"processed={metrics['processed']} "
        f"success={metrics['success']} "
        f"failed={metrics['failed']} "
        f"discarded={metrics['discarded']} "
        f"success_rate={metrics['success_rate']:.2%} "
        f"p95_ms={metrics['p95_latency_ms']} "
        f"backlog={metrics['queue_backlog']}"
    )


class AgentMemoryManager:

    @staticmethod
    async def load_memories(
        db: AsyncSession,
        user_id: int,
        categories: Optional[list[str]] = None,
        limit: int = MAX_INJECT_MEMORIES,
    ) -> list[dict]:
        query = (
            select(AgentMemory)
            .where(AgentMemory.user_id == user_id)
            .where(
                (AgentMemory.expires_at.is_(None)) |
                (AgentMemory.expires_at > func.now())
            )
        )
        if categories:
            query = query.where(AgentMemory.category.in_(categories))
        query = query.order_by(
            AgentMemory.importance.desc(),
            AgentMemory.access_count.desc(),
            AgentMemory.updated_at.desc(),
        ).limit(limit)

        result = await db.execute(query)
        memories = result.scalars().all()

        if memories:
            mem_ids = [m.id for m in memories]
            await db.execute(
                update(AgentMemory)
                .where(AgentMemory.id.in_(mem_ids))
                .values(access_count=AgentMemory.access_count + 1)
            )
            await db.commit()

        return [
            {
                "category": m.category,
                "key": m.memory_key,
                "content": m.content,
                "importance": m.importance,
            }
            for m in memories
        ]

    @staticmethod
    def format_memories_for_prompt(memories: list[dict]) -> str:
        if not memories:
            return ""
        lines = ["【用户记忆档案】"]
        for m in memories:
            cat_label = MEMORY_CATEGORIES.get(m["category"], m["category"])
            lines.append(f"- [{cat_label}] {m['content']}")
        lines.append("请根据以上记忆个性化你的回答，但不要直接提及「我记得你...」，自然融入即可。")
        return "\n".join(lines)

    @staticmethod
    async def save_memories(
        db: AsyncSession,
        user_id: int,
        memories: list[dict],
    ) -> int:
        memories = AgentMemoryManager._filter_memories(memories)
        if not memories:
            return 0
        saved = 0
        for mem in memories:
            category = mem.get("category", "preference")
            key = mem.get("key", "")
            content = _sanitize_text(mem.get("content", ""), MEMORY_EXTRACT_MAX_CONTENT_LENGTH)
            importance = min(max(int(mem.get("importance", 1)), 1), 5)

            if not key or not content:
                continue

            stmt = pg_insert(AgentMemory).values(
                user_id=user_id,
                category=category,
                memory_key=key,
                content=content,
                importance=importance,
            ).on_conflict_do_update(
                index_elements=["user_id", "memory_key"],
                set_={
                    "content": content,
                    "importance": importance,
                    "updated_at": func.now(),
                },
            )
            await db.execute(stmt)
            saved += 1

        if saved > 0:
            await db.commit()
            await AgentMemoryManager._enforce_limit(db, user_id)
            logger.info(f"Agent 记忆保存: user={user_id}, saved={saved}")

        return saved

    @staticmethod
    def _filter_memories(memories: list[dict]) -> list[dict]:
        filtered: list[dict] = []
        seen: set[str] = set()
        for mem in memories or []:
            if not isinstance(mem, dict):
                continue
            category = str(mem.get("category") or "").strip()
            key = str(mem.get("key") or "").strip()
            content = str(mem.get("content") or "").strip()
            try:
                importance = int(mem.get("importance", 1))
            except Exception:
                importance = 1
            if category not in MEMORY_CATEGORIES:
                continue
            if not key or not content:
                continue
            if len(content) < 6 or len(content) > MEMORY_EXTRACT_MAX_CONTENT_LENGTH:
                continue
            if importance < MEMORY_EXTRACT_MIN_IMPORTANCE:
                continue
            dedup = f"{category}:{key}:{content}"
            if dedup in seen:
                continue
            seen.add(dedup)
            filtered.append({
                "category": category,
                "key": key[:100],
                "content": content,
                "importance": min(max(importance, 1), 5),
            })
        return filtered

    @staticmethod
    async def _enforce_limit(db: AsyncSession, user_id: int):
        count_q = select(func.count(AgentMemory.id)).where(AgentMemory.user_id == user_id)
        count_r = await db.execute(count_q)
        total = count_r.scalar() or 0

        if total <= MAX_MEMORIES_PER_USER:
            return

        overflow = total - MAX_MEMORIES_PER_USER
        oldest_q = (
            select(AgentMemory.id)
            .where(AgentMemory.user_id == user_id)
            .order_by(
                AgentMemory.importance.asc(),
                AgentMemory.access_count.asc(),
                AgentMemory.updated_at.asc(),
            )
            .limit(overflow)
        )
        oldest_r = await db.execute(oldest_q)
        old_ids = [row[0] for row in oldest_r.all()]
        if old_ids:
            await db.execute(delete(AgentMemory).where(AgentMemory.id.in_(old_ids)))
            await db.commit()
            logger.info(f"Agent 记忆淘汰: user={user_id}, evicted={len(old_ids)}")

    @staticmethod
    async def extract_and_save(
        db: AsyncSession,
        user_id: int,
        engine,
        conversation_messages: list[dict],
    ) -> int:
        if len(conversation_messages) < 2:
            return 0

        from .prompts.identity import AI_IDENTITY_GUARD_LITE
        from ..services.ai_service import AIModelTier

        conv_text = ""
        for msg in conversation_messages[-10:]:
            role = "用户" if msg.get("role") == "user" else "翰林"
            conv_text += f"{role}：{msg.get('content', '')[:200]}\n"

        prompt = MEMORY_EXTRACT_PROMPT + conv_text

        try:
            result = await engine.run_agent_json(
                prompt=prompt,
                system_prompt=AI_IDENTITY_GUARD_LITE + "\n你是一个记忆提取器，只输出JSON，不要工具调用。",
                db=db,
                temperature=0.2,
                max_tokens=512,
                model_tier=AIModelTier.FLASH,
                tools=[],
                enable_react=False,
                enable_planner=False,
            )
            memories = result.get("memories", [])
            if not memories or not isinstance(memories, list):
                return 0
            return await AgentMemoryManager.save_memories(db, user_id, memories)
        except Exception as e:
            logger.warning(f"Agent 记忆提取失败: {e}")
            return 0


class AgentMemoryExtractionWorker:

    def __init__(self):
        self._stopped = False
        self._idle_rounds = 0

    def stop(self):
        self._stopped = True

    async def _rescue_retry_events(self):
        async with AsyncSessionLocal() as db:
            ids_r = await db.execute(
                select(AgentMemoryEvent.id)
                .where(
                    and_(
                        AgentMemoryEvent.status == MEMORY_EVENT_STATUS_RETRYING,
                        AgentMemoryEvent.next_retry_at.is_not(None),
                        AgentMemoryEvent.next_retry_at <= func.now(),
                    )
                )
                .order_by(AgentMemoryEvent.next_retry_at.asc())
                .limit(MEMORY_EXTRACT_BATCH_SIZE * 2)
            )
            ids = [row[0] for row in ids_r.all()]
            for event_id in ids:
                await _enqueue_event_id(event_id)

    async def _rescue_stale_processing(self):
        timeout_sec = max(int(MEMORY_EXTRACT_TIMEOUT_SECONDS * 2), 20)
        stale_before = _now_utc() - timedelta(seconds=timeout_sec)
        async with AsyncSessionLocal() as db:
            r = await db.execute(
                update(AgentMemoryEvent)
                .where(
                    and_(
                        AgentMemoryEvent.status == MEMORY_EVENT_STATUS_PROCESSING,
                        AgentMemoryEvent.started_at.is_not(None),
                        AgentMemoryEvent.started_at < stale_before,
                    )
                )
                .values(
                    status=MEMORY_EVENT_STATUS_RETRYING,
                    next_retry_at=_now_utc(),
                    updated_at=func.now(),
                    last_error="stale_processing",
                )
                .returning(AgentMemoryEvent.id)
            )
            await db.commit()
            ids = [row[0] for row in r.all()]
            for event_id in ids:
                await _enqueue_event_id(event_id)

    async def _fallback_scan_queued_ids(self) -> list[int]:
        async with AsyncSessionLocal() as db:
            queued_r = await db.execute(
                select(AgentMemoryEvent.id)
                .where(
                    and_(
                        AgentMemoryEvent.status.in_([MEMORY_EVENT_STATUS_QUEUED, MEMORY_EVENT_STATUS_RETRYING]),
                        (AgentMemoryEvent.next_retry_at.is_(None)) | (AgentMemoryEvent.next_retry_at <= func.now()),
                    )
                )
                .order_by(AgentMemoryEvent.created_at.asc())
                .limit(MEMORY_EXTRACT_BATCH_SIZE)
            )
            return [row[0] for row in queued_r.all()]

    async def _claim_event(self, db: AsyncSession, event_id: int) -> Optional[AgentMemoryEvent]:
        r = await db.execute(
            update(AgentMemoryEvent)
            .where(
                and_(
                    AgentMemoryEvent.id == event_id,
                    AgentMemoryEvent.status.in_([MEMORY_EVENT_STATUS_QUEUED, MEMORY_EVENT_STATUS_RETRYING]),
                    (AgentMemoryEvent.next_retry_at.is_(None)) | (AgentMemoryEvent.next_retry_at <= func.now()),
                )
            )
            .values(
                status=MEMORY_EVENT_STATUS_PROCESSING,
                started_at=_now_utc(),
                attempt_count=AgentMemoryEvent.attempt_count + 1,
                updated_at=func.now(),
                last_error=None,
            )
            .returning(AgentMemoryEvent)
        )
        row = r.first()
        if not row:
            return None
        return row[0]

    async def _mark_done(self, db: AsyncSession, event_id: int, latency_ms: int, extracted_count: int):
        await db.execute(
            update(AgentMemoryEvent)
            .where(AgentMemoryEvent.id == event_id)
            .values(
                status=MEMORY_EVENT_STATUS_DONE,
                extracted_count=extracted_count,
                finished_at=_now_utc(),
                latency_ms=latency_ms,
                updated_at=func.now(),
                next_retry_at=None,
            )
        )
        await db.commit()

    async def _mark_failed_or_retry(self, db: AsyncSession, event: AgentMemoryEvent, error_text: str):
        now = _now_utc()
        attempts = int(event.attempt_count or 0)
        max_attempts = int(event.max_attempts or MEMORY_EXTRACT_MAX_RETRIES)
        if attempts < max_attempts:
            delay_seconds = MEMORY_EXTRACT_RETRY_BASE_SECONDS * (2 ** max(0, attempts - 1))
            next_retry_at = now + timedelta(seconds=delay_seconds)
            await db.execute(
                update(AgentMemoryEvent)
                .where(AgentMemoryEvent.id == event.id)
                .values(
                    status=MEMORY_EVENT_STATUS_RETRYING,
                    next_retry_at=next_retry_at,
                    finished_at=now,
                    updated_at=func.now(),
                    last_error=_sanitize_text(error_text, 400),
                )
            )
            await db.commit()
            await _enqueue_event_id(event.id)
        else:
            await db.execute(
                update(AgentMemoryEvent)
                .where(AgentMemoryEvent.id == event.id)
                .values(
                    status=MEMORY_EVENT_STATUS_FAILED,
                    next_retry_at=None,
                    finished_at=now,
                    updated_at=func.now(),
                    last_error=_sanitize_text(error_text, 400),
                )
            )
            await db.commit()

    async def _process_one(self, event_id: int, engine) -> bool:
        started = time.perf_counter()
        async with AsyncSessionLocal() as db:
            event = await self._claim_event(db, event_id)
            if not event:
                return False
            try:
                payload = event.payload or {}
                messages = payload.get("messages", [])
                extracted_count = await asyncio.wait_for(
                    AgentMemoryManager.extract_and_save(db, event.user_id, engine, messages),
                    timeout=MEMORY_EXTRACT_TIMEOUT_SECONDS,
                )
                latency_ms = int((time.perf_counter() - started) * 1000)
                await self._mark_done(db, event.id, latency_ms, extracted_count)
                await _incr_metric("processed", 1)
                await _incr_metric("success", 1)
                await _push_latency_metric(latency_ms)
                return True
            except Exception as e:
                try:
                    await db.rollback()
                except Exception:
                    pass
                await self._mark_failed_or_retry(db, event, str(e))
                await _incr_metric("processed", 1)
                await _incr_metric("failed", 1)
                return False

    async def run(self):
        from ..services.ai_service import get_ai_service

        while not self._stopped:
            ai = get_ai_service()
            if not getattr(ai, "_configured", True):
                await asyncio.sleep(5)
                continue
            engine = getattr(ai, "agent", None)
            if engine is None:
                await asyncio.sleep(2)
                continue

            await self._rescue_retry_events()
            if self._idle_rounds % 15 == 0:
                await self._rescue_stale_processing()

            ids = await _pop_batch_event_ids(MEMORY_EXTRACT_BATCH_SIZE)
            if not ids:
                ids = await self._fallback_scan_queued_ids()
            unique_ids = []
            seen = set()
            for eid in ids:
                if eid in seen:
                    continue
                seen.add(eid)
                unique_ids.append(eid)

            if not unique_ids:
                self._idle_rounds += 1
                await asyncio.sleep(1.5)
                continue

            self._idle_rounds = 0
            sem = asyncio.Semaphore(max(1, MEMORY_EXTRACT_WORKER_CONCURRENCY))

            async def _run_with_limit(eid: int):
                async with sem:
                    await self._process_one(eid, engine)

            await asyncio.gather(*(_run_with_limit(eid) for eid in unique_ids))


async def run_memory_extraction_worker():
    worker = AgentMemoryExtractionWorker()
    await worker.run()

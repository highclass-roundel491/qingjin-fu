import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ....schemas.ai import (
    AIChatRequest, AIChatResponse,
    AIScoreRequest, AIScoreResponse,
    AICreationRequest, AICreationResponse,
    AICheckPoemRequest, AICheckPoemResponse,
    AIAnalyzePoemRequest, AIAnalyzePoemResponse,
    AIFeihuaRequest, AIFeihuaResponse,
    AIPoemContextRequest, AIPoemContextResponse,
    AIPoemChatRequest, AIPoemChatResponse,
)
from ....services.ai_service import get_ai_service, get_model_name
from ....services.poem_search import search_poems_by_keyword
from ....core.database import get_db
from ...deps import get_current_user, get_current_user_optional

router = APIRouter()


@router.post("/chat", response_model=AIChatResponse)
async def ai_chat(
    request: AIChatRequest,
    current_user=Depends(get_current_user),
):
    ai = get_ai_service()
    content = await ai.chat(
        prompt=request.prompt,
        system_prompt=request.system_prompt,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
    )
    return AIChatResponse(content=content, model=get_model_name())


@router.post("/score", response_model=AIScoreResponse)
async def ai_score(
    request: AIScoreRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    ai = get_ai_service()
    poem_context = None
    try:
        keywords = [w for w in request.correct_answers if len(w) <= 20]
        if keywords:
            poems = await search_poems_by_keyword(db, keywords[0], limit=1)
            if poems:
                poem = poems[0]
                poem_context = {
                    "title": poem.title,
                    "author": poem.author,
                    "dynasty": poem.dynasty,
                    "full_content": poem.content,
                }
    except Exception:
        pass
    try:
        result = await ai.agent_score_answer(
            question=request.question,
            correct_answers=request.correct_answers,
            user_answer=request.user_answer,
            db=db,
            poem_context=poem_context,
        )
        return AIScoreResponse(**result)
    except Exception:
        raise HTTPException(status_code=502, detail="AI评分服务暂时不可用")


@router.post("/creation", response_model=AICreationResponse)
async def ai_creation(
    request: AICreationRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    ai = get_ai_service()
    try:
        ref_dict = None
        if request.reference_poem:
            ref_dict = request.reference_poem.model_dump()
        result = await ai.agent_assist_creation(
            context=request.context,
            mode=request.mode,
            db=db,
            keywords=request.keywords,
            reference_poem=ref_dict,
            user_id=current_user.id,
        )
        return AICreationResponse(**result)
    except Exception:
        raise HTTPException(status_code=502, detail="AI创作服务暂时不可用")


@router.post("/check-poem", response_model=AICheckPoemResponse)
async def ai_check_poem(
    request: AICheckPoemRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    ai = get_ai_service()
    try:
        result = await ai.agent_check_poem(poem_text=request.poem_text, db=db)
        return AICheckPoemResponse(**result)
    except Exception:
        raise HTTPException(status_code=502, detail="AI格律检查服务暂时不可用")


@router.post("/analyze-poem", response_model=AIAnalyzePoemResponse)
async def ai_analyze_poem(
    request: AIAnalyzePoemRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    ai = get_ai_service()
    try:
        result = await ai.agent_analyze_poem(
            poem_text=request.poem_text,
            db=db,
        )
        return AIAnalyzePoemResponse(**result)
    except Exception:
        raise HTTPException(status_code=502, detail="AI赏析服务暂时不可用")


@router.post("/feihua-respond", response_model=AIFeihuaResponse)
async def ai_feihua_respond(
    request: AIFeihuaRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    ai = get_ai_service()
    try:
        result = await ai.agent_feihualing_respond(
            keyword=request.keyword,
            used_poems=request.used_poems,
            db=db,
        )
        return AIFeihuaResponse(**result)
    except Exception:
        raise HTTPException(status_code=502, detail="AI飞花令服务暂时不可用")


@router.post("/poem-context", response_model=AIPoemContextResponse)
async def ai_poem_context(
    request: AIPoemContextRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    if request.query_type == "free_qa" and not request.question:
        raise HTTPException(status_code=400, detail="自由问答模式需要提供问题")
    ai = get_ai_service()
    try:
        user_id = current_user.id if current_user else None
        result = await ai.agent_poem_context(
            title=request.title,
            author=request.author,
            dynasty=request.dynasty,
            content=request.content,
            query_type=request.query_type,
            db=db,
            genre=request.genre,
            category=request.category,
            question=request.question,
            user_id=user_id,
        )
        return AIPoemContextResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=502, detail="AI助学服务暂时不可用")


@router.post("/poem-chat", response_model=AIPoemChatResponse)
async def ai_poem_chat(
    request: AIPoemChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    ai = get_ai_service()
    try:
        history = [{"role": m.role, "content": m.content} for m in request.history]
        user_id = current_user.id if current_user else None
        result = await ai.agent_poem_chat(
            title=request.title,
            author=request.author,
            dynasty=request.dynasty,
            content=request.content,
            history=history,
            message=request.message,
            db=db,
            genre=request.genre,
            category=request.category,
            user_id=user_id,
        )
        return AIPoemChatResponse(**result)
    except Exception:
        raise HTTPException(status_code=502, detail="AI对话服务暂时不可用")


@router.post("/poem-chat-stream")
async def ai_poem_chat_stream(
    request: AIPoemChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    ai = get_ai_service()
    history = [{"role": m.role, "content": m.content} for m in request.history]
    user_id = current_user.id if current_user else None

    async def event_generator():
        try:
            async for chunk in ai.agent_poem_chat_stream(
                title=request.title,
                author=request.author,
                dynasty=request.dynasty,
                content=request.content,
                history=history,
                message=request.message,
                db=db,
                genre=request.genre,
                category=request.category,
                user_id=user_id,
            ):
                try:
                    parsed = json.loads(chunk)
                    event_type = parsed.get("type", "content")
                    if event_type in ("thinking", "tool_call", "memory"):
                        yield f"data: {chunk}\n\n"
                    else:
                        yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
                except (json.JSONDecodeError, TypeError):
                    yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception:
            yield f"data: {json.dumps({'error': 'AI对话服务暂时不可用'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


_SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


def _make_sse_generator(queue: asyncio.Queue, task_coro):
    async def generator():
        task = asyncio.create_task(task_coro)
        try:
            while True:
                event = await queue.get()
                if event is None:
                    break
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except asyncio.CancelledError:
            task.cancel()
        finally:
            if not task.done():
                await task
    return generator()


async def _run_with_progress(queue: asyncio.Queue, coro):
    try:
        result = await coro
        await queue.put({"type": "result", "data": result})
    except Exception:
        await queue.put({"type": "error", "content": "AI服务暂时不可用"})
    finally:
        await queue.put(None)


@router.post("/check-poem-stream")
async def ai_check_poem_stream(
    request: AICheckPoemRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    ai = get_ai_service()
    queue: asyncio.Queue = asyncio.Queue()

    async def on_progress(event):
        await queue.put(event)

    coro = _run_with_progress(queue, ai.agent_check_poem(
        poem_text=request.poem_text, db=db, on_progress=on_progress,
    ))
    return StreamingResponse(_make_sse_generator(queue, coro), media_type="text/event-stream", headers=_SSE_HEADERS)


@router.post("/analyze-poem-stream")
async def ai_analyze_poem_stream(
    request: AIAnalyzePoemRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    ai = get_ai_service()
    queue: asyncio.Queue = asyncio.Queue()

    async def on_progress(event):
        await queue.put(event)

    coro = _run_with_progress(queue, ai.agent_analyze_poem(
        poem_text=request.poem_text, db=db, on_progress=on_progress,
    ))
    return StreamingResponse(_make_sse_generator(queue, coro), media_type="text/event-stream", headers=_SSE_HEADERS)


@router.post("/creation-stream")
async def ai_creation_stream(
    request: AICreationRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    ai = get_ai_service()
    queue: asyncio.Queue = asyncio.Queue()

    async def on_progress(event):
        await queue.put(event)

    ref_dict = None
    if request.reference_poem:
        ref_dict = request.reference_poem.model_dump()
    coro = _run_with_progress(queue, ai.agent_assist_creation(
        context=request.context, mode=request.mode, db=db,
        keywords=request.keywords, reference_poem=ref_dict,
        user_id=current_user.id, on_progress=on_progress,
    ))
    return StreamingResponse(_make_sse_generator(queue, coro), media_type="text/event-stream", headers=_SSE_HEADERS)


@router.post("/poem-context-stream")
async def ai_poem_context_stream(
    request: AIPoemContextRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    if request.query_type == "free_qa" and not request.question:
        raise HTTPException(status_code=400, detail="自由问答模式需要提供问题")
    ai = get_ai_service()
    queue: asyncio.Queue = asyncio.Queue()

    async def on_progress(event):
        await queue.put(event)

    user_id = current_user.id if current_user else None
    coro = _run_with_progress(queue, ai.agent_poem_context(
        title=request.title, author=request.author, dynasty=request.dynasty,
        content=request.content, query_type=request.query_type, db=db,
        genre=request.genre, category=request.category,
        question=request.question, user_id=user_id, on_progress=on_progress,
    ))
    return StreamingResponse(_make_sse_generator(queue, coro), media_type="text/event-stream", headers=_SSE_HEADERS)

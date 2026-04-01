import asyncio
import logging
import random as _random
import re
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from datetime import date, datetime, timedelta
from typing import Optional
from app.core.database import get_db
from app.core.achievement_sync import sync_user_achievements
from app.models.challenge import DailyChallenge, ChallengeSubmission
from app.models.poem import Poem
from app.models.user import User
from app.schemas.challenge import (
    DailyChallengeResponse,
    ChallengeListResponse,
    ChallengeCreateRequest,
    ChallengeSubmitRequest,
    ChallengeSubmitResponse,
    ChallengeResponseItem,
    ChallengeResponseListResponse,
    ChallengeHistoryItem,
    ChallengeHistoryResponse,
    ChallengeDeleteResponse,
    ChallengeRankingItem,
    ChallengeRankingResponse,
    ChallengeAIGenerateRequest,
    ChallengeAIGenerateResponse,
    ChallengeAIHintRequest,
    ChallengeAIHintResponse,
    ChallengeAIReviewResponse,
    ChallengeAICheckRequest,
    ChallengeAICheckResponse,
    ChallengeAIExplainResponse,
    ChallengeAIExplainRecommendation,
)
from app.api.deps import get_current_user, get_current_user_optional
from app.core.levels import calculate_challenge_rewards, calculate_level
from app.services.ai_service import get_ai_service
from app.services.poem_search import search_poems_by_content
from app.agent.skills.challenge import (
    agent_score_challenge,
    agent_generate_challenge,
    agent_challenge_hint,
    agent_review_responses,
    agent_explain_challenge,
)

logger = logging.getLogger("uvicorn.error")

router = APIRouter()

AI_SCORE_TIMEOUT = 8

def _clamp(val, lo, hi):
    try:
        return max(lo, min(hi, int(val)))
    except (TypeError, ValueError):
        return lo

def _sanitize_ai_score(data: dict) -> dict:
    beauty = _clamp(data.get("beauty_score"), 0, 30)
    creativity = _clamp(data.get("creativity_score"), 0, 30)
    mood_s = _clamp(data.get("mood_score"), 0, 30)
    raw_total = _clamp(data.get("ai_score"), 0, 100)
    sub_total = beauty + creativity + mood_s
    ai_total = min(raw_total, sub_total + 10, 100)
    return {
        "ai_score": ai_total,
        "beauty_score": beauty,
        "creativity_score": creativity,
        "mood_score": mood_s,
        "feedback": str(data.get("feedback", ""))[:200],
        "highlight": str(data.get("highlight", ""))[:100],
        "is_original_match": bool(data.get("is_original_match", False)),
    }

def _parse_hint_level(value, fallback: int) -> int:
    if value is None or isinstance(value, bool):
        return _clamp(fallback, 1, 3)
    if isinstance(value, (int, float)):
        return _clamp(value, 1, 3)
    text = str(value).strip()
    match = re.search(r"\d+", text)
    if match:
        return _clamp(match.group(), 1, 3)
    mapping = {
        "一": 1,
        "二": 2,
        "三": 3,
        "第一层": 1,
        "第二层": 2,
        "第三层": 3,
        "一级": 1,
        "二级": 2,
        "三级": 3,
    }
    return _clamp(mapping.get(text, fallback), 1, 3)

def _parse_boolish(value, fallback: bool) -> bool:
    if value is None:
        return fallback
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y", "on", "是", "有", "可用", "继续"}:
        return True
    if text in {"false", "0", "no", "n", "off", "否", "无", "不可用", "结束"}:
        return False
    return fallback

def _sanitize_ai_hint(data: dict, requested_level: int) -> dict:
    payload = data if isinstance(data, dict) else {}
    hint_level = _parse_hint_level(payload.get("hint_level"), requested_level)
    hint_text = str(payload.get("hint_text") or payload.get("hint") or "").strip()
    if not hint_text:
        defaults = {
            1: "先从诗句描写的景物与季节意象入手思考。",
            2: "结合诗句常见题材与作者风格继续推敲。",
            3: "留意空缺字在句中的词性和语法位置。",
        }
        hint_text = defaults.get(hint_level, defaults[1])
    next_available = _parse_boolish(payload.get("next_available"), hint_level < 3)
    if hint_level >= 3:
        next_available = False
    return {
        "hint_text": hint_text[:80],
        "hint_level": hint_level,
        "next_available": next_available,
    }

async def _find_poem_context(db: AsyncSession, template: str) -> Optional[dict]:
    template_text = template.replace("__", "").replace("_", "")
    if len(template_text) < 3:
        return None
    try:
        poems = await search_poems_by_content(db, template_text[:20], limit=1)
    except Exception as e:
        logger.debug(f"poem_context search failed: {e}")
        return None
    if not poems:
        return None
    p = poems[0]
    return {
        "title": p.title,
        "author": p.author,
        "dynasty": p.dynasty,
        "full_content": p.content,
    }

async def _enrich_challenge(challenge: DailyChallenge, db: AsyncSession) -> DailyChallengeResponse:
    creator_name = None
    if challenge.creator_id:
        user_q = select(User.username).where(User.id == challenge.creator_id)
        r = await db.execute(user_q)
        creator_name = r.scalar_one_or_none()
    return DailyChallengeResponse(
        id=challenge.id,
        challenge_type=challenge.challenge_type or "fill_blank",
        creator_id=challenge.creator_id,
        creator_name=creator_name,
        is_daily=challenge.is_daily or False,
        date=challenge.date,
        sentence_template=challenge.sentence_template,
        sentence_template_2=challenge.sentence_template_2,
        blank_count=challenge.blank_count or 1,
        theme=challenge.theme,
        mood=challenge.mood,
        hint=challenge.hint,
        original_answer=challenge.original_answer,
        original_answer_2=challenge.original_answer_2,
        difficulty=challenge.difficulty or "medium",
        status=challenge.status or "active",
        response_count=challenge.response_count or 0,
        created_at=challenge.created_at,
    )

@router.get("/daily", response_model=DailyChallengeResponse)
async def get_daily_challenge(
    db: AsyncSession = Depends(get_db)
):
    today = date.today()
    query = select(DailyChallenge).where(
        and_(DailyChallenge.date == today, DailyChallenge.is_daily == True)
    )
    result = await db.execute(query)
    challenge = result.scalar_one_or_none()
    if challenge:
        return await _enrich_challenge(challenge, db)

    plaza_q = (
        select(DailyChallenge)
        .where(
            and_(
                DailyChallenge.status == "active",
                DailyChallenge.challenge_type == "fill_blank",
                DailyChallenge.is_daily == False,
                DailyChallenge.sentence_template_2.isnot(None),
            )
        )
        .order_by(DailyChallenge.response_count.desc(), DailyChallenge.created_at.desc())
        .limit(1)
    )
    top = (await db.execute(plaza_q)).scalar_one_or_none()
    if top:
        top.is_daily = True
        top.date = today
        await db.commit()
        await db.refresh(top)
        return await _enrich_challenge(top, db)

    try:
        poem_q = select(Poem).order_by(func.random()).limit(1)
        poem = (await db.execute(poem_q)).scalar_one_or_none()
        if not poem:
            raise HTTPException(status_code=404, detail="今日妙题尚未生成")
        ai = get_ai_service()
        data = None
        for _ in range(3):
            candidate = await ai.generate_challenge(
                poem_text=poem.content,
                poem_title=poem.title,
                poem_author=poem.author,
                poem_dynasty=poem.dynasty,
                difficulty="medium",
            )
            tmpl = candidate.get("sentence_template", "")
            if "_" in tmpl and candidate.get("original_answer"):
                data = candidate
                break
        if not data:
            raise HTTPException(status_code=404, detail="今日妙题尚未生成")
        t2 = data.get("sentence_template_2")
        new_daily = DailyChallenge(
            challenge_type="fill_blank",
            is_daily=True,
            date=today,
            sentence_template=data["sentence_template"],
            sentence_template_2=t2 if t2 and "_" in str(t2) else None,
            blank_count=1,
            original_answer=data.get("original_answer"),
            original_answer_2=data.get("original_answer_2"),
            theme=data.get("theme"),
            mood=data.get("mood"),
            hint=data.get("hint"),
            difficulty="medium",
            status="active",
            response_count=0,
        )
        db.add(new_daily)
        await db.commit()
        await db.refresh(new_daily)
        return await _enrich_challenge(new_daily, db)
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"AI生成今日妙题失败: {e}")
        raise HTTPException(status_code=404, detail="今日妙题尚未生成")

@router.get("/list", response_model=ChallengeListResponse)
async def list_challenges(
    challenge_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    base = select(DailyChallenge).where(DailyChallenge.status == "active")
    if challenge_type:
        base = base.where(DailyChallenge.challenge_type == challenge_type)
    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar() or 0
    q = base.order_by(DailyChallenge.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(q)).scalars().all()
    items = [await _enrich_challenge(c, db) for c in rows]
    return ChallengeListResponse(items=items, total=total, page=page, page_size=page_size)

@router.post("/create", response_model=DailyChallengeResponse)
async def create_challenge(
    req: ChallengeCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    challenge = DailyChallenge(
        challenge_type=req.challenge_type,
        creator_id=current_user.id,
        is_daily=False,
        sentence_template=req.sentence_template,
        sentence_template_2=req.sentence_template_2,
        blank_count=req.blank_count,
        original_answer=req.original_answer,
        original_answer_2=req.original_answer_2,
        theme=req.theme,
        mood=req.mood,
        hint=req.hint,
        difficulty=req.difficulty,
        status="active",
        response_count=0,
    )
    db.add(challenge)
    await db.commit()
    await db.refresh(challenge)
    return await _enrich_challenge(challenge, db)

@router.post("/submit", response_model=ChallengeSubmitResponse)
async def submit_challenge(
    submission: ChallengeSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    q = select(DailyChallenge).where(DailyChallenge.id == submission.challenge_id)
    challenge = (await db.execute(q)).scalar_one_or_none()
    if not challenge:
        raise HTTPException(status_code=404, detail="挑战不存在")

    if challenge.challenge_type == "fill_blank":
        bc = challenge.blank_count or 1
        if len(submission.answer) != bc:
            raise HTTPException(status_code=400, detail=f"请填入{bc}个字")
        if challenge.sentence_template_2:
            if not submission.answer_2:
                raise HTTPException(status_code=400, detail="请填写下联空位")
            if len(submission.answer_2) != bc:
                raise HTTPException(status_code=400, detail=f"请填入{bc}个字")

    scored = {
        "ai_score": 0, "beauty_score": 0, "creativity_score": 0,
        "mood_score": 0, "feedback": "", "highlight": "", "is_original_match": False,
    }
    try:
        ai = get_ai_service()
        raw = await asyncio.wait_for(
            agent_score_challenge(
                engine=ai.agent,
                sentence_template=challenge.sentence_template,
                sentence_template_2=challenge.sentence_template_2,
                user_answer=submission.answer,
                user_answer_2=submission.answer_2,
                challenge_type=challenge.challenge_type or "fill_blank",
                db=db,
                theme=challenge.theme,
                mood=challenge.mood,
            ),
            timeout=AI_SCORE_TIMEOUT + 5,
        )
        scored = _sanitize_ai_score(raw)
    except asyncio.TimeoutError:
        logger.warning("Agent评分超时，使用默认分数")
    except Exception as e:
        logger.warning(f"Agent评分调用失败，使用默认分数: {e}")

    ai_total = scored["ai_score"]
    beauty = scored["beauty_score"]
    creativity = scored["creativity_score"]
    mood_s = scored["mood_score"]
    feedback = scored["feedback"]
    highlight = scored["highlight"]
    is_original = scored["is_original_match"]

    rewards = calculate_challenge_rewards()
    base_exp = rewards["exp"]
    base_points = rewards["points"]
    if ai_total >= 80:
        exp_gained = int(base_exp * 1.5)
        points_gained = int(base_points * 1.5)
    elif ai_total >= 60:
        exp_gained = int(base_exp * 1.2)
        points_gained = int(base_points * 1.2)
    else:
        exp_gained = base_exp
        points_gained = base_points
    current_user.exp = (current_user.exp or 0)

    new_sub = ChallengeSubmission(
        user_id=current_user.id,
        challenge_id=submission.challenge_id,
        answer=submission.answer,
        answer_2=submission.answer_2,
        content=submission.content,
        ai_score=ai_total,
        ai_feedback=feedback,
        beauty_score=beauty,
        creativity_score=creativity,
        mood_score=mood_s,
        exp_gained=exp_gained,
        points_gained=points_gained,
    )
    db.add(new_sub)

    challenge.response_count = (challenge.response_count or 0) + 1
    current_user.exp += exp_gained
    current_user.points = (current_user.points or 0) + points_gained
    current_user.level = calculate_level(current_user.exp)
    await sync_user_achievements(db, current_user)
    await db.commit()
    await db.refresh(new_sub)

    tmpl = challenge.sentence_template
    if "__" in tmpl:
        completed_sentence = tmpl.replace("__", submission.answer, 1)
    elif "_" in tmpl:
        completed_sentence = tmpl.replace("_", submission.answer, 1)
    else:
        completed_sentence = submission.answer
    completed_sentence_2 = None
    if challenge.sentence_template_2 and submission.answer_2:
        tmpl2 = challenge.sentence_template_2
        if "__" in tmpl2:
            completed_sentence_2 = tmpl2.replace("__", submission.answer_2, 1)
        elif "_" in tmpl2:
            completed_sentence_2 = tmpl2.replace("_", submission.answer_2, 1)

    return ChallengeSubmitResponse(
        id=new_sub.id,
        completed_sentence=completed_sentence,
        completed_sentence_2=completed_sentence_2,
        exp_gained=exp_gained,
        points_gained=points_gained,
        ai_score=ai_total,
        beauty_score=beauty,
        creativity_score=creativity,
        mood_score=mood_s,
        ai_feedback=feedback or None,
        ai_highlight=highlight or None,
        is_original_match=is_original,
    )

@router.get("/history", response_model=ChallengeHistoryResponse)
async def get_challenge_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(ChallengeSubmission).where(
        ChallengeSubmission.user_id == current_user.id
    ).order_by(ChallengeSubmission.submitted_at.desc())

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    q = query.offset((page - 1) * page_size).limit(page_size)
    submissions = (await db.execute(q)).scalars().all()

    today = date.today()
    streak_days = 0
    check_date = today
    for _ in range(30):
        day_query = select(ChallengeSubmission).join(DailyChallenge).where(
            and_(
                ChallengeSubmission.user_id == current_user.id,
                DailyChallenge.date == check_date
            )
        )
        if (await db.execute(day_query)).scalars().first():
            streak_days += 1
            check_date -= timedelta(days=1)
        else:
            break

    items = []
    for s in submissions:
        ctype = "fill_blank"
        cq = select(DailyChallenge.challenge_type).where(DailyChallenge.id == s.challenge_id)
        ct = (await db.execute(cq)).scalar_one_or_none()
        if ct:
            ctype = ct
        items.append(ChallengeHistoryItem(
            id=s.id,
            challenge_id=s.challenge_id,
            challenge_type=ctype,
            answer=s.answer,
            answer_2=s.answer_2,
            content=s.content,
            exp_gained=s.exp_gained or 0,
            points_gained=s.points_gained or 0,
            ai_score=s.ai_score or 0,
            beauty_score=s.beauty_score or 0,
            creativity_score=s.creativity_score or 0,
            mood_score=s.mood_score or 0,
            submitted_at=s.submitted_at,
        ))

    return ChallengeHistoryResponse(
        items=items,
        total=total,
        streak_days=streak_days,
        page=page,
        page_size=page_size,
    )

@router.delete("/submissions/{submission_id}", response_model=ChallengeDeleteResponse)
async def delete_submission(
    submission_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    q = select(ChallengeSubmission).where(ChallengeSubmission.id == submission_id)
    submission = (await db.execute(q)).scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=404, detail="提交记录不存在")
    if submission.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能删除自己的提交记录")

    exp_to_deduct = submission.exp_gained or 0
    points_to_deduct = submission.points_gained or 0

    current_user.exp = max(0, (current_user.exp or 0) - exp_to_deduct)
    current_user.points = max(0, (current_user.points or 0) - points_to_deduct)
    current_user.level = calculate_level(current_user.exp)

    cq = select(DailyChallenge).where(DailyChallenge.id == submission.challenge_id)
    challenge = (await db.execute(cq)).scalar_one_or_none()
    if challenge:
        challenge.response_count = max(0, (challenge.response_count or 0) - 1)

    await db.delete(submission)
    await sync_user_achievements(db, current_user)
    await db.commit()

    return ChallengeDeleteResponse(
        id=submission_id,
        exp_deducted=exp_to_deduct,
        points_deducted=points_to_deduct,
        message="已删除提交记录，相应经验与积分已扣回"
    )


@router.delete("/{challenge_id}", response_model=ChallengeDeleteResponse)
async def delete_challenge(
    challenge_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    q = select(DailyChallenge).where(DailyChallenge.id == challenge_id)
    challenge = (await db.execute(q)).scalar_one_or_none()
    if not challenge:
        raise HTTPException(status_code=404, detail="题目不存在")
    if challenge.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能删除自己出的题目")
    if challenge.is_daily:
        raise HTTPException(status_code=403, detail="每日题目不可删除")

    subs = await db.execute(
        select(ChallengeSubmission).where(ChallengeSubmission.challenge_id == challenge_id)
    )
    total_exp = 0
    total_points = 0
    for sub in subs.scalars().all():
        total_exp += sub.exp_gained or 0
        total_points += sub.points_gained or 0
        user_q = select(User).where(User.id == sub.user_id)
        user = (await db.execute(user_q)).scalar_one_or_none()
        if user:
            user.exp = max(0, (user.exp or 0) - (sub.exp_gained or 0))
            user.points = max(0, (user.points or 0) - (sub.points_gained or 0))
            user.level = calculate_level(user.exp)
        await db.delete(sub)

    await db.delete(challenge)
    await db.commit()

    return ChallengeDeleteResponse(
        id=challenge_id,
        exp_deducted=total_exp,
        points_deducted=total_points,
        message="已删除题目及所有相关提交"
    )

@router.get("/rankings", response_model=ChallengeRankingResponse)
async def get_challenge_rankings(
    period: str = Query("all", pattern="^(today|week|all)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    base = select(
        ChallengeSubmission.user_id,
        func.count(ChallengeSubmission.id).label("sub_count"),
        func.sum(ChallengeSubmission.exp_gained).label("sum_exp"),
        func.sum(ChallengeSubmission.points_gained).label("sum_points"),
    )

    now = datetime.now()
    if period == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        base = base.where(ChallengeSubmission.submitted_at >= start)
    elif period == "week":
        start = now - timedelta(days=7)
        base = base.where(ChallengeSubmission.submitted_at >= start)

    base = base.group_by(ChallengeSubmission.user_id)
    total_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(total_q)).scalar() or 0

    ranked = base.order_by(func.sum(ChallengeSubmission.points_gained).desc()).offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(ranked)).all()

    items = []
    for i, r in enumerate(rows):
        user_q = select(User).where(User.id == r.user_id)
        user = (await db.execute(user_q)).scalar_one_or_none()
        if not user:
            continue
        items.append(ChallengeRankingItem(
            rank=(page - 1) * page_size + i + 1,
            user_id=r.user_id,
            username=user.username,
            nickname=user.nickname,
            avatar_url=user.avatar_url,
            total_submissions=r.sub_count or 0,
            total_exp=r.sum_exp or 0,
            total_points=r.sum_points or 0,
            level=calculate_level(user.exp or 0),
            exp=user.exp or 0,
        ))

    return ChallengeRankingResponse(items=items, total=total, period=period)

@router.get("/{challenge_id}", response_model=DailyChallengeResponse)
async def get_challenge_detail(
    challenge_id: int,
    db: AsyncSession = Depends(get_db)
):
    q = select(DailyChallenge).where(DailyChallenge.id == challenge_id)
    challenge = (await db.execute(q)).scalar_one_or_none()
    if not challenge:
        raise HTTPException(status_code=404, detail="挑战不存在")
    return await _enrich_challenge(challenge, db)

@router.get("/{challenge_id}/responses", response_model=ChallengeResponseListResponse)
async def get_challenge_responses(
    challenge_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    base = select(ChallengeSubmission).where(ChallengeSubmission.challenge_id == challenge_id)
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar() or 0
    q = base.order_by(ChallengeSubmission.submitted_at.desc()).offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(q)).scalars().all()

    items = []
    for s in rows:
        uname = None
        uq = select(User.username).where(User.id == s.user_id)
        uname = (await db.execute(uq)).scalar_one_or_none()
        items.append(ChallengeResponseItem(
            id=s.id,
            challenge_id=s.challenge_id,
            user_id=s.user_id,
            username=uname,
            answer=s.answer,
            answer_2=s.answer_2,
            content=s.content,
            likes_count=s.likes_count or 0,
            submitted_at=s.submitted_at,
        ))

    return ChallengeResponseListResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("/ai-generate", response_model=ChallengeAIGenerateResponse)
async def ai_generate_challenge(
    req: ChallengeAIGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    base = select(Poem)
    if req.dynasty:
        base = base.where(Poem.dynasty == req.dynasty)
    if req.theme:
        base = base.where(Poem.tags.contains(req.theme))

    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar() or 0
    if total == 0:
        count_all = (await db.execute(select(func.count()).select_from(Poem))).scalar() or 0
        if count_all == 0:
            raise HTTPException(status_code=404, detail="诗词库暂无数据，无法生成题目")
        offset = _random.randint(0, count_all - 1)
        result = await db.execute(select(Poem).offset(offset).limit(1))
        poem = result.scalar_one_or_none()
    else:
        offset = _random.randint(0, total - 1)
        result = await db.execute(base.offset(offset).limit(1))
        poem = result.scalar_one_or_none()
    if not poem:
        raise HTTPException(status_code=404, detail="诗词库暂无数据，无法生成题目")
    try:
        ai = get_ai_service()
        data = await agent_generate_challenge(
            engine=ai.agent,
            db=db,
            difficulty=req.difficulty,
            theme=req.theme,
            dynasty=req.dynasty,
        )
        tmpl = data.get("sentence_template", "")
        if "_" not in tmpl or not data.get("original_answer"):
            data = None
            for _ in range(2):
                candidate = await ai.generate_challenge(
                    poem_text=poem.content,
                    poem_title=poem.title,
                    poem_author=poem.author,
                    poem_dynasty=poem.dynasty,
                    difficulty=req.difficulty,
                )
                ct = candidate.get("sentence_template", "")
                if "_" in ct and candidate.get("original_answer"):
                    data = candidate
                    break
            if not data:
                raise ValueError("AI生成的题目格式不符")
        else:
            pass
        t2 = data.get("sentence_template_2")
        t2_valid = t2 and "_" in str(t2)
        return ChallengeAIGenerateResponse(
            sentence_template=data["sentence_template"],
            sentence_template_2=t2 if t2_valid else None,
            blank_count=1,
            original_answer=data["original_answer"],
            original_answer_2=data.get("original_answer_2"),
            theme=data.get("theme"),
            mood=data.get("mood"),
            hint=data.get("hint"),
            difficulty=data.get("difficulty", req.difficulty),
            poem_title=data.get("poem_title") or poem.title,
            poem_author=data.get("poem_author") or poem.author,
            poem_dynasty=data.get("poem_dynasty") or poem.dynasty,
        )
    except Exception:
        raise HTTPException(status_code=502, detail="AI出题服务暂时不可用")


@router.post("/{challenge_id}/ai-hint", response_model=ChallengeAIHintResponse)
async def ai_challenge_hint(
    challenge_id: int,
    req: ChallengeAIHintRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(DailyChallenge).where(DailyChallenge.id == challenge_id)
    challenge = (await db.execute(q)).scalar_one_or_none()
    if not challenge:
        raise HTTPException(status_code=404, detail="挑战不存在")
    try:
        ai = get_ai_service()
        data = await agent_challenge_hint(
            engine=ai.agent,
            sentence_template=challenge.sentence_template,
            hint_level=req.hint_level,
            db=db,
            theme=challenge.theme,
            mood=challenge.mood,
        )
        return ChallengeAIHintResponse(**_sanitize_ai_hint(data, req.hint_level))
    except Exception:
        logger.exception(f"ai_hint failed: challenge_id={challenge_id} hint_level={req.hint_level}")
        raise HTTPException(status_code=502, detail="AI提示服务暂时不可用")


@router.post("/{challenge_id}/ai-review", response_model=ChallengeAIReviewResponse)
async def ai_review_responses(
    challenge_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(DailyChallenge).where(DailyChallenge.id == challenge_id)
    challenge = (await db.execute(q)).scalar_one_or_none()
    if not challenge:
        raise HTTPException(status_code=404, detail="挑战不存在")
    sub_q = (
        select(ChallengeSubmission, User.username)
        .join(User, User.id == ChallengeSubmission.user_id, isouter=True)
        .where(ChallengeSubmission.challenge_id == challenge_id)
        .order_by(ChallengeSubmission.submitted_at.desc())
        .limit(10)
    )
    rows = (await db.execute(sub_q)).all()
    if len(rows) < 2:
        raise HTTPException(status_code=400, detail="至少需要2条作答才能进行赏析")
    answers = [
        {"answer": s.answer, "answer_2": s.answer_2, "username": uname}
        for s, uname in rows
    ]
    try:
        ai = get_ai_service()
        data = await agent_review_responses(
            engine=ai.agent,
            sentence_template=challenge.sentence_template,
            sentence_template_2=challenge.sentence_template_2,
            answers=answers,
            db=db,
            theme=challenge.theme,
            original_answer=challenge.original_answer,
            original_answer_2=challenge.original_answer_2,
        )
        return ChallengeAIReviewResponse(
            best_answer_index=data.get("best_answer_index", 0),
            best_reason=data.get("best_reason", ""),
            answer_tags=data.get("answer_tags", []),
            overall_review=data.get("overall_review", ""),
            diversity_note=data.get("diversity_note", ""),
        )
    except Exception:
        raise HTTPException(status_code=502, detail="AI赏析服务暂时不可用")


@router.post("/{challenge_id}/ai-explain", response_model=ChallengeAIExplainResponse)
async def ai_explain_challenge(
    challenge_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(DailyChallenge).where(DailyChallenge.id == challenge_id)
    challenge = (await db.execute(q)).scalar_one_or_none()
    if not challenge:
        raise HTTPException(status_code=404, detail="挑战不存在")

    sub_q = (
        select(ChallengeSubmission)
        .where(
            and_(
                ChallengeSubmission.challenge_id == challenge_id,
                ChallengeSubmission.user_id == current_user.id,
            )
        )
        .order_by(ChallengeSubmission.submitted_at.desc())
        .limit(1)
    )
    submission = (await db.execute(sub_q)).scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=400, detail="请先完成答题再查看解析")

    try:
        ai = get_ai_service()
        data = await agent_explain_challenge(
            engine=ai.agent,
            sentence_template=challenge.sentence_template,
            sentence_template_2=challenge.sentence_template_2,
            user_answer=submission.answer,
            user_answer_2=submission.answer_2,
            original_answer=challenge.original_answer,
            original_answer_2=challenge.original_answer_2,
            db=db,
            theme=challenge.theme,
        )
        recs = []
        for r in data.get("recommendations", [])[:3]:
            if isinstance(r, dict):
                recs.append(ChallengeAIExplainRecommendation(
                    title=str(r.get("title", "")),
                    author=str(r.get("author", "")),
                    reason=str(r.get("reason", "")),
                ))
        return ChallengeAIExplainResponse(
            poem_title=str(data.get("poem_title", "")),
            poem_author=str(data.get("poem_author", "")),
            poem_dynasty=str(data.get("poem_dynasty", "")),
            poem_content=str(data.get("poem_content", "")),
            appreciation=str(data.get("appreciation", ""))[:200],
            word_analysis=str(data.get("word_analysis", ""))[:150],
            comparison=str(data.get("comparison", ""))[:150],
            recommendations=recs,
        )
    except Exception:
        raise HTTPException(status_code=502, detail="翰林解析服务暂时不可用")


@router.post("/ai-check", response_model=ChallengeAICheckResponse)
async def ai_check_challenge(
    req: ChallengeAICheckRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        ai = get_ai_service()
        data = await ai.agent_check_challenge(
            sentence_template=req.sentence_template,
            db=db,
            sentence_template_2=req.sentence_template_2,
            user_answer=req.user_answer,
        )
        return ChallengeAICheckResponse(
            is_valid=data.get("is_valid", False),
            feedback=data.get("feedback", ""),
            suggestions=data.get("suggestions", []),
        )
    except Exception:
        raise HTTPException(status_code=502, detail="AI检查服务暂时不可用")

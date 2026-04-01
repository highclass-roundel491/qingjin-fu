from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from datetime import datetime, timedelta
from typing import Optional, List
import random
import json

from app.core.database import get_db
from app.core.achievement_sync import sync_user_achievements
from app.core.levels import calculate_level, calculate_timed_challenge_exp
from app.core.redis_cache import cache_get, cache_set
from app.models.timed_challenge import TimedChallengeSession, TimedChallengeAnswer
from app.models.poem import Poem
from app.models.user import User
from app.schemas.timed_challenge import (
    TimedChallengeStartRequest, TimedChallengeStartResponse,
    TimedAnswerRequest, TimedAnswerResponse,
    TimedChallengeEndRequest, TimedChallengeResult,
    TimedHistoryResponse, TimedHistoryItem,
    TimedRankingResponse,
    TimedQuestion, QuestionOption, TimedAnswerDetail
)
from app.api.deps import get_current_user

router = APIRouter()

DIFFICULTY_CONFIG = {
    "easy": {"time": 20, "options": 4, "min_content_len": 10},
    "medium": {"time": 15, "options": 4, "min_content_len": 20},
    "hard": {"time": 10, "options": 4, "min_content_len": 20},
}

SCORE_CONFIG = {
    "easy": {"base": 10, "time_bonus_rate": 0.5, "combo_bonus": [0, 0, 2, 4, 6, 8, 10]},
    "medium": {"base": 15, "time_bonus_rate": 1.0, "combo_bonus": [0, 0, 3, 6, 9, 12, 15]},
    "hard": {"base": 20, "time_bonus_rate": 1.5, "combo_bonus": [0, 0, 4, 8, 12, 16, 20]},
}


def _split_content_lines(content: str) -> List[str]:
    lines = []
    for line in content.replace("\r\n", "\n").split("\n"):
        line = line.strip()
        if not line:
            continue
        for sep in ["。", "！", "？"]:
            line = line.replace(sep, sep + "\n")
        for sub in line.split("\n"):
            sub = sub.strip().rstrip("，、；")
            if len(sub) >= 4:
                lines.append(sub)
    return lines


def _mask_verse(verse: str) -> str:
    chars = list(verse)
    if len(chars) <= 2:
        return "____"
    indices = list(range(len(chars)))
    mask_count = max(1, len(chars) // 3)
    mask_positions = random.sample(indices, min(mask_count, len(indices)))
    for i in mask_positions:
        chars[i] = "____"
    return "".join(chars)


async def _generate_question(
    db: AsyncSession,
    q_index: int,
    q_type: str,
    difficulty: str,
    used_poem_ids: set
) -> Optional[dict]:
    config = DIFFICULTY_CONFIG[difficulty]

    for _ in range(10):
        q = select(Poem).where(
            func.length(Poem.content) >= config["min_content_len"]
        ).order_by(func.random()).limit(20)
        rows = (await db.execute(q)).scalars().all()
        candidates = [p for p in rows if p.id not in used_poem_ids]
        if not candidates:
            candidates = rows
        if not candidates:
            return None

        poem = random.choice(candidates)
        lines = _split_content_lines(poem.content)
        if len(lines) < 2:
            continue

        lq, rq = "\u201c", "\u201d"

        if q_type == "fill_verse":
            target_line = random.choice(lines)
            target_idx = lines.index(target_line)
            context_line = lines[target_idx - 1] if target_idx > 0 else lines[min(target_idx + 1, len(lines) - 1)]
            question_text = f"{lq}{context_line}{rq}的下一句是？" if target_idx > 0 else f"{lq}{context_line}{rq}的上一句是？"

            wrong_q = select(Poem.content).where(
                Poem.id != poem.id,
                Poem.dynasty == poem.dynasty
            ).order_by(func.random()).limit(10)
            wrong_poems = (await db.execute(wrong_q)).scalars().all()
            wrong_lines = []
            for wp_content in wrong_poems:
                wl = _split_content_lines(wp_content)
                wrong_lines.extend(wl)
            wrong_lines = [w for w in wrong_lines if w != target_line and len(w) >= 3]
            random.shuffle(wrong_lines)
            distractors = wrong_lines[:3]

            if len(distractors) < 3:
                continue

            options_raw = distractors + [target_line]
            random.shuffle(options_raw)
            options = [QuestionOption(key=chr(65 + i), text=t) for i, t in enumerate(options_raw)]
            correct_key = next(o.key for o in options if o.text == target_line)

            return {
                "index": q_index,
                "question_type": "fill_verse",
                "question_text": question_text,
                "options": options,
                "correct_answer": correct_key,
                "poem_id": poem.id,
                "poem_title": poem.title,
                "poem_author": poem.author,
                "poem_dynasty": poem.dynasty,
                "poem_content": poem.content,
                "hint": f"出自{poem.dynasty}诗人{poem.author}之手",
            }

        elif q_type == "author_guess":
            target_line = random.choice(lines)
            question_text = f"{lq}{target_line}{rq}的作者是？"

            wrong_q = select(Poem.author).where(
                Poem.author != poem.author,
                Poem.dynasty == poem.dynasty
            ).limit(50)
            wrong_authors_raw = list((await db.execute(wrong_q)).scalars().all())
            wrong_authors = list({a for a in wrong_authors_raw if a and a != poem.author})
            random.shuffle(wrong_authors)
            distractors = wrong_authors[:3]

            if len(distractors) < 3:
                continue

            options_raw = distractors + [poem.author]
            random.shuffle(options_raw)
            options = [QuestionOption(key=chr(65 + i), text=t) for i, t in enumerate(options_raw)]
            correct_key = next(o.key for o in options if o.text == poem.author)

            return {
                "index": q_index,
                "question_type": "author_guess",
                "question_text": question_text,
                "options": options,
                "correct_answer": correct_key,
                "poem_id": poem.id,
                "poem_title": poem.title,
                "poem_author": poem.author,
                "poem_dynasty": poem.dynasty,
                "poem_content": poem.content,
                "hint": f"此诗题为《{poem.title}》",
            }

        elif q_type == "verse_match":
            if len(lines) < 4:
                continue
            idx = random.randrange(0, len(lines) - 1)
            upper = lines[idx]
            lower = lines[idx + 1]
            question_text = f"请选出与{lq}{upper}{rq}对应的下句"

            wrong_q = select(Poem.content).where(
                Poem.id != poem.id
            ).order_by(func.random()).limit(10)
            wrong_poems = (await db.execute(wrong_q)).scalars().all()
            wrong_lines = []
            for wp_content in wrong_poems:
                wl = _split_content_lines(wp_content)
                wrong_lines.extend(wl)
            wrong_lines = [w for w in wrong_lines if w != lower and w != upper and len(w) >= 3]
            random.shuffle(wrong_lines)
            distractors = wrong_lines[:3]

            if len(distractors) < 3:
                continue

            options_raw = distractors + [lower]
            random.shuffle(options_raw)
            options = [QuestionOption(key=chr(65 + i), text=t) for i, t in enumerate(options_raw)]
            correct_key = next(o.key for o in options if o.text == lower)

            return {
                "index": q_index,
                "question_type": "verse_match",
                "question_text": question_text,
                "options": options,
                "correct_answer": correct_key,
                "poem_id": poem.id,
                "poem_title": poem.title,
                "poem_author": poem.author,
                "poem_dynasty": poem.dynasty,
                "poem_content": poem.content,
                "hint": f"出自《{poem.title}》",
            }

    return None


def _pick_question_type(q_type: str) -> str:
    if q_type == "mixed":
        return random.choice(["fill_verse", "author_guess", "verse_match"])
    return q_type


def _calc_score(difficulty: str, is_correct: bool, time_spent: int, combo: int) -> int:
    if not is_correct:
        return 0
    cfg = SCORE_CONFIG[difficulty]
    time_limit = DIFFICULTY_CONFIG[difficulty]["time"]
    time_bonus = max(0, int((time_limit - time_spent) * cfg["time_bonus_rate"]))
    combo_idx = min(combo, len(cfg["combo_bonus"]) - 1)
    combo_bonus = cfg["combo_bonus"][combo_idx]
    return cfg["base"] + time_bonus + combo_bonus


@router.post("/start", response_model=TimedChallengeStartResponse)
async def start_timed_challenge(
    req: TimedChallengeStartRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    active_q = select(TimedChallengeSession).where(
        and_(
            TimedChallengeSession.user_id == current_user.id,
            TimedChallengeSession.status == "active"
        )
    )
    active = (await db.execute(active_q)).scalars().all()
    for s in active:
        s.status = "abandoned"
        s.ended_at = func.now()

    config = DIFFICULTY_CONFIG[req.difficulty]
    session = TimedChallengeSession(
        user_id=current_user.id,
        difficulty=req.difficulty,
        question_type=req.question_type,
        total_questions=req.question_count,
        time_per_question=config["time"],
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    qt = _pick_question_type(req.question_type)
    q_data = await _generate_question(db, 0, qt, req.difficulty, set())
    if not q_data:
        raise HTTPException(status_code=500, detail="题库异常，无法生成题目")

    answer_record = TimedChallengeAnswer(
        session_id=session.id,
        user_id=current_user.id,
        question_index=0,
        question_type=q_data["question_type"],
        poem_id=q_data["poem_id"],
        question_text=q_data["question_text"],
        options=json.dumps([o.model_dump() for o in q_data["options"]], ensure_ascii=False),
        correct_answer=q_data["correct_answer"],
    )
    db.add(answer_record)
    await db.commit()

    return TimedChallengeStartResponse(
        session_id=session.id,
        difficulty=req.difficulty,
        total_questions=req.question_count,
        time_per_question=config["time"],
        first_question=TimedQuestion(
            index=0,
            question_type=q_data["question_type"],
            question_text=q_data["question_text"],
            options=q_data["options"],
            hint=q_data.get("hint"),
            poem_dynasty=q_data.get("poem_dynasty"),
            time_limit=config["time"],
        )
    )


@router.post("/answer", response_model=TimedAnswerResponse)
async def submit_answer(
    req: TimedAnswerRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    sess_q = select(TimedChallengeSession).where(
        and_(
            TimedChallengeSession.id == req.session_id,
            TimedChallengeSession.user_id == current_user.id,
            TimedChallengeSession.status == "active"
        )
    )
    session = (await db.execute(sess_q)).scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在或已结束")

    ans_q = select(TimedChallengeAnswer).where(
        and_(
            TimedChallengeAnswer.session_id == session.id,
            TimedChallengeAnswer.question_index == req.question_index,
        )
    )
    answer_record = (await db.execute(ans_q)).scalar_one_or_none()
    if not answer_record:
        raise HTTPException(status_code=404, detail="题目不存在")
    if answer_record.user_answer is not None:
        raise HTTPException(status_code=400, detail="该题已作答")

    is_correct = req.answer.upper() == answer_record.correct_answer.upper()

    if is_correct:
        session.combo += 1
        session.max_combo = max(session.max_combo, session.combo)
    else:
        session.combo = 0

    score = _calc_score(session.difficulty, is_correct, req.time_spent, session.combo)

    answer_record.user_answer = req.answer.upper()
    answer_record.is_correct = is_correct
    answer_record.time_spent = req.time_spent
    answer_record.score = score

    session.answered_count += 1
    if is_correct:
        session.correct_count += 1
    session.total_score += score

    poem_title = None
    poem_author = None
    poem_content = None
    if answer_record.poem_id:
        poem_q = select(Poem).where(Poem.id == answer_record.poem_id)
        poem = (await db.execute(poem_q)).scalar_one_or_none()
        if poem:
            poem_title = poem.title
            poem_author = poem.author
            poem_content = poem.content

    is_finished = session.answered_count >= session.total_questions
    next_question = None

    if not is_finished:
        used_ids_q = select(TimedChallengeAnswer.poem_id).where(
            TimedChallengeAnswer.session_id == session.id
        )
        used_rows = (await db.execute(used_ids_q)).scalars().all()
        used_ids = {pid for pid in used_rows if pid is not None}

        qt = _pick_question_type(session.question_type)
        next_idx = session.answered_count
        q_data = await _generate_question(db, next_idx, qt, session.difficulty, used_ids)

        if q_data:
            next_record = TimedChallengeAnswer(
                session_id=session.id,
                user_id=current_user.id,
                question_index=next_idx,
                question_type=q_data["question_type"],
                poem_id=q_data["poem_id"],
                question_text=q_data["question_text"],
                options=json.dumps([o.model_dump() for o in q_data["options"]], ensure_ascii=False),
                correct_answer=q_data["correct_answer"],
            )
            db.add(next_record)
            next_question = TimedQuestion(
                index=next_idx,
                question_type=q_data["question_type"],
                question_text=q_data["question_text"],
                options=q_data["options"],
                hint=q_data.get("hint"),
                poem_dynasty=q_data.get("poem_dynasty"),
                time_limit=DIFFICULTY_CONFIG[session.difficulty]["time"],
            )
        else:
            is_finished = True

    if is_finished:
        exp = calculate_timed_challenge_exp(session.correct_count, session.total_questions, session.difficulty, session.max_combo)
        session.exp_gained = exp
        session.status = "completed"
        session.ended_at = func.now()

        current_user.exp = (current_user.exp or 0) + exp
        current_user.points = (current_user.points or 0) + max(1, exp // 5)
        current_user.level = calculate_level(current_user.exp)
        await sync_user_achievements(db, current_user)

    correct_text = answer_record.correct_answer
    options_data = json.loads(answer_record.options)
    for opt in options_data:
        if opt["key"] == answer_record.correct_answer:
            correct_text = opt["text"]
            break

    await db.commit()

    return TimedAnswerResponse(
        is_correct=is_correct,
        correct_answer=correct_text,
        score_gained=score,
        combo=session.combo,
        total_score=session.total_score,
        correct_count=session.correct_count,
        answered_count=session.answered_count,
        poem_title=poem_title,
        poem_author=poem_author,
        poem_content=poem_content,
        next_question=next_question,
        is_finished=is_finished,
    )


@router.post("/end", response_model=TimedChallengeResult)
async def end_timed_challenge(
    req: TimedChallengeEndRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    sess_q = select(TimedChallengeSession).where(
        and_(
            TimedChallengeSession.id == req.session_id,
            TimedChallengeSession.user_id == current_user.id,
        )
    )
    session = (await db.execute(sess_q)).scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    if session.status == "active":
        exp = calculate_timed_challenge_exp(session.correct_count, session.total_questions, session.difficulty, session.max_combo)
        session.exp_gained = exp
        session.status = "completed"
        session.ended_at = func.now()

        current_user.exp = (current_user.exp or 0) + exp
        current_user.points = (current_user.points or 0) + max(1, exp // 5)
        current_user.level = calculate_level(current_user.exp)
        await sync_user_achievements(db, current_user)
        await db.commit()
        await db.refresh(session)

    answers_q = select(TimedChallengeAnswer).where(
        TimedChallengeAnswer.session_id == session.id
    ).order_by(TimedChallengeAnswer.question_index)
    answers = (await db.execute(answers_q)).scalars().all()

    details = []
    for a in answers:
        correct_text = a.correct_answer
        try:
            opts = json.loads(a.options)
            for opt in opts:
                if opt["key"] == a.correct_answer:
                    correct_text = opt["text"]
                    break
        except Exception:
            pass

        details.append(TimedAnswerDetail(
            index=a.question_index,
            question_type=a.question_type,
            question_text=a.question_text,
            correct_answer=correct_text,
            user_answer=a.user_answer,
            is_correct=a.is_correct,
            score=a.score,
            time_spent=a.time_spent,
        ))

    duration = 0
    if session.ended_at and session.started_at:
        duration = int((session.ended_at - session.started_at).total_seconds())

    accuracy = 0.0
    if session.answered_count > 0:
        accuracy = round(session.correct_count / session.answered_count * 100, 1)

    return TimedChallengeResult(
        session_id=session.id,
        difficulty=session.difficulty,
        total_questions=session.total_questions,
        answered_count=session.answered_count,
        correct_count=session.correct_count,
        accuracy=accuracy,
        total_score=session.total_score,
        max_combo=session.max_combo,
        exp_gained=session.exp_gained,
        duration=duration,
        answers=details,
    )


@router.get("/history", response_model=TimedHistoryResponse)
async def get_timed_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    base = select(TimedChallengeSession).where(
        and_(
            TimedChallengeSession.user_id == current_user.id,
            TimedChallengeSession.status == "completed",
        )
    )
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar() or 0

    q = base.order_by(desc(TimedChallengeSession.started_at)).offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(q)).scalars().all()

    items = []
    for s in rows:
        duration = 0
        if s.ended_at and s.started_at:
            duration = int((s.ended_at - s.started_at).total_seconds())
        accuracy = 0.0
        if s.answered_count > 0:
            accuracy = round(s.correct_count / s.answered_count * 100, 1)
        items.append(TimedHistoryItem(
            id=s.id,
            difficulty=s.difficulty,
            total_questions=s.total_questions,
            correct_count=s.correct_count,
            accuracy=accuracy,
            total_score=s.total_score,
            max_combo=s.max_combo,
            exp_gained=s.exp_gained,
            started_at=s.started_at,
            duration=duration,
        ))

    stats_q = select(
        func.max(TimedChallengeSession.total_score),
        func.count(TimedChallengeSession.id),
    ).where(
        and_(
            TimedChallengeSession.user_id == current_user.id,
            TimedChallengeSession.status == "completed",
        )
    )
    stats = (await db.execute(stats_q)).one()
    best_score = stats[0] or 0
    total_games = stats[1] or 0

    best_acc_q = select(
        TimedChallengeSession.correct_count,
        TimedChallengeSession.answered_count,
    ).where(
        and_(
            TimedChallengeSession.user_id == current_user.id,
            TimedChallengeSession.status == "completed",
            TimedChallengeSession.answered_count > 0,
        )
    )
    acc_rows = (await db.execute(best_acc_q)).all()
    best_accuracy = 0.0
    for r in acc_rows:
        acc = r[0] / r[1] * 100 if r[1] > 0 else 0
        best_accuracy = max(best_accuracy, acc)
    best_accuracy = round(best_accuracy, 1)

    return TimedHistoryResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        best_score=best_score,
        best_accuracy=best_accuracy,
        total_games=total_games,
    )


@router.get("/rankings", response_model=TimedRankingResponse)
async def get_timed_rankings(
    period: str = Query("all", pattern="^(today|week|all)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    cache_key = f"timed:rankings:{period}:{page}:{page_size}"
    cached = await cache_get(cache_key)
    if cached:
        return JSONResponse(content=cached)

    base = select(
        TimedChallengeSession.user_id,
        func.sum(TimedChallengeSession.total_score).label("sum_score"),
        func.max(TimedChallengeSession.total_score).label("best_score"),
        func.count(TimedChallengeSession.id).label("games"),
    ).where(TimedChallengeSession.status == "completed")

    now = datetime.utcnow()
    if period == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        base = base.where(TimedChallengeSession.started_at >= start)
    elif period == "week":
        start = now - timedelta(days=7)
        base = base.where(TimedChallengeSession.started_at >= start)

    base = base.group_by(TimedChallengeSession.user_id).subquery()
    total_q = select(func.count()).select_from(base)
    total = (await db.execute(total_q)).scalar() or 0

    accuracy = select(
        TimedChallengeSession.user_id.label("user_id"),
        func.sum(TimedChallengeSession.correct_count).label("correct_count"),
        func.sum(TimedChallengeSession.answered_count).label("answered_count"),
    ).where(
        TimedChallengeSession.status == "completed"
    ).group_by(
        TimedChallengeSession.user_id
    ).subquery()

    ranked = select(
        base.c.user_id,
        base.c.sum_score,
        base.c.best_score,
        base.c.games,
        User.username,
        User.nickname,
        User.avatar_url,
        User.exp,
        accuracy.c.correct_count,
        accuracy.c.answered_count,
    ).join(
        User, User.id == base.c.user_id
    ).outerjoin(
        accuracy, accuracy.c.user_id == base.c.user_id
    ).order_by(
        desc(base.c.sum_score)
    ).offset(
        (page - 1) * page_size
    ).limit(
        page_size
    )
    rows = (await db.execute(ranked)).all()

    items = []
    for i, r in enumerate(rows):
        best_acc = round(r.correct_count / r.answered_count * 100, 1) if r.answered_count and r.answered_count > 0 else 0.0

        items.append({
            "rank": (page - 1) * page_size + i + 1,
            "user_id": r.user_id,
            "username": r.username,
            "nickname": r.nickname,
            "avatar_url": r.avatar_url,
            "total_score": r.sum_score or 0,
            "best_score": r.best_score or 0,
            "total_games": r.games or 0,
            "best_accuracy": best_acc,
            "level": calculate_level(r.exp or 0),
            "exp": r.exp or 0,
        })

    response_data = {
        "items": items,
        "total": total,
        "period": period,
    }
    await cache_set(cache_key, response_data, ttl=30)
    return JSONResponse(content=response_data)

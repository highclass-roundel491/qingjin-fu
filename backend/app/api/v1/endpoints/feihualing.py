from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from typing import List, Optional
import asyncio
import random
import re
import time as _time
from datetime import datetime, timezone
from uuid import UUID

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.feihualing import FeiHuaLingGame, FeiHuaLingRound
from app.models.poem import Poem
from app.schemas.feihualing import (
    FeiHuaLingGameStart, FeiHuaLingGameResponse, PoemSubmit,
    PoemSubmitResponse, GameEndRequest, GameResult,
    GameHistoryResponse, GameHistoryItem, RoundHistory, HintResponse,
    AIRoundData
)
from app.core.levels import calculate_feihualing_exp, calculate_feihualing_score, calculate_level
from app.services.ai_service import get_ai_service
from app.services.poem_search import search_poems_by_keyword, search_poems_by_content, extract_verses

import logging
logger = logging.getLogger("uvicorn.error")

router = APIRouter()

COMMON_KEYWORDS = [
    "春", "夏", "秋", "冬", "花", "月", "风", "雨", "雪", "云",
    "山", "水", "江", "河", "天", "地", "日", "星", "夜", "晨",
    "酒", "梦", "愁", "情", "柳", "鸟", "竹", "松", "琴", "书"
]

HINT_COST = 3
MIN_POEM_LENGTH = 3
VALID_TARGET_ROUNDS = {5, 10, 15}
AI_PROMPT_CANDIDATE_LIMIT = 8


def _split_verses(content: str) -> List[str]:
    parts = re.split(r'[，。！？；\n,\.!?;]', content)
    return [p.strip() for p in parts if p.strip() and len(p.strip()) >= MIN_POEM_LENGTH]

AI_RESPONSE_TIMEOUT = 10


def _normalize_verse_for_match(content: Optional[str]) -> str:
    if not isinstance(content, str):
        return ""
    return re.sub(r'[\s，。！？；、,.!?;]+', '', content)


def _match_candidate_verse(candidate_list: List[dict], verse: str) -> Optional[dict]:
    target = _normalize_verse_for_match(verse)
    if not target:
        return None
    for candidate in candidate_list:
        if _normalize_verse_for_match(candidate.get("content")) == target:
            return candidate
    return None


def _normalize_target_rounds(value: Optional[int]) -> int:
    return value if value in VALID_TARGET_ROUNDS else 10


def _normalize_ai_payload(payload: object) -> dict:
    if not isinstance(payload, dict):
        return {}
    verse = payload.get("verse")
    return {
        "verse": verse.strip() if isinstance(verse, str) else "",
        "poem_title": payload.get("poem_title") if isinstance(payload.get("poem_title"), str) else None,
        "author": payload.get("author") if isinstance(payload.get("author"), str) else None,
        "dynasty": payload.get("dynasty") if isinstance(payload.get("dynasty"), str) else None,
    }


def _calculate_ai_score(target_rounds: int, combo: int) -> int:
    return calculate_feihualing_score(target_rounds, 20, combo)

@router.post("/start", response_model=FeiHuaLingGameResponse)
async def start_game(
    request: FeiHuaLingGameStart,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    t_start = _time.monotonic()
    target_rounds = _normalize_target_rounds(request.difficulty)

    if request.keyword and len(request.keyword) == 1:
        keyword = request.keyword
    else:
        keyword = random.choice(COMMON_KEYWORDS)

    t_kw = _time.monotonic()
    logger.info(f"[FHL start] keyword={keyword} kw_select={t_kw - t_start:.3f}s")

    game = FeiHuaLingGame(
        user_id=current_user.id,
        keyword=keyword,
        status="playing"
    )
    db.add(game)
    await db.commit()
    await db.refresh(game)

    ai_first = None
    try:
        poems = await search_poems_by_keyword(db, keyword, limit=50)
        t_search = _time.monotonic()
        logger.info(f"[FHL start] poem_search={t_search - t_kw:.3f}s found={len(poems)}")

        candidate_list: list[dict] = []
        if poems:
            for p in poems:
                verses = extract_verses(p, keyword)
                for v in verses:
                    v["poem_id"] = p.id
                    candidate_list.append(v)

        ai_verse = ""
        ai_meta: dict = {}
        ai_poem_id = None

        try:
            ai_service = get_ai_service()
            ai_result = await asyncio.wait_for(
                ai_service.feihualing_respond(
                    keyword=keyword,
                    used_poems=[],
                    candidate_poems=candidate_list[:AI_PROMPT_CANDIDATE_LIMIT] if candidate_list else None,
                ),
                timeout=AI_RESPONSE_TIMEOUT,
            )
            t_ai = _time.monotonic()
            logger.info(f"[FHL start] ai_respond={t_ai - t_search:.3f}s")
            ai_meta = _normalize_ai_payload(ai_result)
            ai_verse = ai_meta.get("verse", "")
            if ai_verse and keyword not in ai_verse:
                ai_verse = ""
            if ai_verse:
                candidate_match = _match_candidate_verse(candidate_list, ai_verse)
                if candidate_match:
                    ai_poem_id = candidate_match.get("poem_id")
                    ai_meta["poem_title"] = ai_meta.get("poem_title") or candidate_match.get("title")
                    ai_meta["author"] = ai_meta.get("author") or candidate_match.get("author")
                    ai_meta["dynasty"] = ai_meta.get("dynasty") or candidate_match.get("dynasty")
                else:
                    matched = await search_poems_by_content(db, ai_verse, limit=1)
                    if matched:
                        ai_poem_id = matched[0].id
                        ai_meta["poem_title"] = ai_meta.get("poem_title") or matched[0].title
                        ai_meta["author"] = ai_meta.get("author") or matched[0].author
                        ai_meta["dynasty"] = ai_meta.get("dynasty") or matched[0].dynasty
        except asyncio.TimeoutError:
            logger.warning(f"[FHL start] AI调用超时({AI_RESPONSE_TIMEOUT}s)，使用fallback")
        except Exception as e:
            logger.warning(f"AI先手出句失败，使用fallback: {e}")

        if not ai_verse and candidate_list:
            pick = random.choice(candidate_list)
            ai_verse = pick["content"]
            ai_poem_id = pick.get("poem_id")
            ai_meta = {
                "verse": ai_verse,
                "poem_title": pick.get("title"),
                "author": pick.get("author"),
                "dynasty": pick.get("dynasty"),
            }

        if ai_verse:
            game.total_rounds = 1
            ai_round = FeiHuaLingRound(
                game_id=game.id,
                round_number=1,
                player="ai",
                poem_content=ai_verse,
                poem_id=ai_poem_id,
                poem_author=ai_meta.get("author"),
                poem_title=ai_meta.get("poem_title"),
                poem_dynasty=ai_meta.get("dynasty"),
                response_time=None
            )
            db.add(ai_round)
            game.ai_score = _calculate_ai_score(target_rounds, 1)
            await db.commit()

            ai_first = AIRoundData(
                verse=ai_verse,
                poem_title=ai_meta.get("poem_title"),
                author=ai_meta.get("author"),
                dynasty=ai_meta.get("dynasty"),
                round_number=1,
                verified=ai_poem_id is not None
            )
    except Exception as e:
        logger.warning(f"AI先手整体失败: {e}")

    t_total = _time.monotonic()
    logger.info(f"[FHL start] total={t_total - t_start:.3f}s ai_first={'yes' if ai_first else 'fallback'}")

    return FeiHuaLingGameResponse(
        game_id=game.id,
        keyword=keyword,
        time_limit=30,
        target_rounds=target_rounds,
        ai_score=game.ai_score,
        ai_first_round=ai_first
    )

@router.post("/submit", response_model=PoemSubmitResponse)
async def submit_poem(
    request: PoemSubmit,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    game_query = select(FeiHuaLingGame).where(
        FeiHuaLingGame.id == request.game_id,
        FeiHuaLingGame.user_id == current_user.id
    )
    game_result = await db.execute(game_query)
    game = game_result.scalar_one_or_none()

    if not game:
        raise HTTPException(status_code=404, detail="游戏不存在")

    if game.status != "playing":
        raise HTTPException(status_code=400, detail="游戏已结束")

    poem_content = re.sub(r'^[\s，。！？；、,.!?;\s]+|[\s，。！？；、,.!?;\s]+$', '', request.poem_content)

    if len(poem_content) < MIN_POEM_LENGTH:
        return PoemSubmitResponse(
            valid=False,
            message=f"诗句至少需要{MIN_POEM_LENGTH}个字",
            continue_game=True,
            user_score=game.user_score,
            round_number=game.total_rounds
        )

    if game.keyword not in poem_content:
        return PoemSubmitResponse(
            valid=False,
            message=f'诗句中未包含令字「{game.keyword}」',
            continue_game=True,
            user_score=game.user_score,
            round_number=game.total_rounds
        )

    safe_content = poem_content.replace('%', r'\%').replace('_', r'\_')
    poem_query = select(Poem).where(
        Poem.content.like(f'%{safe_content}%')
    ).limit(1)
    poem_result_q = await db.execute(poem_query)
    poem = poem_result_q.scalar_one_or_none()

    if not poem:
        verse_poems = []
        candidate_q = select(Poem).where(
            Poem.content.contains(game.keyword)
        ).limit(500)
        candidate_r = await db.execute(candidate_q)
        candidates = candidate_r.scalars().all()

        for cp in candidates:
            verses = _split_verses(cp.content)
            for v in verses:
                if poem_content in v or v in poem_content:
                    verse_poems.append(cp)
                    break
            if verse_poems:
                break

        if verse_poems:
            poem = verse_poems[0]
        else:
            return PoemSubmitResponse(
                valid=False,
                message="未找到该诗句，请输入完整的诗句或半句",
                continue_game=True,
                user_score=game.user_score,
                round_number=game.total_rounds
            )

    used_content_query = select(FeiHuaLingRound).where(
        FeiHuaLingRound.game_id == request.game_id,
        FeiHuaLingRound.poem_content == poem_content
    )
    used_content_r = await db.execute(used_content_query)
    if used_content_r.scalar_one_or_none():
        return PoemSubmitResponse(
            valid=False,
            message="该诗句内容已被使用，请换一句",
            continue_game=True,
            user_score=game.user_score,
            round_number=game.total_rounds
        )

    used_poem_query = select(FeiHuaLingRound).where(
        FeiHuaLingRound.game_id == request.game_id,
        FeiHuaLingRound.poem_id == poem.id
    )
    used_poem_r = await db.execute(used_poem_query)
    if used_poem_r.scalar_one_or_none():
        return PoemSubmitResponse(
            valid=False,
            message="该诗已被引用过，请换一首诗",
            continue_game=True,
            user_score=game.user_score,
            round_number=game.total_rounds
        )

    user_rounds_q = select(func.count()).select_from(FeiHuaLingRound).where(
        FeiHuaLingRound.game_id == request.game_id,
        FeiHuaLingRound.player == "user"
    )
    user_rounds_r = await db.execute(user_rounds_q)
    user_round_count = (user_rounds_r.scalar() or 0) + 1

    target_rounds = _normalize_target_rounds(request.target_rounds)
    score_gained = calculate_feihualing_score(target_rounds, request.response_time, user_round_count)

    game.total_rounds += 1
    game.user_score += score_gained

    exp_gained = calculate_feihualing_exp(score_gained)
    current_user.exp = current_user.exp or 0
    current_user.exp += exp_gained
    current_user.level = calculate_level(current_user.exp)

    user_round = FeiHuaLingRound(
        game_id=game.id,
        round_number=game.total_rounds,
        player="user",
        poem_content=poem_content,
        poem_id=poem.id,
        response_time=request.response_time
    )
    db.add(user_round)

    if user_round_count >= target_rounds:
        game.status = "finished"
        game.ended_at = datetime.now(timezone.utc)
        if game.user_score > game.ai_score:
            game.result = "win"
            result_msg = f"诗才盖世！{target_rounds}轮对弈完胜AI"
        elif game.user_score < game.ai_score:
            game.result = "lose"
            result_msg = f"惜败！{target_rounds}轮后AI得分更高"
        else:
            game.result = "draw"
            result_msg = f"棋逢对手！{target_rounds}轮后平局"
        await db.commit()

        return PoemSubmitResponse(
            valid=True,
            message=result_msg,
            continue_game=False,
            user_score=game.user_score,
            ai_score=game.ai_score,
            round_number=game.total_rounds,
            score_gained=score_gained,
            combo=user_round_count,
            user_round_count=user_round_count,
            poem_author=poem.author,
            poem_title=poem.title,
            poem_dynasty=poem.dynasty
        )

    await db.commit()

    ai_round_data = None
    ai_failed = False

    used_rounds_q = select(FeiHuaLingRound.poem_content).where(
        FeiHuaLingRound.game_id == request.game_id
    )
    used_r = await db.execute(used_rounds_q)
    used_poems = [r[0] for r in used_r.all()]

    used_poem_ids_q = select(FeiHuaLingRound.poem_id).where(
        FeiHuaLingRound.game_id == request.game_id,
        FeiHuaLingRound.poem_id.isnot(None)
    )
    used_pid_r = await db.execute(used_poem_ids_q)
    used_poem_ids = {r[0] for r in used_pid_r.all()}

    poems = await search_poems_by_keyword(db, game.keyword, limit=80)
    candidate_list: list[dict] = []
    if poems:
        for p in poems:
            if p.id in used_poem_ids:
                continue
            verses = extract_verses(p, game.keyword)
            for v in verses:
                if v["content"] not in used_poems:
                    v["poem_id"] = p.id
                    candidate_list.append(v)

    progress_ratio = user_round_count / target_rounds if target_rounds > 0 else 0
    if progress_ratio < 0.4:
        ai_candidates = candidate_list[:AI_PROMPT_CANDIDATE_LIMIT]
    elif progress_ratio < 0.7:
        mid = len(candidate_list) // 3
        ai_candidates = candidate_list[mid:mid + AI_PROMPT_CANDIDATE_LIMIT]
    else:
        ai_candidates = (
            candidate_list[-AI_PROMPT_CANDIDATE_LIMIT:]
            if len(candidate_list) > AI_PROMPT_CANDIDATE_LIMIT
            else candidate_list
        )

    ai_verse = ""
    ai_meta: dict = {}
    ai_poem_id = None
    try:
        ai_service = get_ai_service()
        ai_result = await asyncio.wait_for(
            ai_service.feihualing_respond(
                keyword=game.keyword,
                used_poems=used_poems,
                candidate_poems=ai_candidates if ai_candidates else None,
            ),
            timeout=AI_RESPONSE_TIMEOUT,
        )
        ai_meta = _normalize_ai_payload(ai_result)
        ai_verse = ai_meta.get("verse", "")
        if ai_verse and (game.keyword not in ai_verse or ai_verse in used_poems):
            ai_verse = ""

        if ai_verse:
            candidate_match = _match_candidate_verse(candidate_list, ai_verse)
            if candidate_match and candidate_match.get("poem_id") not in used_poem_ids:
                ai_poem_id = candidate_match.get("poem_id")
                ai_meta["poem_title"] = ai_meta.get("poem_title") or candidate_match.get("title")
                ai_meta["author"] = ai_meta.get("author") or candidate_match.get("author")
                ai_meta["dynasty"] = ai_meta.get("dynasty") or candidate_match.get("dynasty")
            else:
                matched = await search_poems_by_content(db, ai_verse, limit=1)
                if matched:
                    mp = matched[0]
                    if mp.id not in used_poem_ids:
                        ai_poem_id = mp.id
                        ai_meta["poem_title"] = ai_meta.get("poem_title") or mp.title
                        ai_meta["author"] = ai_meta.get("author") or mp.author
                        ai_meta["dynasty"] = ai_meta.get("dynasty") or mp.dynasty
    except asyncio.TimeoutError:
        logger.warning(f"AI飞花令应答超时({AI_RESPONSE_TIMEOUT}s)，使用数据库fallback")
    except Exception as e:
        logger.warning(f"AI飞花令应答失败，将使用数据库fallback: {e}")

    if not ai_verse and candidate_list:
        pick = random.choice(candidate_list)
        ai_verse = pick["content"]
        ai_poem_id = pick.get("poem_id")
        ai_meta = {
            "verse": ai_verse,
            "poem_title": pick.get("title"),
            "author": pick.get("author"),
            "dynasty": pick.get("dynasty"),
        }

    if ai_verse:
        game.total_rounds += 1
        ai_round = FeiHuaLingRound(
            game_id=game.id,
            round_number=game.total_rounds,
            player="ai",
            poem_content=ai_verse,
            poem_id=ai_poem_id,
            poem_author=ai_meta.get("author"),
            poem_title=ai_meta.get("poem_title"),
            poem_dynasty=ai_meta.get("dynasty"),
            response_time=None
        )
        db.add(ai_round)

        ai_score_val = _calculate_ai_score(target_rounds, user_round_count)
        game.ai_score += ai_score_val
        await db.commit()

        ai_round_data = AIRoundData(
            verse=ai_verse,
            poem_title=ai_meta.get("poem_title"),
            author=ai_meta.get("author"),
            dynasty=ai_meta.get("dynasty"),
            round_number=game.total_rounds,
            verified=ai_poem_id is not None
        )
    else:
        ai_failed = True

    remaining = target_rounds - user_round_count

    return PoemSubmitResponse(
        valid=True,
        message=f"妙！还需{remaining}句",
        continue_game=True,
        user_score=game.user_score,
        ai_score=game.ai_score,
        round_number=game.total_rounds,
        score_gained=score_gained,
        combo=user_round_count,
        user_round_count=user_round_count,
        poem_author=poem.author,
        poem_title=poem.title,
        poem_dynasty=poem.dynasty,
        ai_round=ai_round_data,
        ai_failed=ai_failed
    )

@router.get("/hint/{game_id}", response_model=HintResponse)
async def get_hint(
    game_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    game_query = select(FeiHuaLingGame).where(
        FeiHuaLingGame.id == game_id,
        FeiHuaLingGame.user_id == current_user.id
    )
    game_result = await db.execute(game_query)
    game = game_result.scalar_one_or_none()

    if not game:
        raise HTTPException(status_code=404, detail="游戏不存在")

    if game.status != "playing":
        raise HTTPException(status_code=400, detail="游戏已结束")

    rounds_query = select(FeiHuaLingRound.poem_id).where(
        FeiHuaLingRound.game_id == game_id,
        FeiHuaLingRound.poem_id.isnot(None)
    )
    rounds_result = await db.execute(rounds_query)
    used_poem_ids = [r[0] for r in rounds_result.all()]

    hint_poem_query = select(Poem).where(Poem.content.contains(game.keyword))
    if used_poem_ids:
        hint_poem_query = hint_poem_query.where(~Poem.id.in_(used_poem_ids))

    count_q = select(func.count()).select_from(hint_poem_query.subquery())
    hint_total = (await db.execute(count_q)).scalar() or 0
    if hint_total == 0:
        raise HTTPException(status_code=404, detail="暂无可用提示")

    offset = random.randint(0, hint_total - 1)
    hint_poem_query = hint_poem_query.offset(offset).limit(1)

    hint_poem_result = await db.execute(hint_poem_query)
    hint_poem = hint_poem_result.scalar_one_or_none()

    if not hint_poem:
        raise HTTPException(status_code=404, detail="暂无可用提示")
    verses = _split_verses(hint_poem.content)
    matching_verses = [v for v in verses if game.keyword in v]

    if matching_verses:
        chosen = random.choice(matching_verses)
        mask_len = max(1, len(chosen) // 3)
        mask_start = random.randint(0, len(chosen) - mask_len)
        hint_text = chosen[:mask_start] + "_" * mask_len + chosen[mask_start + mask_len:]
    else:
        content = hint_poem.content
        if len(content) > 10:
            hint_text = content[:8] + "..."
        else:
            hint_text = content[:len(content) // 2] + "..."

    game.user_score = max(0, game.user_score - HINT_COST)
    await db.commit()

    return HintResponse(
        hint=hint_text,
        author=hint_poem.author,
        hint_cost=HINT_COST
    )

@router.post("/end", response_model=GameResult)
async def end_game(
    request: GameEndRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    game_query = select(FeiHuaLingGame).where(
        FeiHuaLingGame.id == request.game_id,
        FeiHuaLingGame.user_id == current_user.id
    )
    game_result = await db.execute(game_query)
    game = game_result.scalar_one_or_none()

    if not game:
        raise HTTPException(status_code=404, detail="游戏不存在")

    if game.status != "finished":
        game.status = "finished"
        game.ended_at = datetime.now(timezone.utc)

        if request.reason == "win":
            game.result = "win"
        elif request.reason in ("surrender", "timeout"):
            game.result = "lose"
        else:
            game.result = "draw"

        await db.commit()

    rounds_query = select(FeiHuaLingRound).where(
        FeiHuaLingRound.game_id == game.id
    ).order_by(FeiHuaLingRound.round_number)
    rounds_result = await db.execute(rounds_query)
    rounds = rounds_result.scalars().all()

    poem_ids = [r.poem_id for r in rounds if r.poem_id]
    poems_map = {}
    if poem_ids:
        poems_q = select(Poem).where(Poem.id.in_(poem_ids))
        poems_r = await db.execute(poems_q)
        poems_map = {p.id: p for p in poems_r.scalars().all()}

    round_history = []
    for r in rounds:
        poem = poems_map.get(r.poem_id)
        round_history.append(RoundHistory(
            round_number=r.round_number,
            player=r.player,
            poem_content=r.poem_content,
            author=r.poem_author or (poem.author if poem else None),
            title=r.poem_title or (poem.title if poem else None),
            dynasty=r.poem_dynasty or (poem.dynasty if poem else None),
            created_at=r.created_at
        ))

    duration = 0
    if game.ended_at and game.created_at:
        duration = int((game.ended_at - game.created_at).total_seconds())

    user_rc = sum(1 for r in rounds if r.player == "user")

    return GameResult(
        game_id=game.id,
        result=game.result,
        user_score=game.user_score,
        ai_score=game.ai_score,
        total_rounds=game.total_rounds,
        user_round_count=user_rc,
        keyword=game.keyword,
        duration=duration,
        rounds=round_history
    )

@router.get("/history", response_model=GameHistoryResponse)
async def get_history(
    page: int = 1,
    page_size: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    count_query = select(func.count()).select_from(FeiHuaLingGame).where(
        FeiHuaLingGame.user_id == current_user.id,
        FeiHuaLingGame.status == "finished"
    )
    count_result = await db.execute(count_query)
    total = count_result.scalar()
    
    games_query = select(FeiHuaLingGame).where(
        FeiHuaLingGame.user_id == current_user.id,
        FeiHuaLingGame.status == "finished"
    ).order_by(desc(FeiHuaLingGame.created_at)).offset(
        (page - 1) * page_size
    ).limit(page_size)
    
    games_result = await db.execute(games_query)
    games = games_result.scalars().all()
    
    items = [GameHistoryItem.model_validate(game, from_attributes=True) for game in games]
    
    return GameHistoryResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )

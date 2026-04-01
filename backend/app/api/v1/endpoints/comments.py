from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from typing import Optional
from app.core.database import get_db
from app.models.comment import WorkComment, WorkCommentLike
from app.models.work import Work
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentResponse, CommentListResponse
from app.api.deps import get_current_user, get_current_user_optional

router = APIRouter()


async def build_comment_response(
    comment: WorkComment,
    user: User,
    db: AsyncSession,
    current_user_id: Optional[int] = None,
    reply_to_username: Optional[str] = None
) -> CommentResponse:
    is_liked = False
    if current_user_id:
        like_r = await db.execute(
            select(WorkCommentLike).where(
                and_(WorkCommentLike.comment_id == comment.id, WorkCommentLike.user_id == current_user_id)
            )
        )
        is_liked = like_r.scalar_one_or_none() is not None

    return CommentResponse(
        id=comment.id,
        work_id=comment.work_id,
        user_id=comment.user_id,
        username=user.username,
        nickname=user.nickname,
        avatar_url=user.avatar_url,
        parent_id=comment.parent_id,
        reply_to_username=reply_to_username,
        content=comment.content,
        like_count=comment.like_count,
        is_liked=is_liked,
        created_at=comment.created_at,
        replies=[]
    )


@router.post("/{work_id}/comments", response_model=CommentResponse)
async def create_comment(
    work_id: int,
    data: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    work_r = await db.execute(select(Work).where(and_(Work.id == work_id, Work.status == "published")))
    work = work_r.scalar_one_or_none()
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在或未发布")

    reply_to_username = None
    if data.parent_id:
        parent_r = await db.execute(
            select(WorkComment).where(and_(WorkComment.id == data.parent_id, WorkComment.work_id == work_id))
        )
        parent = parent_r.scalar_one_or_none()
        if not parent:
            raise HTTPException(status_code=404, detail="回复的评论不存在")
        parent_user_r = await db.execute(select(User).where(User.id == parent.user_id))
        parent_user = parent_user_r.scalar_one_or_none()
        if parent_user:
            reply_to_username = parent_user.username

    comment = WorkComment(
        work_id=work_id,
        user_id=current_user.id,
        parent_id=data.parent_id,
        content=data.content
    )
    db.add(comment)

    work.comment_count = (work.comment_count or 0) + 1

    await db.commit()
    await db.refresh(comment)

    return await build_comment_response(comment, current_user, db, current_user.id, reply_to_username)


@router.get("/{work_id}/comments", response_model=CommentListResponse)
async def get_comments(
    work_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    current_user_id = current_user.id if current_user else None

    count_q = select(func.count()).select_from(WorkComment).where(
        and_(WorkComment.work_id == work_id, WorkComment.parent_id.is_(None))
    )
    total_r = await db.execute(count_q)
    total = total_r.scalar() or 0

    top_q = select(WorkComment, User).join(User, WorkComment.user_id == User.id).where(
        and_(WorkComment.work_id == work_id, WorkComment.parent_id.is_(None))
    ).order_by(desc(WorkComment.created_at)).offset((page - 1) * page_size).limit(page_size)

    top_r = await db.execute(top_q)
    top_comments = top_r.all()

    items = []
    for comment, user in top_comments:
        resp = await build_comment_response(comment, user, db, current_user_id)

        replies_q = select(WorkComment, User).join(User, WorkComment.user_id == User.id).where(
            WorkComment.parent_id == comment.id
        ).order_by(WorkComment.created_at).limit(50)
        replies_r = await db.execute(replies_q)

        for reply, reply_user in replies_r.all():
            parent_user_r = await db.execute(select(User).where(User.id == comment.user_id))
            parent_user = parent_user_r.scalar_one_or_none()
            rtu = parent_user.username if parent_user else None

            if reply.parent_id != comment.id:
                nested_parent_r = await db.execute(select(WorkComment).where(WorkComment.id == reply.parent_id))
                nested_parent = nested_parent_r.scalar_one_or_none()
                if nested_parent:
                    np_user_r = await db.execute(select(User).where(User.id == nested_parent.user_id))
                    np_user = np_user_r.scalar_one_or_none()
                    rtu = np_user.username if np_user else None

            reply_resp = await build_comment_response(reply, reply_user, db, current_user_id, rtu)
            resp.replies.append(reply_resp)

        items.append(resp)

    return CommentListResponse(items=items, total=total, page=page, page_size=page_size)


@router.delete("/{work_id}/comments/{comment_id}")
async def delete_comment(
    work_id: int,
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    comment_r = await db.execute(
        select(WorkComment).where(and_(WorkComment.id == comment_id, WorkComment.work_id == work_id))
    )
    comment = comment_r.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")

    work_r = await db.execute(select(Work).where(Work.id == work_id))
    work = work_r.scalar_one_or_none()

    if comment.user_id != current_user.id:
        if not work or work.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权删除此评论")

    replies_count_r = await db.execute(
        select(func.count()).select_from(WorkComment).where(WorkComment.parent_id == comment_id)
    )
    replies_count = replies_count_r.scalar() or 0

    await db.delete(comment)

    if work:
        work.comment_count = max(0, (work.comment_count or 0) - 1 - replies_count)

    await db.commit()
    return {"code": 200, "message": "评论已删除"}


@router.post("/{work_id}/comments/{comment_id}/like")
async def like_comment(
    work_id: int,
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    comment_r = await db.execute(
        select(WorkComment).where(and_(WorkComment.id == comment_id, WorkComment.work_id == work_id))
    )
    comment = comment_r.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")

    existing = await db.execute(
        select(WorkCommentLike).where(
            and_(WorkCommentLike.comment_id == comment_id, WorkCommentLike.user_id == current_user.id)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="已点赞")

    like = WorkCommentLike(comment_id=comment_id, user_id=current_user.id)
    db.add(like)
    comment.like_count = (comment.like_count or 0) + 1
    await db.commit()
    return {"code": 200, "message": "点赞成功", "like_count": comment.like_count}


@router.delete("/{work_id}/comments/{comment_id}/like")
async def unlike_comment(
    work_id: int,
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    existing_r = await db.execute(
        select(WorkCommentLike).where(
            and_(WorkCommentLike.comment_id == comment_id, WorkCommentLike.user_id == current_user.id)
        )
    )
    like = existing_r.scalar_one_or_none()
    if not like:
        raise HTTPException(status_code=400, detail="未点赞")

    await db.delete(like)

    comment_r = await db.execute(select(WorkComment).where(WorkComment.id == comment_id))
    comment = comment_r.scalar_one_or_none()
    if comment:
        comment.like_count = max(0, (comment.like_count or 0) - 1)

    await db.commit()
    return {"code": 200, "message": "取消点赞", "like_count": comment.like_count if comment else 0}

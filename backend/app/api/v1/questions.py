from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func

from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.models.document import Document
from backend.app.models.question import Question, QuestionOption
from backend.app.models.review import ReviewItem
from backend.app.schemas.question import (
    QuestionResponse,
    QuestionUpdateRequest,
    QuestionListResponse,
    OptionSchema,
)
from backend.app.api.deps import get_current_user, get_document_for_user, get_question_for_user
from backend.app.services.document_status import recompute_document_status_and_confidence

router = APIRouter(tags=["Questions"])

@router.get("/documents/{document_id}/questions", response_model=QuestionListResponse)
async def get_document_questions(
    document_id: str,
    status_filter: Optional[str] = Query(None, alias="status"),
    review_required: Optional[bool] = None,
    min_confidence: Optional[float] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    doc = await get_document_for_user(document_id, user, db)

    base_query = select(Question).where(Question.document_id == doc.id)

    if status_filter:
        base_query = base_query.where(Question.status == status_filter.upper())
    if review_required is not None:
        base_query = base_query.where(Question.review_required == review_required)
    if min_confidence is not None:
        base_query = base_query.where(Question.confidence >= min_confidence)
    if search:
        base_query = base_query.where(Question.question_text.ilike(f"%{search}%"))

    # Total count matching filters
    count_stmt = select(func.count()).select_from(base_query.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = (
        base_query
        .options(selectinload(Question.options))
        .order_by(Question.question_number.asc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    result = await db.execute(stmt)
    questions = result.scalars().all()
    has_next = (page * limit) < total

    return QuestionListResponse(
        total=total,
        page=page,
        limit=limit,
        has_next=has_next,
        items=[QuestionResponse.model_validate(q) for q in questions]
    )

@router.get("/questions/{question_id}", response_model=QuestionResponse)
async def get_question(
    question_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Question)
        .options(selectinload(Question.options))
        .where(Question.id == question_id)
    )
    result = await db.execute(stmt)
    q = result.scalars().first()
    if not q:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found.")

    # Check parent document ownership
    _ = await get_document_for_user(q.document_id, user, db)
    return QuestionResponse.model_validate(q)

@router.patch("/questions/{question_id}", response_model=QuestionResponse)
async def update_question(
    question_id: str,
    req: QuestionUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Question)
        .options(selectinload(Question.options))
        .where(Question.id == question_id)
    )
    result = await db.execute(stmt)
    q = result.scalars().first()
    if not q:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found.")

    # Check parent document ownership
    doc = await get_document_for_user(q.document_id, user, db)

    # Apply updates
    if req.question_text is not None:
        q.question_text = req.question_text
    if req.question_type is not None:
        q.question_type = req.question_type
    if req.answer is not None:
        q.answer = req.answer
        q.answer_status = "CONFIRMED"

    if req.status is not None:
        q.status = req.status
    if req.review_required is not None:
        q.review_required = req.review_required
    if req.is_reviewed is not None:
        q.is_reviewed = req.is_reviewed
    else:
        # If user is updating, mark as reviewed
        q.is_reviewed = True
        q.reviewed_by = user.email
        q.reviewed_at = datetime.now(timezone.utc)

    # Update options if provided
    if req.options is not None:
        # Clear existing options
        for old_opt in list(q.options):
            await db.delete(old_opt)
        q.options = []
        for new_opt in req.options:
            opt_obj = QuestionOption(
                question_id=q.id,
                option_key=new_opt.option_key,
                option_text=new_opt.option_text,
            )
            db.add(opt_obj)
            q.options.append(opt_obj)

    # If question marked resolved/reviewed and review_required is False, resolve associated review items
    if q.is_reviewed and not q.review_required:
        q.status = "VERIFIED"
        rev_stmt = select(ReviewItem).where(ReviewItem.question_id == q.id, ReviewItem.is_resolved == False)
        rev_res = await db.execute(rev_stmt)
        for rev_item in rev_res.scalars().all():
            rev_item.is_resolved = True
            rev_item.resolved_by = user.email
            rev_item.resolved_at = datetime.now(timezone.utc)

    await db.commit()

    # Re-evaluate document overall review status and confidence
    await recompute_document_status_and_confidence(db, doc)

    # Reload question with updated options
    stmt_reload = (
        select(Question)
        .options(selectinload(Question.options))
        .where(Question.id == q.id)
    )
    res_reload = await db.execute(stmt_reload)
    updated_q = res_reload.scalars().first()
    return QuestionResponse.model_validate(updated_q)

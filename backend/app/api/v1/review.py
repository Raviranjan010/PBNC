from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.models.document import Document
from backend.app.models.question import Question
from backend.app.models.review import ReviewItem, ExtractionWarning
from backend.app.schemas.review import ReviewItemResponse, WarningResponse
from backend.app.schemas.question import QuestionResponse
from backend.app.api.deps import get_current_user, get_document_for_user

router = APIRouter(tags=["Review"])

@router.get("/documents/{document_id}/review-items")
async def get_document_review_items(
    document_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    doc = await get_document_for_user(document_id, user, db)

    rev_stmt = select(ReviewItem).where(ReviewItem.document_id == doc.id).order_by(ReviewItem.created_at.desc())
    rev_res = await db.execute(rev_stmt)
    review_items = rev_res.scalars().all()

    warn_stmt = select(ExtractionWarning).where(ExtractionWarning.document_id == doc.id).order_by(ExtractionWarning.created_at.desc())
    warn_res = await db.execute(warn_stmt)
    warnings = warn_res.scalars().all()

    return {
        "document_id": doc.id,
        "review_items": [ReviewItemResponse.model_validate(r) for r in review_items],
        "warnings": [WarningResponse.model_validate(w) for w in warnings],
    }

@router.get("/review/queue", response_model=List[QuestionResponse])
async def get_global_review_queue(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns all questions across all documents of the current user that require human review.
    """
    stmt = (
        select(Question)
        .join(Document, Question.document_id == Document.id)
        .options(selectinload(Question.options))
        .where(
            Document.user_id == user.id,
            Question.review_required == True
        )
        .order_by(Question.confidence.asc())
    )
    result = await db.execute(stmt)
    questions = result.scalars().all()
    return [QuestionResponse.model_validate(q) for q in questions]

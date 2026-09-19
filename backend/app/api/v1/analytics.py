from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.models.document import Document
from backend.app.models.question import Question
from backend.app.models.review import ExtractionWarning
from backend.app.schemas.analytics import AnalyticsResponse
from backend.app.api.deps import get_current_user

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("", response_model=AnalyticsResponse)
async def get_analytics(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Computes real database metrics for the current user's document intelligence workspace.
    """
    # Documents stats
    doc_count_stmt = select(func.count(Document.id)).where(Document.user_id == user.id)
    total_docs = (await db.execute(doc_count_stmt)).scalar() or 0

    processed_doc_stmt = select(func.count(Document.id)).where(
        Document.user_id == user.id,
        Document.status.in_(["COMPLETED", "PARTIAL", "REVIEW_REQUIRED"])
    )
    processed_docs = (await db.execute(processed_doc_stmt)).scalar() or 0

    # Questions stats
    q_base = select(Question).join(Document, Question.document_id == Document.id).where(Document.user_id == user.id)
    
    total_q_stmt = select(func.count(Question.id)).join(Document, Question.document_id == Document.id).where(Document.user_id == user.id)
    total_questions = (await db.execute(total_q_stmt)).scalar() or 0

    verified_q_stmt = select(func.count(Question.id)).join(Document, Question.document_id == Document.id).where(
        Document.user_id == user.id,
        Question.status == "VERIFIED"
    )
    verified_questions = (await db.execute(verified_q_stmt)).scalar() or 0

    partial_q_stmt = select(func.count(Question.id)).join(Document, Question.document_id == Document.id).where(
        Document.user_id == user.id,
        Question.status == "PARTIAL"
    )
    partial_questions = (await db.execute(partial_q_stmt)).scalar() or 0

    review_q_stmt = select(func.count(Question.id)).join(Document, Question.document_id == Document.id).where(
        Document.user_id == user.id,
        Question.review_required == True
    )
    review_required_questions = (await db.execute(review_q_stmt)).scalar() or 0

    avg_conf_stmt = select(func.avg(Question.confidence)).join(Document, Question.document_id == Document.id).where(
        Document.user_id == user.id
    )
    avg_conf = (await db.execute(avg_conf_stmt)).scalar() or 0.0

    # Status distribution
    status_distribution = {
        "VERIFIED": verified_questions,
        "PARTIAL": partial_questions,
        "REVIEW_REQUIRED": review_required_questions
    }

    # Warnings by stage
    warn_stmt = (
        select(ExtractionWarning.stage, func.count(ExtractionWarning.id))
        .join(Document, ExtractionWarning.document_id == Document.id)
        .where(Document.user_id == user.id)
        .group_by(ExtractionWarning.stage)
    )
    warn_rows = (await db.execute(warn_stmt)).all()
    warning_counts_by_stage = {stage: count for stage, count in warn_rows}

    return AnalyticsResponse(
        total_documents=total_docs,
        processed_documents=processed_docs,
        total_questions=total_questions,
        review_required_questions=review_required_questions,
        verified_questions=verified_questions,
        partial_questions=partial_questions,
        average_confidence=round(float(avg_conf), 2),
        status_distribution=status_distribution,
        warning_counts_by_stage=warning_counts_by_stage,
    )

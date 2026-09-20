from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from backend.app.models.document import Document
from backend.app.models.question import Question

async def recompute_document_status_and_confidence(db: AsyncSession, doc: Document) -> None:
    """
    Re-evaluates a document's average_confidence and overall status
    based on its current set of questions.
    """
    stmt = select(Question).where(Question.document_id == doc.id)
    res = await db.execute(stmt)
    questions = res.scalars().all()

    if questions:
        avg_conf = round(sum(q.confidence for q in questions) / len(questions), 2)
        doc.average_confidence = avg_conf
        has_review_required = any(q.review_required for q in questions)

        if has_review_required:
            doc.status = "REVIEW_REQUIRED"
        elif avg_conf >= 0.90:
            doc.status = "COMPLETED"
        else:
            doc.status = "PARTIAL"
    
    await db.commit()

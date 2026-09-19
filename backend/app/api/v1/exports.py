import csv
import io
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.models.document import Document
from backend.app.models.question import Question
from backend.app.schemas.export import ExportDocumentJSON, ExportQuestion, ExportOption
from backend.app.api.deps import get_current_user, get_document_for_user

router = APIRouter(prefix="/documents", tags=["Exports"])

@router.get("/{document_id}/export/json")
async def export_document_json(
    document_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    doc = await get_document_for_user(document_id, user, db)

    stmt = (
        select(Question)
        .options(selectinload(Question.options))
        .where(Question.document_id == doc.id)
        .order_by(Question.question_number.asc())
    )
    result = await db.execute(stmt)
    questions = result.scalars().all()

    export_questions = []
    for q in questions:
        opts = [ExportOption(key=o.option_key, text=o.option_text) for o in q.options]
        export_questions.append(ExportQuestion(
            id=q.id,
            question_number=q.question_number,
            question_text=q.question_text,
            question_type=q.question_type,
            options=opts,
            answer=q.answer,
            answer_status=q.answer_status,
            confidence=q.confidence,
            status=q.status,
            review_required=q.review_required,
            source_pages=q.source_pages or [],
        ))

    export_doc = ExportDocumentJSON(
        document_id=doc.id,
        filename=doc.original_filename,
        page_count=doc.page_count,
        extracted_at=datetime.now(timezone.utc).isoformat(),
        average_confidence=doc.average_confidence,
        questions=export_questions,
    )

    json_data = export_doc.model_dump_json(indent=2)
    filename = f"export_{doc.filename}.json"
    
    return Response(
        content=json_data,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@router.get("/{document_id}/export/csv")
async def export_document_csv(
    document_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    doc = await get_document_for_user(document_id, user, db)

    stmt = (
        select(Question)
        .options(selectinload(Question.options))
        .where(Question.document_id == doc.id)
        .order_by(Question.question_number.asc())
    )
    result = await db.execute(stmt)
    questions = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Question Number",
        "Question Text",
        "Question Type",
        "Options",
        "Answer",
        "Answer Status",
        "Confidence",
        "Status",
        "Review Required",
        "Source Pages"
    ])

    for q in questions:
        opts_str = " | ".join([f"({o.option_key}) {o.option_text}" for o in q.options])
        pages_str = ", ".join(map(str, q.source_pages or []))
        writer.writerow([
            q.question_number,
            q.question_text,
            q.question_type,
            opts_str,
            q.answer or "",
            q.answer_status,
            f"{q.confidence:.2f}",
            q.status,
            "Yes" if q.review_required else "No",
            pages_str,
        ])

    csv_data = output.getvalue()
    filename = f"export_{doc.filename}.csv"

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

import os
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Response, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func, delete

from backend.app.core.database import get_db
from backend.app.core.storage import storage, sanitize_filename
from backend.app.core.rate_limiter import rate_limit_upload
from backend.app.models.user import User
from backend.app.models.document import Document, DocumentPage, DocumentRelationship
from backend.app.models.job import ProcessingJob
from backend.app.models.question import Question, QuestionOption
from backend.app.models.answer import AnswerKey
from backend.app.models.review import ReviewItem, ExtractionWarning
from backend.app.services.answer_matcher import AnswerMatcher
from backend.app.services.confidence import ConfidenceCalculator
from backend.app.services.document_status import recompute_document_status_and_confidence
from backend.app.schemas.document import (
    DocumentUploadResponse,
    DocumentResponse,
    PaginatedDocumentResponse,
    DocumentDetailResponse,
    DocumentPageResponse,
    ProcessingStatusResponse,
)
from backend.app.schemas.answer import RelatedDocumentRequest, RelatedDocumentResponse
from backend.app.services.validator import DocumentValidator, DocumentValidationError
from backend.app.api.deps import get_current_user, get_document_for_user
from backend.app.worker import dispatch_document_task

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    file: UploadFile = File(...),
    user: User = Depends(rate_limit_upload),
    db: AsyncSession = Depends(get_db)
):
    """
    Accepts file upload, executes strict validation (magic bytes, size, integrity),
    saves file safely, creates database records, and queues async extraction.
    Rate limited per authenticated user.
    """
    content = await file.read()
    filename = file.filename or "uploaded_document.pdf"

    # Step 1: Validate file
    try:
        file_type, mime_type, page_count = DocumentValidator.validate_file(filename, content)
    except DocumentValidationError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )

    # Step 2: Safe storage
    doc_id = str(uuid.uuid4())
    relative_path, file_size = await storage.save_file(content, user.id, doc_id, filename)

    # Step 3: Database persistence
    doc = Document(
        id=doc_id,
        user_id=user.id,
        filename=sanitize_filename(filename),
        original_filename=filename,
        file_type=file_type,
        mime_type=mime_type,
        file_size_bytes=file_size,
        page_count=page_count,
        storage_path=relative_path,
        status="QUEUED",
    )
    db.add(doc)

    job_id = str(uuid.uuid4())
    job = ProcessingJob(
        id=job_id,
        document_id=doc_id,
        status="QUEUED",
        current_step="QUEUED",
        step_details=[{
            "step": "QUEUED",
            "message": "Document received, validated, and queued for asynchronous processing.",
        }],
    )
    db.add(job)
    await db.commit()

    # Step 4: Dispatch async worker task
    dispatch_document_task(doc_id, job_id)

    return DocumentUploadResponse(
        document_id=doc_id,
        job_id=job_id,
        filename=doc.original_filename,
        status="QUEUED",
        message="Document uploaded successfully and queued for processing."
    )

@router.get("", response_model=PaginatedDocumentResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lists uploaded documents for the current user with pagination."""
    count_stmt = select(func.count(Document.id)).where(Document.user_id == user.id)
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = (
        select(Document)
        .where(Document.user_id == user.id)
        .order_by(Document.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    result = await db.execute(stmt)
    items = result.scalars().all()
    has_next = (page * limit) < total

    return PaginatedDocumentResponse(
        total=total,
        page=page,
        limit=limit,
        has_next=has_next,
        items=[DocumentResponse.model_validate(doc) for doc in items]
    )

@router.post("/{document_id}/retry", response_model=DocumentUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def retry_document_processing(
    document_id: str,
    user: User = Depends(rate_limit_upload),
    db: AsyncSession = Depends(get_db)
):
    """
    Deliberately retries extraction for a failed, partial, or review-required document.
    Performs transactional cleanup of prior extractions to guarantee idempotency.
    Rate limited per authenticated user.
    """
    doc = await get_document_for_user(document_id, user, db)

    # Validates document is in a retryable state
    if doc.status == "COMPLETED" and (doc.average_confidence or 0) >= 0.90:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document is already completed with high confidence and cannot be retried."
        )
    if doc.status in ["QUEUED", "PROCESSING"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document is currently being processed."
        )

    # Transactional cleanup of previous extraction results
    await db.execute(delete(Question).where(Question.document_id == doc.id))
    await db.execute(delete(ExtractionWarning).where(ExtractionWarning.document_id == doc.id))
    await db.execute(delete(ReviewItem).where(ReviewItem.document_id == doc.id))
    await db.execute(delete(AnswerKey).where(AnswerKey.document_id == doc.id))

    doc.status = "QUEUED"
    doc.average_confidence = None

    job_id = str(uuid.uuid4())
    job = ProcessingJob(
        id=job_id,
        document_id=doc.id,
        status="QUEUED",
        current_step="INITIALIZING",
        step_details=[{
            "step": "QUEUED",
            "message": "Document retry initiated and queued for re-extraction.",
        }],
    )
    db.add(job)
    await db.commit()

    dispatch_document_task(doc.id, job.id)

    return DocumentUploadResponse(
        document_id=doc.id,
        job_id=job.id,
        filename=doc.original_filename,
        status="QUEUED",
        message="Document retry queued successfully."
    )

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Deletes a document, its physical storage file and rendered pages,
    and cascades deletion to all database records.
    """
    doc = await get_document_for_user(document_id, user, db)

    # Delete storage file
    if doc.storage_path:
        await storage.delete_file(doc.storage_path)

    # Delete rendered page images if any
    pages_stmt = select(DocumentPage).where(DocumentPage.document_id == doc.id)
    pages_res = await db.execute(pages_stmt)
    for p in pages_res.scalars().all():
        if p.image_path:
            await storage.delete_file(p.image_path)

    # Delete document record (foreign keys cascade in DB)
    await db.delete(doc)
    await db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document_details(
    document_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    doc = await get_document_for_user(document_id, user, db)

    # Count questions
    q_count_stmt = select(func.count(Question.id)).where(Question.document_id == doc.id)
    q_count = (await db.execute(q_count_stmt)).scalar() or 0

    # Count review required
    rev_count_stmt = select(func.count(Question.id)).where(
        Question.document_id == doc.id,
        Question.review_required == True
    )
    rev_count = (await db.execute(rev_count_stmt)).scalar() or 0

    # Count warnings
    warn_count_stmt = select(func.count(ExtractionWarning.id)).where(ExtractionWarning.document_id == doc.id)
    warn_count = (await db.execute(warn_count_stmt)).scalar() or 0

    # Fetch pages
    pages_stmt = select(DocumentPage).where(DocumentPage.document_id == doc.id).order_by(DocumentPage.page_number)
    pages_res = await db.execute(pages_stmt)
    pages = pages_res.scalars().all()

    page_responses = [
        DocumentPageResponse(
            id=p.id,
            page_number=p.page_number,
            extracted_text=p.extracted_text,
            width=p.width,
            height=p.height,
            image_url=f"/api/v1/documents/{doc.id}/pages/{p.page_number}" if p.image_path else None
        )
        for p in pages
    ]

    # Fetch related documents
    rel_stmt = select(DocumentRelationship).where(
        (DocumentRelationship.parent_document_id == doc.id) |
        (DocumentRelationship.related_document_id == doc.id)
    )
    rels = (await db.execute(rel_stmt)).scalars().all()
    related_ids = [
        r.related_document_id if r.parent_document_id == doc.id else r.parent_document_id
        for r in rels
    ]

    return DocumentDetailResponse(
        id=doc.id,
        user_id=doc.user_id,
        filename=doc.filename,
        original_filename=doc.original_filename,
        file_type=doc.file_type,
        mime_type=doc.mime_type,
        file_size_bytes=doc.file_size_bytes,
        page_count=doc.page_count,
        status=doc.status,
        average_confidence=doc.average_confidence,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        questions_count=q_count,
        review_required_count=rev_count,
        warnings_count=warn_count,
        pages=page_responses,
        related_document_ids=related_ids,
    )

@router.get("/{document_id}/status", response_model=ProcessingStatusResponse)
async def get_document_status(
    document_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    doc = await get_document_for_user(document_id, user, db)
    
    # Get latest processing job
    stmt = (
        select(ProcessingJob)
        .where(ProcessingJob.document_id == doc.id)
        .order_by(ProcessingJob.created_at.desc())
    )
    result = await db.execute(stmt)
    job = result.scalars().first()

    if not job:
        return ProcessingStatusResponse(
            document_id=doc.id,
            job_id="",
            status=doc.status,
            current_step=doc.status,
            step_details=[],
        )

    return ProcessingStatusResponse(
        document_id=doc.id,
        job_id=job.id,
        status=job.status,
        current_step=job.current_step,
        step_details=job.step_details or [],
        error_message=job.error_message,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )

@router.get("/{document_id}/pages/{page_num}")
async def get_page_image(
    document_id: str,
    page_num: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    doc = await get_document_for_user(document_id, user, db)
    
    stmt = select(DocumentPage).where(
        DocumentPage.document_id == doc.id,
        DocumentPage.page_number == page_num
    )
    result = await db.execute(stmt)
    page = result.scalars().first()

    if not page or not page.image_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rendered image for page {page_num} was not found."
        )

    file_path = storage.get_file_path(page.image_path)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image file missing from storage.")

    return FileResponse(file_path, media_type="image/png")

@router.post("/{document_id}/related", response_model=RelatedDocumentResponse)
async def associate_related_document(
    document_id: str,
    req: RelatedDocumentRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    doc = await get_document_for_user(document_id, user, db)
    related_doc = await get_document_for_user(req.related_document_id, user, db)

    # Validate processing state if relationship is ANSWER_KEY
    if req.relationship_type == "ANSWER_KEY":
        if related_doc.status in ["QUEUED", "PROCESSING"]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The related answer-key document must finish processing before association."
            )
        if related_doc.status == "FAILED":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="The related answer-key document failed processing and cannot be used as an answer key."
            )

    # Create relationship if it doesn't already exist
    rel_stmt = select(DocumentRelationship).where(
        DocumentRelationship.parent_document_id == doc.id,
        DocumentRelationship.related_document_id == related_doc.id,
        DocumentRelationship.relationship_type == req.relationship_type
    )
    rel_res = await db.execute(rel_stmt)
    rel = rel_res.scalars().first()
    if not rel:
        rel = DocumentRelationship(
            parent_document_id=doc.id,
            related_document_id=related_doc.id,
            relationship_type=req.relationship_type,
        )
        db.add(rel)
        await db.commit()
        await db.refresh(rel)

    resolved_count = 0
    unresolved_count = 0
    invalid_count = 0
    message = "Document relationship established."

    if req.relationship_type == "ANSWER_KEY":
        pages_stmt = (
            select(DocumentPage)
            .where(DocumentPage.document_id == related_doc.id)
            .order_by(DocumentPage.page_number)
        )
        pages_res = await db.execute(pages_stmt)
        pages = pages_res.scalars().all()

        pages_payload = [
            {
                "page_number": p.page_number,
                "text": ((p.extracted_text or "") + "\n" + (p.ocr_text or "")).strip(),
            }
            for p in pages
        ]

        detected_key = AnswerMatcher.find_answer_key_in_pages(pages_payload)
        if not detected_key:
            message = "Relationship established, but no answer key structure could be parsed from the related document."
        else:
            # Persist AnswerKey record associated with the PARENT document
            ak_record = AnswerKey(
                document_id=doc.id,
                raw_key_text=detected_key.raw_text,
                detected_format=detected_key.detected_format,
                source_page=detected_key.source_page,
                parsed_mappings=detected_key.mappings,
            )
            db.add(ak_record)
            await db.commit()

            # Load parent document questions with options and warnings
            q_stmt = (
                select(Question)
                .options(selectinload(Question.options), selectinload(Question.warnings))
                .where(Question.document_id == doc.id)
                .order_by(Question.question_number.asc())
            )
            q_res = await db.execute(q_stmt)
            parent_questions = q_res.scalars().all()

            for q in parent_questions:
                q_num = str(q.question_number).strip()
                if q_num in detected_key.mappings:
                    matched_ans = detected_key.mappings[q_num]
                    # Validate that the option actually exists if options are present
                    has_option = any(opt.option_key == matched_ans for opt in q.options) if q.options else True
                    if q.options and not has_option:
                        q.answer = None
                        q.answer_status = "INVALID"
                        q.review_required = True
                        q.status = "REVIEW_REQUIRED"
                        invalid_count += 1
                        warning = ExtractionWarning(
                            document_id=doc.id,
                            question_id=q.id,
                            stage="ANSWER_KEY",
                            warning_code="INVALID_ANSWER_KEY",
                            message=f"Answer key maps Question {q_num} to option '{matched_ans}', but available options are {', '.join(o.option_key for o in q.options)}.",
                            severity="WARNING",
                        )
                        db.add(warning)
                        review_item = ReviewItem(
                            document_id=doc.id,
                            question_id=q.id,
                            issue_type="INVALID_ANSWER_KEY",
                            description=f"Answer key maps Question {q_num} to option '{matched_ans}', which does not match any available options.",
                        )
                        db.add(review_item)
                    else:
                        q.answer = matched_ans
                        q.answer_status = "CONFIRMED"
                        q.answer_source_document_id = related_doc.id
                        q.answer_source_page = detected_key.source_page
                        # Recalculate confidence for question
                        first_page = q.source_pages[0] if q.source_pages else 1
                        q.confidence = ConfidenceCalculator.calculate_question_confidence(
                            question=q,
                            page_ocr_conf=1.0,
                            is_digital=True
                        )
                        q.status, q.review_required = ConfidenceCalculator.determine_status_and_review(
                            q.confidence, has_warnings=bool(q.warnings), is_uncertain=False
                        )
                        resolved_count += 1
                else:
                    if q.answer_status != "CONFIRMED":
                        q.answer_status = "NOT_FOUND"
                        q.answer = None
                    unresolved_count += 1

            await db.commit()
            await recompute_document_status_and_confidence(db, doc)
            message = f"Answer key associated successfully. Resolved {resolved_count} answers, {unresolved_count} unresolved, {invalid_count} invalid."

    return RelatedDocumentResponse(
        id=rel.id,
        parent_document_id=rel.parent_document_id,
        related_document_id=rel.related_document_id,
        relationship_type=rel.relationship_type,
        created_at=rel.created_at,
        resolved_count=resolved_count,
        unresolved_count=unresolved_count,
        invalid_count=invalid_count,
        message=message,
    )


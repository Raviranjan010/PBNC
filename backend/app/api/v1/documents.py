import os
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func

from backend.app.core.database import get_db
from backend.app.core.storage import storage, sanitize_filename
from backend.app.models.user import User
from backend.app.models.document import Document, DocumentPage, DocumentRelationship
from backend.app.models.job import ProcessingJob
from backend.app.models.question import Question
from backend.app.models.review import ReviewItem, ExtractionWarning
from backend.app.schemas.document import (
    DocumentUploadResponse,
    DocumentResponse,
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
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Accepts file upload, executes strict validation (magic bytes, size, integrity),
    saves file safely, creates database records, and queues async extraction.
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

@router.get("", response_model=List[DocumentResponse])
async def list_documents(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Document)
        .where(Document.user_id == user.id)
        .order_by(Document.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()

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

    # Create relationship
    rel = DocumentRelationship(
        parent_document_id=doc.id,
        related_document_id=related_doc.id,
        relationship_type=req.relationship_type,
    )
    db.add(rel)
    await db.commit()
    await db.refresh(rel)
    return rel

from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime
from backend.app.schemas.question import QuestionResponse
from backend.app.schemas.review import ReviewItemResponse, WarningResponse
from backend.app.schemas.answer import AnswerKeyResponse

class DocumentUploadResponse(BaseModel):
    document_id: str
    job_id: str
    filename: str
    status: str
    message: str

class DocumentPageResponse(BaseModel):
    id: str
    page_number: int
    extracted_text: Optional[str] = None
    width: Optional[float] = None
    height: Optional[float] = None
    image_url: Optional[str] = None

    class Config:
        from_attributes = True

class DocumentResponse(BaseModel):
    id: str
    user_id: str
    filename: str
    original_filename: str
    file_type: str
    mime_type: str
    file_size_bytes: int
    page_count: int
    status: str
    average_confidence: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PaginatedDocumentResponse(BaseModel):
    total: int
    page: int = 1
    limit: int = 20
    has_next: bool = False
    items: List[DocumentResponse]

class DocumentDetailResponse(DocumentResponse):
    questions_count: int = 0
    review_required_count: int = 0
    warnings_count: int = 0
    pages: List[DocumentPageResponse] = []
    related_document_ids: List[str] = []

class ProcessingStatusResponse(BaseModel):
    document_id: str
    job_id: str
    status: str
    current_step: str
    step_details: List[dict] = []
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

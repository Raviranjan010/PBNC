from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class OptionSchema(BaseModel):
    id: Optional[str] = None
    option_key: str
    option_text: str

    class Config:
        from_attributes = True

class QuestionResponse(BaseModel):
    id: str
    document_id: str
    question_number: str
    question_text: str
    question_type: str
    options: List[OptionSchema] = []
    answer: Optional[str] = None
    answer_status: str
    answer_source_page: Optional[int] = None
    confidence: float
    status: str
    review_required: bool
    is_reviewed: bool
    source_pages: List[int] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class QuestionUpdateRequest(BaseModel):
    question_text: Optional[str] = None
    question_type: Optional[str] = None
    options: Optional[List[OptionSchema]] = None
    answer: Optional[str] = None
    status: Optional[str] = None  # VERIFIED, PARTIAL, REVIEW_REQUIRED
    review_required: Optional[bool] = None
    is_reviewed: Optional[bool] = None

class QuestionListResponse(BaseModel):
    total: int
    items: List[QuestionResponse]

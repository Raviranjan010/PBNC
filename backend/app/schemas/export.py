from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class ExportOption(BaseModel):
    key: str
    text: str

class ExportQuestion(BaseModel):
    id: str
    question_number: str
    question_text: str
    question_type: str
    options: List[ExportOption] = []
    answer: Optional[str] = None
    answer_status: str
    confidence: float
    status: str
    review_required: bool
    source_pages: List[int] = []

class ExportDocumentJSON(BaseModel):
    document_id: str
    filename: str
    page_count: int
    extracted_at: str
    average_confidence: Optional[float] = None
    questions: List[ExportQuestion] = []

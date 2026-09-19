from pydantic import BaseModel
from typing import Dict, Optional, Any
from datetime import datetime

class AnswerKeyResponse(BaseModel):
    id: str
    document_id: str
    raw_key_text: Optional[str] = None
    detected_format: Optional[str] = None
    source_page: Optional[int] = None
    parsed_mappings: Dict[str, str] = {}
    created_at: datetime

    class Config:
        from_attributes = True

class RelatedDocumentRequest(BaseModel):
    related_document_id: str
    relationship_type: str = "ANSWER_KEY"

class RelatedDocumentResponse(BaseModel):
    id: str
    parent_document_id: str
    related_document_id: str
    relationship_type: str
    created_at: datetime

    class Config:
        from_attributes = True

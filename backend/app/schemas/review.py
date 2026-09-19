from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ReviewItemResponse(BaseModel):
    id: str
    document_id: str
    question_id: Optional[str] = None
    issue_type: str
    description: str
    is_resolved: bool
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class WarningResponse(BaseModel):
    id: str
    document_id: str
    question_id: Optional[str] = None
    stage: str
    warning_code: str
    message: str
    severity: str
    created_at: datetime

    class Config:
        from_attributes = True

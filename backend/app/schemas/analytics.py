from pydantic import BaseModel
from typing import Dict, List

class AnalyticsResponse(BaseModel):
    total_documents: int
    processed_documents: int
    total_questions: int
    review_required_questions: int
    verified_questions: int
    partial_questions: int
    average_confidence: float
    status_distribution: Dict[str, int]
    warning_counts_by_stage: Dict[str, int]

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class ParsedOption(BaseModel):
    key: str
    text: str

class ParsedQuestion(BaseModel):
    question_number: str
    question_text: str
    question_type: str = "MCQ"
    options: List[ParsedOption] = []
    answer: Optional[str] = None
    answer_status: str = "CONFIRMED"  # CONFIRMED, UNCERTAIN, NOT_FOUND
    answer_source_page: Optional[int] = None
    answer_source_document_id: Optional[str] = None
    source_pages: List[int] = []
    confidence: float = 0.85
    warnings: List[str] = []

class AIProvider(ABC):
    @abstractmethod
    async def extract_structured_questions(
        self, pages_text: List[Dict[str, Any]]
    ) -> List[ParsedQuestion]:
        """
        Takes list of {'page_number': int, 'text': str} and returns validated structured questions.
        """
        pass

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class ReviewItem(Base):
    __tablename__ = "review_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(String(36), ForeignKey("questions.id", ondelete="CASCADE"), nullable=True, index=True)
    issue_type = Column(String(100), nullable=False)  # LOW_CONFIDENCE, UNCERTAIN_ANSWER, MISSING_OPTIONS, OCR_AMBIGUITY
    description = Column(Text, nullable=False)
    is_resolved = Column(Boolean, default=False, nullable=False, index=True)
    resolved_by = Column(String(255), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    document = relationship("Document", back_populates="review_items")
    question = relationship("Question", back_populates="review_items")

class ExtractionWarning(Base):
    __tablename__ = "extraction_warnings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(String(36), ForeignKey("questions.id", ondelete="CASCADE"), nullable=True, index=True)
    stage = Column(String(50), nullable=False)  # OCR, PARSING, MATCHING, VALIDATION
    warning_code = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(20), default="WARNING", nullable=False)  # INFO, WARNING, ERROR
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    document = relationship("Document", back_populates="warnings")
    question = relationship("Question", back_populates="warnings")

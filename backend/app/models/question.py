import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class Question(Base):
    __tablename__ = "questions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    question_number = Column(String(50), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), default="MCQ", nullable=False)  # MCQ, SHORT, TRUE_FALSE
    
    answer = Column(String(100), nullable=True)
    answer_status = Column(String(50), default="CONFIRMED", nullable=False)  # CONFIRMED, UNCERTAIN, NOT_FOUND
    answer_source_page = Column(Integer, nullable=True)
    answer_source_document_id = Column(String(36), nullable=True)
    
    confidence = Column(Float, default=0.0, nullable=False)
    status = Column(String(50), default="REVIEW_REQUIRED", nullable=False)  # VERIFIED, PARTIAL, REVIEW_REQUIRED
    review_required = Column(Boolean, default=False, nullable=False, index=True)
    is_reviewed = Column(Boolean, default=False, nullable=False)
    reviewed_by = Column(String(255), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    
    source_pages = Column(JSON, default=list, nullable=False)  # e.g. [1, 2]
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    document = relationship("Document", back_populates="questions")
    options = relationship("QuestionOption", back_populates="question", cascade="all, delete-orphan", order_by="QuestionOption.option_key")
    review_items = relationship("ReviewItem", back_populates="question", cascade="all, delete-orphan")
    warnings = relationship("ExtractionWarning", back_populates="question", cascade="all, delete-orphan")

class QuestionOption(Base):
    __tablename__ = "question_options"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    question_id = Column(String(36), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    option_key = Column(String(10), nullable=False)  # A, B, C, D
    option_text = Column(Text, nullable=False)

    question = relationship("Question", back_populates="options")

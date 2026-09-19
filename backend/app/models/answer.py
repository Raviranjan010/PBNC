import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class AnswerKey(Base):
    __tablename__ = "answer_keys"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    raw_key_text = Column(Text, nullable=True)
    detected_format = Column(String(50), nullable=True)  # TABLE, INLINE, LIST
    source_page = Column(Integer, nullable=True)
    parsed_mappings = Column(JSON, default=dict, nullable=False)  # {"1": "A", "2": "B"}
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    document = relationship("Document", back_populates="answer_keys")

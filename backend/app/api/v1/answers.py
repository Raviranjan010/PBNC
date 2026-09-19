from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.models.answer import AnswerKey
from backend.app.schemas.answer import AnswerKeyResponse
from backend.app.api.deps import get_current_user, get_document_for_user

router = APIRouter(prefix="/documents", tags=["Answers"])

@router.get("/{document_id}/answers", response_model=List[AnswerKeyResponse])
async def get_document_answers(
    document_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    doc = await get_document_for_user(document_id, user, db)

    stmt = select(AnswerKey).where(AnswerKey.document_id == doc.id).order_by(AnswerKey.created_at.asc())
    result = await db.execute(stmt)
    keys = result.scalars().all()
    return [AnswerKeyResponse.model_validate(k) for k in keys]

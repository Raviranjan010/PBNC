from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.core.database import get_db
from backend.app.core.security import decode_access_token
from backend.app.models.user import User
from backend.app.models.document import Document
from backend.app.models.question import Question

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalars().first()
    if user is None or not user.is_active:
        raise credentials_exception
    return user

async def get_document_for_user(
    document_id: str,
    user: User,
    db: AsyncSession
) -> Document:
    """
    Enforces strict ownership authorization:
    Raises 404 if document doesn't exist, and 403 if it belongs to another user.
    """
    stmt = select(Document).where(Document.id == document_id)
    result = await db.execute(stmt)
    doc = result.scalars().first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} was not found."
        )
    if doc.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You do not have permission to view or modify this document."
        )
    return doc

async def get_question_for_user(
    question_id: str,
    user: User,
    db: AsyncSession
) -> Question:
    """
    Retrieves question while verifying ownership of the parent document.
    """
    stmt = select(Question).where(Question.id == question_id)
    result = await db.execute(stmt)
    question = result.scalars().first()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question with ID {question_id} was not found."
        )
    
    # Check document ownership
    doc_stmt = select(Document).where(Document.id == question.document_id)
    doc_result = await db.execute(doc_stmt)
    doc = doc_result.scalars().first()
    if not doc or doc.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You do not have permission to access this question."
        )
    return question

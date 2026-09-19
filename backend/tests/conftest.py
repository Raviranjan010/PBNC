import os
import sys
import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.main import app
from backend.app.core.database import Base, get_db
from backend.app.core.security import get_password_hash, create_access_token
from backend.app.models.user import User

import os
from backend.app.core.config import settings
settings.CELERY_TASK_ALWAYS_EAGER = True

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_papermind.db"

test_async_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
)

TestAsyncSessionLocal = async_sessionmaker(
    bind=test_async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.core import database

test_sync_engine = create_engine("sqlite:///./test_papermind.db", echo=False)
database.SyncSessionLocal = sessionmaker(bind=test_sync_engine, autocommit=False, autoflush=False)

async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestAsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True, scope="function")
async def prepare_database():
    async with test_async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def test_user_a(client: AsyncClient) -> dict:
    async with TestAsyncSessionLocal() as session:
        user = User(
            id="user-aaa-111",
            email="usera@papermind.io",
            hashed_password=get_password_hash("Password123!"),
            full_name="User Alpha",
            is_active=True,
        )
        session.add(user)
        await session.commit()
    token = create_access_token(subject="user-aaa-111")
    return {"id": "user-aaa-111", "email": "usera@papermind.io", "token": token, "headers": {"Authorization": f"Bearer {token}"}}

@pytest.fixture
async def test_user_b(client: AsyncClient) -> dict:
    async with TestAsyncSessionLocal() as session:
        user = User(
            id="user-bbb-222",
            email="userb@papermind.io",
            hashed_password=get_password_hash("Password123!"),
            full_name="User Beta",
            is_active=True,
        )
        session.add(user)
        await session.commit()
    token = create_access_token(subject="user-bbb-222")
    return {"id": "user-bbb-222", "email": "userb@papermind.io", "token": token, "headers": {"Authorization": f"Bearer {token}"}}

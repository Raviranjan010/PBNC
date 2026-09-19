from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine
from backend.app.core.config import settings
from typing import AsyncGenerator

# Async Engine for FastAPI
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Sync Engine for Celery / background worker tasks
sync_db_url = settings.SYNC_DATABASE_URL
if not sync_db_url:
    if settings.DATABASE_URL.startswith("sqlite+aiosqlite"):
        sync_db_url = settings.DATABASE_URL.replace("sqlite+aiosqlite", "sqlite")
    elif settings.DATABASE_URL.startswith("postgresql+asyncpg"):
        sync_db_url = settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql+psycopg2")
    else:
        sync_db_url = settings.DATABASE_URL

sync_engine = create_engine(sync_db_url, echo=False)
SyncSessionLocal = sessionmaker(bind=sync_engine, autocommit=False, autoflush=False)

Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

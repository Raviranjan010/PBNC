import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import settings
from backend.app.core.database import async_engine, Base
from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.documents import router as documents_router
from backend.app.api.v1.questions import router as questions_router
from backend.app.api.v1.answers import router as answers_router
from backend.app.api.v1.review import router as review_router
from backend.app.api.v1.exports import router as exports_router
from backend.app.api.v1.analytics import router as analytics_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("papermind")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application starting up. Database schema managed by Alembic migrations.")
    yield
    # Shutdown
    await async_engine.dispose()
    logger.info("Database connections closed.")

app = FastAPI(
    title=f"{settings.PROJECT_NAME} - Document Intelligence & Question Extraction API",
    description="Production-grade Document Intelligence & Question Extraction Platform for Pragati Bharti Round 2.",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers for clean structured errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error processing {request.method} {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred while processing the request."}
    )

# Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(documents_router, prefix=settings.API_V1_STR)
app.include_router(questions_router, prefix=settings.API_V1_STR)
app.include_router(answers_router, prefix=settings.API_V1_STR)
app.include_router(review_router, prefix=settings.API_V1_STR)
app.include_router(exports_router, prefix=settings.API_V1_STR)
app.include_router(analytics_router, prefix=settings.API_V1_STR)

@app.get("/health", tags=["Health"])
async def health_check():
    """Service liveness probe endpoint."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

@app.get("/health/ready", tags=["Health"])
async def readiness_check():
    """
    Readiness probe verifying real dependencies:
    - Database reachability (SELECT 1)
    - Redis broker / ping
    - Safe storage writability
    """
    import os
    checks = {}
    is_ready = True

    # 1. Database check
    try:
        from sqlalchemy import text
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = {"status": "ok"}
    except Exception as e:
        is_ready = False
        checks["database"] = {"status": "error", "detail": str(e)}

    # 2. Redis check
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.REDIS_URL, socket_timeout=2.0)
        pong = await r.ping()
        await r.aclose()
        if pong:
            checks["redis"] = {"status": "ok"}
        else:
            is_ready = False
            checks["redis"] = {"status": "error", "detail": "ping failed"}
    except Exception as e:
        is_ready = False
        checks["redis"] = {"status": "error", "detail": str(e)}

    # 3. Storage check
    try:
        storage_dir = settings.STORAGE_DIR
        os.makedirs(storage_dir, exist_ok=True)
        probe_file = os.path.join(storage_dir, ".readiness_probe")
        with open(probe_file, "w") as f:
            f.write("probe")
        if os.path.exists(probe_file):
            os.remove(probe_file)
        checks["storage"] = {"status": "ok"}
    except Exception as e:
        is_ready = False
        checks["storage"] = {"status": "error", "detail": str(e)}

    payload = {
        "status": "ready" if is_ready else "unready",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
    }

    if not is_ready:
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=payload)
    return JSONResponse(status_code=status.HTTP_200_OK, content=payload)

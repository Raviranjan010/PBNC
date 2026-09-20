import time
import logging
from typing import Optional
from fastapi import Request, HTTPException, status, Depends
from backend.app.core.config import settings
from backend.app.api.deps import get_current_user
from backend.app.models.user import User

logger = logging.getLogger("papermind.ratelimit")

# In-memory store fallback when Redis is unreachable or during unit tests
_memory_cache: dict[str, list[float]] = {}

def clear_rate_limit_cache():
    """Helper for testing to reset rate limit memory cache."""
    _memory_cache.clear()

async def apply_rate_limit(key: str, limit: int, window_seconds: int = 60) -> None:
    now = time.time()
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.REDIS_URL, socket_timeout=1.0)
        current = await r.incr(key)
        if current == 1:
            await r.expire(key, window_seconds)
        await r.aclose()
        if current > limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: maximum {limit} requests per {window_seconds}s.",
                headers={"Retry-After": str(window_seconds)}
            )
        return
    except HTTPException:
        raise
    except Exception as e:
        logger.debug(f"Redis rate limiter fallback to in-memory: {e}")

    # In-memory fallback
    window_start = now - window_seconds
    timestamps = [t for t in _memory_cache.get(key, []) if t > window_start]
    if len(timestamps) >= limit:
        _memory_cache[key] = timestamps
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: maximum {limit} requests per {window_seconds}s.",
            headers={"Retry-After": str(window_seconds)}
        )
    timestamps.append(now)
    _memory_cache[key] = timestamps

async def rate_limit_auth(request: Request) -> None:
    """Rate limits unauthenticated auth endpoints (register/login) by client IP."""
    client_ip = request.client.host if request.client else "unknown"
    # Support reverse proxy header
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    key = f"ratelimit:auth:{client_ip}"
    await apply_rate_limit(key, limit=settings.RATE_LIMIT_AUTH_PER_MINUTE, window_seconds=60)

async def rate_limit_upload(user: User = Depends(get_current_user)) -> User:
    """Rate limits authenticated document upload & retry operations by user ID."""
    key = f"ratelimit:upload:{user.id}"
    await apply_rate_limit(key, limit=settings.RATE_LIMIT_UPLOAD_PER_MINUTE, window_seconds=60)
    return user

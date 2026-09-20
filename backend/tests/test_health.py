import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "PaperMind"
    assert "timestamp" in data

@pytest.mark.asyncio
async def test_health_ready_success(client: AsyncClient, monkeypatch):
    # Mock redis ping to succeed
    class DummyRedis:
        async def ping(self):
            return True
        async def aclose(self):
            pass

    import redis.asyncio as aioredis
    monkeypatch.setattr(aioredis, "from_url", lambda *args, **kwargs: DummyRedis())

    response = await client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["checks"]["database"]["status"] == "ok"
    assert data["checks"]["redis"]["status"] == "ok"
    assert data["checks"]["storage"]["status"] == "ok"

@pytest.mark.asyncio
async def test_health_ready_dependency_failure(client: AsyncClient, monkeypatch):
    # Mock redis ping to fail / raise exception
    class FailingRedis:
        async def ping(self):
            raise ConnectionError("Redis cluster unreachable")
        async def aclose(self):
            pass

    import redis.asyncio as aioredis
    monkeypatch.setattr(aioredis, "from_url", lambda *args, **kwargs: FailingRedis())

    response = await client.get("/health/ready")
    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "unready"
    assert data["checks"]["redis"]["status"] == "error"
    assert "unreachable" in data["checks"]["redis"]["detail"]

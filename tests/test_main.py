import pytest
from httpx import AsyncClient
from src.main import app
from src.core.context import application_context, AppContext
from fakeredis.aioredis import FakeRedis
from contextlib import asynccontextmanager

pytestmark = pytest.mark.asyncio


@asynccontextmanager
async def mock_application_context():
    redis_client = FakeRedis()
    ctx = AppContext(redis=redis_client)
    try:
        yield ctx
    finally:
        await redis_client.close()


async def test_root():
    app.dependency_overrides[application_context] = mock_application_context
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, FastAPI!"}
    app.dependency_overrides.clear()


async def test_ping_redis():
    app.dependency_overrides[application_context] = mock_application_context
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/ping-redis")
    assert response.status_code == 200
    assert response.json() == {"redis_ok": True}
    app.dependency_overrides.clear()


async def test_ping_db():
    app.dependency_overrides[application_context] = mock_application_context
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/ping-db")
    assert response.status_code == 200
    assert response.json() == {"db_ok": True}
    app.dependency_overrides.clear()

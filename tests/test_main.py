import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from src.main import app

# Mark all tests in this file as asyncio tests
pytestmark = pytest.mark.asyncio


@pytest.fixture
def test_app() -> FastAPI:
    """Fixture to provide the FastAPI app instance."""
    # In a real application, you might override dependencies here for testing
    return app


async def test_root(test_app: FastAPI):
    """Test the root endpoint."""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, FastAPI!"}


async def test_ping_redis_mocked(test_app: FastAPI):
    """Test the redis ping endpoint with a mocked context."""
    # This test demonstrates how to mock parts of the context for unit testing
    from redis.asyncio import Redis

    from src.core.context import AppContext
    from src.main import get_context

    class MockRedis(Redis):
        async def ping(self, *args, **kwargs):
            return True  # Simulate a successful ping

    def get_mock_context() -> AppContext:
        return AppContext(redis=MockRedis())

    # Override the dependency for the duration of this test
    test_app.dependency_overrides[get_context] = get_mock_context

    async with AsyncClient(app=test_app, base_url="http://test") as client:
        response = await client.get("/ping-redis")

    assert response.status_code == 200
    assert response.json() == {"redis_ok": True}

    # Clean up the override after the test
    del test_app.dependency_overrides[get_context]

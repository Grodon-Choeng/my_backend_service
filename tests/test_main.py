from contextlib import asynccontextmanager

import pytest
from fakeredis.aioredis import FakeRedis

from src.core.context import AppContext


pytestmark = pytest.mark.asyncio


@asynccontextmanager
async def mock_application_context():
    redis_client = FakeRedis()
    ctx = AppContext(redis=redis_client)
    try:
        yield ctx
    finally:
        await redis_client.close()

import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass

from redis.asyncio import Redis

from src.config import settings
from src.core import databases
from src.core.redis import RedisManager

logger = logging.getLogger(__name__)


@dataclass
class AppContext:
    """
    A data class to hold all application-level shared resources.
    We store the Redis client here, and other resources can be added in the future.
    """

    redis: Redis


@asynccontextmanager
async def application_context():
    """
    The application's core asynchronous context manager.
    Responsible for initializing resources on startup and cleaning them up on shutdown.
    """
    logger.info("Initializing application context...")

    # 1. Initialize RedisManager
    # We instantiate RedisManager here instead of using a global variable in redis.py
    redis_manager = RedisManager(
        redis_url=settings.REDIS.url.unicode_string(), debug=settings.DEBUG
    )

    # 2. Initialize Database
    await databases.init_db()

    # 3. Create the context object
    ctx = AppContext(redis=redis_manager.get_client())

    try:
        # Yielding the context object makes it available to the caller
        yield ctx
    finally:
        # 4. Cleanup resources
        logger.info("Closing application context...")
        await redis_manager.cleanup()
        await databases.close_db()

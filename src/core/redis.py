import logging
from typing import Any, Callable, Optional

from redis.asyncio import ConnectionPool, Redis


def create_redis_with_debug_logger(
    name: str = "redis.debug", *args: Any, **kwargs: Any
) -> Redis:
    logger = logging.getLogger(name)

    def wrapper(func: Callable[..., Any]) -> Callable[..., Any]:
        async def inner(*args: Any, **kwargs: Any) -> Any:
            logger.debug(
                "Calling Redis command: %s args=%s kwargs=%s",
                func.__name__,
                args,
                kwargs,
            )
            result = await func(*args, **kwargs)
            logger.debug("Result of %s: %s", func.__name__, result)
            return result

        return inner

    redis = Redis(*args, **kwargs)
    for command in redis.get_commands():  # type: ignore[attr-defined]
        setattr(redis, command, wrapper(getattr(redis, command)))
    return redis


class RedisManager:
    """
    A manager for Redis clients.

    This class is responsible for creating and managing the Redis connection pool.
    It is designed to be instantiated within an application lifecycle manager (e.g., application_context).
    """

    def __init__(self, redis_url: str, debug: bool = False):
        self._redis_url = redis_url
        self._pool: Optional[ConnectionPool] = None
        self._redis_class: Callable[..., Redis]

        if debug:
            self._redis_class = create_redis_with_debug_logger
        else:
            self._redis_class = Redis

        if not self._redis_url.startswith("fakeredis://"):
            self._pool = ConnectionPool.from_url(
                self._redis_url,
                encoding="utf-8",
                decode_responses=True,
            )

    async def cleanup(self) -> None:
        """Closes the Redis client connection pool."""
        if self._pool:
            await self._pool.disconnect()
        self._pool = None

    def get_client(self) -> Redis:
        """Gets a Redis client instance."""
        if self._redis_url.startswith("fakeredis://"):
            from fakeredis.aioredis import FakeRedis

            return FakeRedis(encoding="utf-8", decode_responses=True)

        if self._pool is None:
            raise RuntimeError("Redis connection pool is not initialized.")

        return self._redis_class(connection_pool=self._pool)


async def ping(client: Redis) -> bool:
    """Tests if the Redis connection is alive (requires a client instance)."""
    try:
        return await client.ping()
    except Exception as e:
        logging.error("Redis ping failed: %s", e)
        return False

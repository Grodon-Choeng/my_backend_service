import sys
import logging
from functools import wraps
from typing import Optional

from redis.asyncio import ConnectionPool, Redis


class RedisWithDebugLogger:
    def __init__(self, name: str = "redis.debug", *args, **kwargs):
        self._redis = Redis(*args, **kwargs)
        self._logger = logging.getLogger(name)

    @property
    def logger(self):
        return self._logger

    def __getattr__(self, name):
        attr = getattr(self._redis, name)

        if callable(attr):

            @wraps(attr)
            async def async_wrapper(*args, **kwargs):
                self.logger.debug(
                    "Calling Redis command: %s args=%s kwargs=%s", name, args, kwargs
                )
                result = await attr(*args, **kwargs)
                self.logger.debug("Result of %s: %s", name, result)
                return result

            return async_wrapper
        return attr

    @classmethod
    def setup_logger(
        cls, name: str = "redis.debug", fmt: str = "%(levelname)s:%(name)s:%(message)s"
    ):
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(fmt)
            handler.setFormatter(formatter)
            logger.addHandler(handler)


class RedisManager:
    """Redis 客户端管理器"""

    def __init__(self, redis_url: str, debug: bool = False):
        self.redis_class = None
        self._redis_url = redis_url
        self._pool: Optional[ConnectionPool] = None
        if not self._redis_url.startswith("fakeredis://"):
            self._pool = ConnectionPool.from_url(
                self._redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
        self.set_debug(debug)

    def set_debug(self, debug: bool, fmt: str = "%(levelname)s:%(name)s:%(message)s"):
        """设置是否开启调试日志"""
        if debug:
            self.redis_class = RedisWithDebugLogger
            RedisWithDebugLogger.setup_logger(fmt=fmt)
        else:
            self.redis_class = Redis

    async def cleanup(self) -> None:
        """关闭 Redis 客户端连接"""
        if self._pool:
            await self._pool.disconnect()
        self._pool = None

    def get_client(self) -> Redis:
        """获取 Redis 客户端实例"""
        if self._redis_url.startswith("fakeredis://"):
            from fakeredis.aioredis import FakeRedis

            return FakeRedis(encoding="utf-8", decode_responses=True)

        if self._pool is None:
            raise RuntimeError("Redis 连接池未初始化")

        return self.redis_class(connection_pool=self._pool)


# 模块级共享实例由外部传入 redis_url 创建
shared_redis_manager: Optional[RedisManager] = None


def init(redis_url: str):
    """初始化 Redis 客户端连接池"""
    global shared_redis_manager
    shared_redis_manager = RedisManager(redis_url)


def get_redis() -> Redis:
    """通用依赖注入：获取 Redis 客户端实例"""
    if shared_redis_manager is None:
        raise RuntimeError("RedisManager 尚未初始化，请先调用 init(redis_url)")
    return shared_redis_manager.get_client()


async def close() -> None:
    """关闭 Redis 客户端连接"""
    if shared_redis_manager is not None:
        await shared_redis_manager.cleanup()

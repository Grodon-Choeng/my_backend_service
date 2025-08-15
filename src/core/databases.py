import logging

from tortoise import Tortoise, exceptions

from src.config import TORTOISE_ORM, settings

logger = logging.getLogger(__name__)


async def init_db():
    """
    Initializes Tortoise-ORM and connects to the database.
    """
    logger.info("Initializing database connection...")
    await Tortoise.init(config=TORTOISE_ORM)
    if settings.DEBUG:
        logger.info("Generating database schemas...")
        await Tortoise.generate_schemas()
    logger.info("Database connection initialized successfully.")


async def close_db():
    """
    Closes all database connections managed by Tortoise-ORM.
    """
    logger.info("Closing database connections...")
    await Tortoise.close_connections()
    logger.info("Database connections closed.")


async def check_db_connection() -> bool:
    """
    Performs a simple query to verify that the database connection is active.
    """
    try:
        await Tortoise.get_connection("default").execute_query("SELECT 1")
        logger.debug("Database connection check successful.")
        return True
    except (exceptions.DBConnectionError, OSError) as e:
        logger.error("Database connection check failed: %s", e)
        return False

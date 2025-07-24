import logging

from tortoise import Tortoise

from src.config import settings

logger = logging.getLogger(__name__)


async def init_db():
    """
    Initializes Tortoise-ORM, connects to the database, and generates schemas.
    """
    logger.info("Initializing database connection...")
    db_url = settings.DATABASE_URL.unicode_string()
    await Tortoise.init(
        db_url=db_url,
        modules={"models": settings.DATABASE_MODELS},
    )
    # Generate schemas if in debug mode. For production, use Aerich migrations.
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

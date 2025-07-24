"""
Application configuration module.

This module defines the configuration settings for the FastAPI backend application.
It includes settings for databases, security, CORS, and other application-level configurations.
The configuration values can be loaded from environment variables, .env files, or use default values.
"""

from pydantic_settings import BaseSettings as PydanticBaseSettings
from pydantic import Field, computed_field, MySQLDsn, RedisDsn


from src.core.config import BaseSettings, refer_to_field


class RedisSettings(PydanticBaseSettings):
    """Configuration for Redis connection."""

    HOST: str = "localhost"
    PORT: int = 6379
    PASSWORD: str | None = None
    DATABASE: int = 0

    @computed_field
    @property
    def url(self) -> RedisDsn:
        """
        Generate Redis connection URL automatically.

        Returns:
            RedisDsn: The Redis connection URL.
        """
        password = f":{self.PASSWORD}@" if self.PASSWORD else ""
        return RedisDsn(f"redis://{password}{self.HOST}:{self.PORT}/{self.DATABASE}")


class MysqlSettings(PydanticBaseSettings):
    """Configuration for MySQL database connection."""

    HOST: str = "localhost"
    PORT: int = 3306
    USERNAME: str = "root"
    PASSWORD: str | None = None
    DATABASE: str = "app"

    @computed_field
    @property
    def url(self) -> MySQLDsn:
        """
        Generate MySQL connection URL automatically.

        Returns:
            MySQLDsn: The MySQL connection URL.
        """
        password = f":{self.PASSWORD}" if self.PASSWORD else ""
        auth = f"{self.USERNAME}{password}@" if self.USERNAME else ""
        return MySQLDsn(f"mysql://{auth}{self.HOST}:{self.PORT}/{self.DATABASE}")


class Settings(BaseSettings):
    """
    Main configuration class that manages all application settings.

    This class consolidates all application configuration into a single place,
    making it easy to manage and access settings throughout the application.
    """

    # ⚙️ Application core configuration
    PROJECT_NAME: str = "FastAPI Backend"
    DEBUG: bool = Field(default=False, description="Enable or disable debug mode")
    ENVIRONMENT: str = Field(
        default="production",
        description="Runtime environment (development, staging, production)",
    )
    API_V1_STR: str = "/api/v1"

    # 🔒 Security and authentication configuration
    SECRET_KEY: str = Field(
        description="Secret key used for JWT signing and other operations, must be set!"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # 📦 Database configuration (Tortoise-ORM)
    DATABASE_URL: MySQLDsn = Field(description="Main database connection URL")
    DATABASE_MODELS: list[str] = ["src.models", "aerich.models"]

    # 🔗 Test database configuration (using refer_to_field to automatically reference main database configuration)
    TEST_DATABASE_URL: MySQLDsn | None = refer_to_field(refer_to="DATABASE_URL")

    # 🔗 Redis configuration (using nested model)
    REDIS: RedisSettings = RedisSettings()

    # 🔗 MySQL configuration (using nested model)
    MYSQL: MysqlSettings = MysqlSettings()

    # 🌐 CORS configuration
    BACKEND_CORS_ORIGINS: list[str] = [
        "*"
    ]  # In production, this should be configured with specific frontend domains


# 🚀 Export a globally available configuration instance
settings = Settings()

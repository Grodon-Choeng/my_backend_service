"""
Application configuration module.

This module defines the configuration settings for the FastAPI backend application.
It includes settings for databases, security, CORS, and other application-level configurations.
The configuration values can be loaded from environment variables, .env files, or use default values.
"""

import os

from dotenv import load_dotenv
from pydantic import Field, MySQLDsn, RedisDsn, model_validator
from pydantic_settings import BaseSettings as PydanticBaseSettings

from src.core.config import BaseSettings, refer_to_field

load_dotenv()


class RedisSettings(PydanticBaseSettings):
    """Configuration for Redis connection."""

    HOST: str = "localhost"
    PORT: int = 6379
    PASSWORD: str | None = None
    DATABASE: int = 0

    url: RedisDsn | None = None

    @model_validator(mode="after")
    def set_url(self) -> "RedisSettings":
        if not self.url:
            password = f":{self.PASSWORD}@" if self.PASSWORD else ""
            self.url = RedisDsn(
                f"redis://{password}{self.HOST}:{self.PORT}/{self.DATABASE}"
            )
        return self


class MysqlSettings(PydanticBaseSettings):
    """Configuration for MySQL database connection."""

    HOST: str = "localhost"
    PORT: int = 3306
    USERNAME: str = "root"
    PASSWORD: str | None = None
    DATABASE: str = "app"

    url: MySQLDsn | None = None

    @model_validator(mode="after")
    def set_url(self) -> "MysqlSettings":
        if not self.url:
            password = f":{self.PASSWORD}" if self.PASSWORD else ""
            auth = f"{self.USERNAME}{password}@" if self.USERNAME else ""
            self.url = MySQLDsn(
                f"mysql://{auth}{self.HOST}:{self.PORT}/{self.DATABASE}"
            )
        return self


class Settings(BaseSettings):
    """
    Main configuration class that manages all application settings.
    """

    PROJECT_NAME: str = "FastAPI Backend"
    DEBUG: bool = Field(default=False, description="Enable or disable debug mode")
    ENVIRONMENT: str = Field(
        default="production",
        description="Runtime environment (development, staging, production)",
    )
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = Field(
        description="Secret key used for JWT signing and other operations, must be set!"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    DATABASE_MODELS: list[str] = ["src.core.model"]
    TEST_DATABASE_URL: MySQLDsn | None = refer_to_field(refer_to="MYSQL.url")
    REDIS: RedisSettings = RedisSettings()
    MYSQL: MysqlSettings = MysqlSettings()
    BACKEND_CORS_ORIGINS: list[str] | str = ["*"]

    @model_validator(mode="after")
    def set_dynamic_fields(self) -> "Settings":
        if self.ENVIRONMENT == "development":
            self.DEBUG = True
        if isinstance(self.BACKEND_CORS_ORIGINS, str):
            self.BACKEND_CORS_ORIGINS = [
                origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",")
            ]
        if self.ENVIRONMENT == "production" and self.BACKEND_CORS_ORIGINS == ["*"]:
            self.BACKEND_CORS_ORIGINS = []
        return self


settings = Settings()

# A static dictionary for Aerich, reading directly from environment variables.
# This avoids Pydantic's loading timing issues with Aerich.
DB_URL = "mysql://{user}:{password}@{host}:{port}/{db_name}".format(
    user=os.getenv("MYSQL_USERNAME", "root"),
    password=os.getenv("MYSQL_PASSWORD", "password"),
    host=os.getenv("MYSQL_HOST", "127.0.0.1"),
    port=os.getenv("MYSQL_PORT", 3306),
    db_name=os.getenv("MYSQL_DATABASE", "app"),
)

TORTOISE_ORM = {
    "connections": {"default": DB_URL},
    "apps": {
        "models": {
            "models": ["src.core.model", "aerich.models"],
            "default_connection": "default",
        },
    },
}

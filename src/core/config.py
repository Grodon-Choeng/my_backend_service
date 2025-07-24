"""
Base configuration classes for the application.

This module provides enhanced configuration management capabilities built on top of
Pydantic Settings. It supports loading configuration from multiple sources with
customizable priority orders, including environment variables, .env files, and
file secrets. It also includes features for linking fields and cascading configuration files.
"""

import os
from typing import Any, TypeVar

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings as PydanticBaseSettings
from pydantic_settings import (
    DotEnvSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

T = TypeVar("T", bound="BaseSettings")


def refer_to_field(*, refer_to: str, default: Any = None, **kwargs):
    """
    Create a field that can be referred to another field's value.

    Args:
        refer_to: The name of the field to refer from.
        default: Default value if no link is available.
        **kwargs: Additional field arguments.

    Returns:
        A Pydantic Field with metadata indicating its link.
    """
    metadata = kwargs.pop("json_schema_extra", {})
    metadata["refer_to"] = refer_to
    return Field(default=default, json_schema_extra=metadata, **kwargs)


class BaseSettings(PydanticBaseSettings):
    """
    Base configuration class that supports loading from environment variables and .env files.

    Features:
        - Load config from .env and OS environment
        - Auto-fill fields based on other fields using [refer_to_field]
        - Support for multiple, cascading configuration files via `CONFIG_FILES` env var.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[PydanticBaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """
        Customize sources for reading settings values.

        Priority order:
            1. Init values (highest priority)
            2. Environment variables
            3. Configuration files (specified in CONFIG_FILES, last file has the highest priority)
            4. Default .env file
            5. File secrets (lowest priority)

        Args:
            settings_cls: The settings class being instantiated.
            init_settings: Settings source for init values.
            env_settings: Settings source for environment variables.
            dotenv_settings: Settings source for .env files.
            file_secret_settings: Settings source for file secrets.

        Returns:
            Tuple of settings sources in priority order.
        """
        config_files_str = os.getenv("CONFIG_FILES")

        custom_dotenv_sources = []
        if config_files_str:
            config_files = [path.strip() for path in config_files_str.split(",")]
            # Create a source for each specified config file, reversing the list
            # so that later files have higher priority (as they appear earlier in the tuple).
            custom_dotenv_sources = [
                DotEnvSettingsSource(settings_cls, env_file=path)
                for path in reversed(config_files)
            ]

        return (
            init_settings,
            env_settings,
            *custom_dotenv_sources,
            dotenv_settings,  # This is the default .env source
            file_secret_settings,
        )

    @model_validator(mode="after")
    def _fill_linked_fields(self: T) -> T:
        """
        Fill in missing field values by linking them to other fields.

        This validator checks each field's metadata for a 'refer_to' reference.
        If the current field is empty, it will take the value from the linked field.

        Args:
            self: The settings instance being validated.

        Returns:
            The validated settings instance.
        """
        for field_name, model_field in self.__class__.model_fields.items():
            refer_key = (model_field.json_schema_extra or {}).get("refer_to")
            if refer_key:
                current_value = getattr(self, field_name)
                referred_value = getattr(self, refer_key, None)
                if current_value is None and referred_value is not None:
                    setattr(self, field_name, referred_value)
        return self

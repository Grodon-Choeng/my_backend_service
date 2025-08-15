"""
Core Database Models

This module provides base model classes and mixins for database operations
including timezone-aware datetime handling, timestamp tracking, and soft deletion.
"""

from datetime import datetime, timezone
from typing import Any, Type

from tortoise import fields, models
from tortoise.manager import Manager
from tortoise.queryset import QuerySet


class UTCDateTimeField(fields.DatetimeField):
    """
    A timezone-aware datetime field that ensures all datetime values
    are stored in UTC timezone for consistency across the application.
    """

    def to_db_value(
        self, value: datetime, instance: Type[models.Model] | models.Model
    ) -> datetime:
        """
        Convert datetime to UTC before storing in database.

        Args:
            value (datetime): The datetime value to convert
            instance: The model instance

        Returns:
            datetime: UTC-normalized datetime value
        """
        dt = super().to_db_value(value, instance)
        if dt:
            if not dt.tzinfo:
                dt = dt.astimezone()
            dt = dt.astimezone(timezone.utc)
        return dt

    def to_python_value(self, value: Any) -> datetime:
        """
        Convert database value to Python datetime with UTC timezone.

        Args:
            value: The raw database value

        Returns:
            datetime: Python datetime object with UTC timezone
        """
        if isinstance(value, datetime) and value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        dt = super().to_python_value(value)
        return dt


class TimestampMixin(models.Model):
    """
    Timestamp mixin providing automatic created_at and updated_at fields.

    This mixin automatically tracks when records are created and last updated,
    using timezone-aware UTC datetime values.
    """

    created_at: datetime = UTCDateTimeField(auto_now_add=True)
    updated_at: datetime = UTCDateTimeField(auto_now=True)


class SoftDeleteQuerySet(QuerySet):
    """
    Custom QuerySet that by default only queries non-soft-deleted records.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._filters.update({"is_deleted": False})


class SoftDeleteMixin(models.Model):
    """
    Soft delete mixin providing logical deletion capability.

    Models inheriting this mixin will gain the following features:
    1. The `objects` manager returns only non-deleted records by default.
    2. The `all_objects` manager can query all records, including deleted ones.
    3. `soft_delete()` and `restore()` methods for performing the operations.
    """

    is_deleted = fields.BooleanField(default=False, index=True)
    deleted_at = UTCDateTimeField(null=True, blank=True)

    objects = Manager(SoftDeleteQuerySet)
    all_objects = Manager()

    async def soft_delete(self):
        """Marks the instance as deleted."""
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)
        await self.save(update_fields=["is_deleted", "deleted_at", "updated_at"])

    async def restore(self):
        """Restores a soft-deleted instance."""
        self.is_deleted = False
        self.deleted_at = None
        await self.save(update_fields=["is_deleted", "deleted_at", "updated_at"])

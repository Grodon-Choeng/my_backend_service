"""
Core Database Models

This module provides base model classes and mixins for database operations
including timezone-aware datetime handling, timestamp tracking, and soft deletion.
"""

from typing import Type, Any
from datetime import datetime, timezone

from tortoise import fields, models


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
            # If datetime is naive (no timezone info), assume it's local time
            if not dt.tzinfo:
                dt = dt.astimezone()
            # Convert to UTC for consistent storage
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
        # If we get a datetime without timezone, assume its UTC
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

    #: When the record was created (autopopulated on creation)
    created_at: datetime = UTCDateTimeField(auto_now_add=True)

    #: When the record was last updated (autopopulated on every update)
    updated_at: datetime = UTCDateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteMixin(models.Model):
    """
    Soft delete mixin providing logical deletion capability.

    Instead of physically removing records from the database, this mixin
    marks them as deleted with a flag and records when the deletion occurred.
    """

    #: Whether the record has been logically deleted
    is_deleted = fields.BooleanField(default=False)

    #: When the record was logically deleted (null if not deleted)
    deleted_at = UTCDateTimeField(null=True)

    class Meta:
        abstract = True

    async def soft_delete(self, using_db: bool = None) -> None:
        """
        Async version of delete method to perform soft delete.

        Args:
            using_db: Database connection to use

        Returns:
            Instance of the model
        """
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)
        return await self.save(using_db=using_db)

    async def restore(self) -> None:
        """
        Restore a soft deleted record.
        """
        self.is_deleted = False
        self.deleted_at = None
        return await self.save()

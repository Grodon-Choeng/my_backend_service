import pytest
from tortoise import Tortoise, fields
from tortoise.models import Model

from src.core.model import SoftDeleteMixin, TimestampMixin


class TestModel(TimestampMixin, SoftDeleteMixin, Model):
    """A model for testing our mixins."""

    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255)

    class Meta:
        table = "test_model"


@pytest.fixture(scope="function", autouse=True)
async def initialize_db():
    """Initializes an in-memory SQLite database for each test function."""
    await Tortoise.init(
        db_url="sqlite://:memory:",
        modules={"models": [__name__]},  # Use the current module to find TestModel
    )
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()


@pytest.mark.asyncio
async def test_soft_delete_mixin():
    """Tests the functionality of the SoftDeleteMixin."""
    # 1. Create a new record
    record = await TestModel.create(name="test_record")
    assert not record.is_deleted
    assert record.deleted_at is None

    # 2. Soft delete the record
    await record.soft_delete()
    assert record.is_deleted
    assert record.deleted_at is not None

    # 3. Verify it's not in the default manager
    found_record = await TestModel.objects.filter(id=record.id).first()
    assert found_record is None

    # 4. Verify it IS in the `all_objects` manager
    found_all_record = await TestModel.all_objects.filter(id=record.id).first()
    assert found_all_record is not None
    assert found_all_record.is_deleted

    # 5. Restore the record
    await found_all_record.restore()
    assert not found_all_record.is_deleted
    assert found_all_record.deleted_at is None

    # 6. Verify it's back in the default manager
    restored_record = await TestModel.objects.filter(id=record.id).first()
    assert restored_record is not None
    assert not restored_record.is_deleted


@pytest.mark.asyncio
async def test_soft_delete_queryset():
    """Tests that the custom queryset correctly filters deleted records."""
    await TestModel.create(name="active_1")
    deleted_record = await TestModel.create(name="deleted_1")
    await deleted_record.soft_delete()

    # Default manager should only see 1 record
    active_count = await TestModel.objects.all().count()
    assert active_count == 1

    # `all_objects` manager should see both records
    total_count = await TestModel.all_objects.all().count()
    assert total_count == 2

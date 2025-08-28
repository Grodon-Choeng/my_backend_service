import pytest
from tortoise import fields, Tortoise

from src.core.model import SoftDeleteMixin, TimestampMixin


class MixinTestModel(TimestampMixin, SoftDeleteMixin):
    """A model for testing our mixins."""

    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=255)

    class Meta:
        table = "test_model"
        default_connection = "default"


@pytest.fixture(scope="function")
async def initialize_db():
    """Initializes an in-memory SQLite database for each test function."""
    await Tortoise.init(
        config={
            "connections": {
                "default": {
                    "engine": "tortoise.backends.sqlite",
                    "credentials": {"file_path": ":memory:"},
                }
            },
            "apps": {
                "models": {
                    "models": ["tests.core.test_model"],
                    "default_connection": "default",
                }
            },
        }
    )
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()


@pytest.mark.asyncio
async def test_soft_delete_mixin(initialize_db):
    """Tests the functionality of the SoftDeleteMixin."""
    # 1. Create a new record
    record = await MixinTestModel.create(name="test_record")
    assert not record.is_deleted
    assert record.deleted_at is None

    # 2. Soft delete the record
    await record.soft_delete()
    assert record.is_deleted
    assert record.deleted_at is not None

    # 3. Verify it's not in the default manager
    found_record = await MixinTestModel.objects.filter(id=record.id).first()
    assert found_record is None

    # 4. Verify it IS in the `all_objects` manager
    found_all_record = await MixinTestModel.all_objects.filter(id=record.id).first()
    assert found_all_record is not None
    assert found_all_record.is_deleted

    # 5. Restore the record
    await found_all_record.restore()
    assert not found_all_record.is_deleted
    assert found_all_record.deleted_at is None

    # 6. Verify it's back in the default manager
    restored_record = await MixinTestModel.objects.filter(id=record.id).first()
    assert restored_record is not None
    assert not restored_record.is_deleted


@pytest.mark.asyncio
async def test_soft_delete_queryset(initialize_db):
    """Tests that the custom queryset correctly filters deleted records."""
    await MixinTestModel.create(name="active_1")
    deleted_record = await MixinTestModel.create(name="deleted_1")
    await deleted_record.soft_delete()

    # Default manager should only see 1 record
    active_count = await MixinTestModel.objects.all().count()
    assert active_count == 1

    # `all_objects` manager should see both records
    total_count = await MixinTestModel.all_objects.all().count()
    assert total_count == 2

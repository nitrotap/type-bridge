"""Integration tests for schema generation with all attribute types."""

import pytest

from type_bridge import (
    Boolean,
    Date,
    DateTime,
    DateTimeTZ,
    Decimal,
    Double,
    Duration,
    Entity,
    EntityFlags,
    Flag,
    Integer,
    Key,
    SchemaManager,
    String,
)


@pytest.mark.integration
@pytest.mark.order(8)
def test_schema_with_all_attribute_types(clean_db):
    """Test schema generation for all 9 attribute types."""

    # Define all attribute types
    class Name(String):
        pass

    class Age(Integer):
        pass

    class IsActive(Boolean):
        pass

    class Score(Double):
        pass

    class BirthDate(Date):
        pass

    class CreatedAt(DateTime):
        pass

    class UpdatedAt(DateTimeTZ):
        pass

    class Balance(Decimal):
        pass

    class SessionDuration(Duration):
        pass

    # Create entity with all types
    class CompleteRecord(Entity):
        flags = EntityFlags(type_name="complete_record")
        name: Name = Flag(Key)
        age: Age | None
        is_active: IsActive | None
        score: Score | None
        birth_date: BirthDate | None
        created_at: CreatedAt | None
        updated_at: UpdatedAt | None
        balance: Balance | None
        session_duration: SessionDuration | None

    # Create and sync schema
    schema_manager = SchemaManager(clean_db)
    schema_manager.register(CompleteRecord)
    schema_manager.sync_schema(force=True)

    # Verify schema was created
    schema_info = schema_manager.collect_schema_info()

    # Verify entity exists
    assert "complete_record" in schema_info.entities
    record_info = schema_info.entities["complete_record"]

    # Verify all attribute types are registered
    assert "Name" in schema_info.attributes
    assert "Age" in schema_info.attributes
    assert "IsActive" in schema_info.attributes
    assert "Score" in schema_info.attributes
    assert "BirthDate" in schema_info.attributes
    assert "CreatedAt" in schema_info.attributes
    assert "UpdatedAt" in schema_info.attributes
    assert "Balance" in schema_info.attributes
    assert "SessionDuration" in schema_info.attributes

    # Verify entity owns all attributes
    assert "Name" in record_info.owns
    assert "Age" in record_info.owns
    assert "IsActive" in record_info.owns
    assert "Score" in record_info.owns
    assert "BirthDate" in record_info.owns
    assert "CreatedAt" in record_info.owns
    assert "UpdatedAt" in record_info.owns
    assert "Balance" in record_info.owns
    assert "SessionDuration" in record_info.owns

    # Verify Name is key
    assert record_info.owns["Name"].is_key is True

    # Verify optional attributes have correct cardinality (0..1)
    assert record_info.owns["Age"].card == (0, 1)
    assert record_info.owns["IsActive"].card == (0, 1)
    assert record_info.owns["Score"].card == (0, 1)

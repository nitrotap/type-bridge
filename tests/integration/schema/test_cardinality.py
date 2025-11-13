"""Integration tests for schema cardinality constraints."""

import pytest

from type_bridge import Card, Entity, EntityFlags, Flag, Integer, Key, SchemaManager, String


@pytest.mark.integration
@pytest.mark.order(4)
def test_schema_with_cardinality(clean_db):
    """Test schema creation with various cardinality constraints."""

    class Tag(String):
        pass

    class Score(Integer):
        pass

    class Email(String):
        pass

    class Person(Entity):
        flags = EntityFlags(type_name="person")
        email: Email = Flag(Key)
        tags: list[Tag] = Flag(Card(min=1))  # At least 1 tag
        scores: list[Score] = Flag(Card(max=5))  # At most 5 scores

    # Create and sync schema
    schema_manager = SchemaManager(clean_db)
    schema_manager.register(Person)
    schema_manager.sync_schema(force=True)

    # Verify schema
    schema_info = schema_manager.collect_schema_info()
    person_info = schema_info.entities["person"]

    # Check attribute ownership
    assert "Email" in person_info.owns
    assert "Tag" in person_info.owns
    assert "Score" in person_info.owns

    # Check cardinality flags
    assert person_info.owns["Tag"].is_key is False
    assert person_info.owns["Tag"].card == (1, None)  # min=1, no max

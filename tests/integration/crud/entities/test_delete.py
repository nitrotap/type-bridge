"""Integration tests for entity delete operations."""

import pytest

from type_bridge import Entity, EntityFlags, Flag, Integer, Key, String


@pytest.mark.integration
@pytest.mark.order(19)
def test_delete_entity(db_with_schema):
    """Test deleting entities."""

    class Name(String):
        pass

    class Age(Integer):
        pass

    class Person(Entity):
        flags = EntityFlags(type_name="person")
        name: Name = Flag(Key)
        age: Age | None

    manager = Person.manager(db_with_schema)

    # Insert entity
    jack = Person(name=Name("Jack"), age=Age(30))
    manager.insert(jack)

    # Verify insertion
    results = manager.get(name="Jack")
    assert len(results) == 1

    # Delete
    deleted_count = manager.delete(name="Jack")
    assert deleted_count == 1

    # Verify deletion
    results_after = manager.get(name="Jack")
    assert len(results_after) == 0

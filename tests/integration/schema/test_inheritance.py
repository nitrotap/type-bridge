"""Integration tests for schema inheritance."""

import pytest

from type_bridge import Entity, EntityFlags, Flag, Key, SchemaManager, String


@pytest.mark.integration
@pytest.mark.order(6)
def test_schema_inheritance(clean_db):
    """Test schema creation with entity inheritance."""

    class Name(String):
        pass

    class Animal(Entity):
        flags = EntityFlags(type_name="animal", abstract=True)
        name: Name = Flag(Key)

    class Species(String):
        pass

    class Dog(Animal):
        flags = EntityFlags(type_name="dog")
        species: Species

    # Create and sync schema
    schema_manager = SchemaManager(clean_db)
    schema_manager.register(Animal, Dog)
    schema_manager.sync_schema(force=True)

    # Verify schema
    schema_info = schema_manager.collect_schema_info()

    assert "animal" in schema_info.entities
    assert "dog" in schema_info.entities

    # Verify dog inherits from animal
    dog_info = schema_info.entities["dog"]
    # Dog should own both Name (inherited) and Species
    assert "Name" in dog_info.owns
    assert "Species" in dog_info.owns

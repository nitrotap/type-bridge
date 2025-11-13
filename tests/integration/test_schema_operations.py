"""Integration tests for schema operations with real TypeDB."""

import pytest

from type_bridge import (
    Card,
    Entity,
    EntityFlags,
    Flag,
    Integer,
    Key,
    Relation,
    RelationFlags,
    Role,
    SchemaManager,
    String,
    Unique,
)
from type_bridge.schema import SchemaConflictError


@pytest.mark.integration
@pytest.mark.order(1)
def test_schema_creation_and_sync(clean_db):
    """Test creating and syncing a schema to TypeDB."""
    # Define schema
    class Name(String):
        pass

    class Age(Integer):
        pass

    class Person(Entity):
        flags = EntityFlags(type_name="person")
        name: Name = Flag(Key)
        age: Age | None

    # Create schema manager
    schema_manager = SchemaManager(clean_db)
    schema_manager.register(Person)

    # Sync schema
    schema_manager.sync_schema(force=True)

    # Verify schema was created by collecting it back
    schema_info = schema_manager.collect_schema_info()

    assert "person" in schema_info.entities
    assert "Name" in schema_info.attributes
    assert "Age" in schema_info.attributes


@pytest.mark.integration
@pytest.mark.order(2)
def test_schema_with_relations(clean_db):
    """Test creating schema with entities and relations."""

    class Name(String):
        pass

    class Person(Entity):
        flags = EntityFlags(type_name="person")
        name: Name = Flag(Key)

    class Company(Entity):
        flags = EntityFlags(type_name="company")
        name: Name = Flag(Key)

    class Position(String):
        pass

    class Employment(Relation):
        flags = RelationFlags(type_name="employment")
        employee: Role[Person] = Role("employee", Person)
        employer: Role[Company] = Role("employer", Company)
        position: Position

    # Create and sync schema
    schema_manager = SchemaManager(clean_db)
    schema_manager.register(Person, Company, Employment)
    schema_manager.sync_schema(force=True)

    # Verify schema
    schema_info = schema_manager.collect_schema_info()

    assert "person" in schema_info.entities
    assert "company" in schema_info.entities
    assert "employment" in schema_info.relations

    # Verify relation roles
    employment_info = schema_info.relations["employment"]
    assert "employee" in employment_info.roles
    assert "employer" in employment_info.roles


@pytest.mark.integration
@pytest.mark.order(3)
def test_schema_conflict_detection(clean_db):
    """Test that schema conflict detection prevents data loss."""

    class Name(String):
        pass

    class Age(Integer):
        pass

    class Person(Entity):
        flags = EntityFlags(type_name="person")
        name: Name = Flag(Key)
        age: Age

    # Create initial schema
    schema_manager = SchemaManager(clean_db)
    schema_manager.register(Person)
    schema_manager.sync_schema(force=True)

    # Modify schema - remove age attribute
    class PersonModified(Entity):
        flags = EntityFlags(type_name="person")
        name: Name = Flag(Key)
        # age attribute removed!

    # Try to sync modified schema - should detect conflict
    schema_manager2 = SchemaManager(clean_db)
    schema_manager2.register(PersonModified)

    with pytest.raises(SchemaConflictError) as exc_info:
        schema_manager2.sync_schema()

    # Verify error message mentions removed attribute
    error_msg = str(exc_info.value)
    assert "Age" in error_msg or "age" in error_msg.lower()


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


@pytest.mark.integration
@pytest.mark.order(5)
def test_schema_with_unique_attributes(clean_db):
    """Test schema creation with unique attributes."""

    class Email(String):
        pass

    class Username(String):
        pass

    class User(Entity):
        flags = EntityFlags(type_name="user")
        email: Email = Flag(Key)
        username: Username = Flag(Unique)

    # Create and sync schema
    schema_manager = SchemaManager(clean_db)
    schema_manager.register(User)
    schema_manager.sync_schema(force=True)

    # Verify schema
    schema_info = schema_manager.collect_schema_info()
    user_info = schema_info.entities["user"]

    # Check key and unique flags
    assert user_info.owns["Email"].is_key is True
    assert user_info.owns["Username"].is_unique is True


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


@pytest.mark.integration
@pytest.mark.order(7)
def test_schema_update_safe_changes(clean_db):
    """Test that safe schema changes (adding attributes) work."""

    class Name(String):
        pass

    class Person(Entity):
        flags = EntityFlags(type_name="person")
        name: Name = Flag(Key)

    # Create initial schema
    schema_manager = SchemaManager(clean_db)
    schema_manager.register(Person)
    schema_manager.sync_schema(force=True)

    # Add a new optional attribute (safe change)
    class Age(Integer):
        pass

    class PersonWithAge(Entity):
        flags = EntityFlags(type_name="person")
        name: Name = Flag(Key)
        age: Age | None  # New optional attribute

    # Sync updated schema with force=True
    schema_manager2 = SchemaManager(clean_db)
    schema_manager2.register(PersonWithAge)
    schema_manager2.sync_schema(force=True)

    # Verify new attribute was added
    schema_info = schema_manager2.collect_schema_info()
    person_info = schema_info.entities["person"]

    assert "Name" in person_info.owns
    assert "Age" in person_info.owns

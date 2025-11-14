"""Integration tests for schema creation with relations."""

import pytest

from type_bridge import (
    Entity,
    EntityFlags,
    Flag,
    Key,
    Relation,
    RelationFlags,
    Role,
    SchemaManager,
    String,
)


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

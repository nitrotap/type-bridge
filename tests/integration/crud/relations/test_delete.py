"""Integration tests for relation deletion operations.

Tests cover the RelationManager.delete() method with filter-based deletion
supporting both attribute and role player filters.
"""

import pytest

from type_bridge import (
    Entity,
    Flag,
    Integer,
    Key,
    Relation,
    Role,
    SchemaManager,
    String,
    TypeFlags,
)


@pytest.mark.integration
@pytest.mark.order(140)
def test_relation_manager_has_delete_method(db_with_schema):
    """Test that RelationManager has a delete() method."""

    # Arrange
    class Name(String):
        pass

    class Position(String):
        pass

    class Person(Entity):
        flags = TypeFlags(name="person")
        name: Name = Flag(Key)

    class Company(Entity):
        flags = TypeFlags(name="company")
        name: Name = Flag(Key)

    class Employment(Relation):
        flags = TypeFlags(name="employment")
        employee: Role[Person] = Role("employee", Person)
        employer: Role[Company] = Role("employer", Company)
        position: Position

    schema_manager = SchemaManager(db_with_schema)
    schema_manager.register(Person, Company, Employment)
    schema_manager.sync_schema(force=True)

    manager = Employment.manager(db_with_schema)

    # Act & Assert - RelationManager should have delete() method
    expected = True
    actual = hasattr(manager, "delete")
    assert expected == actual


@pytest.mark.integration
@pytest.mark.order(141)
def test_delete_relation_by_role_players(db_with_schema):
    """Test deleting specific relation by role players."""

    # Arrange
    class Name(String):
        pass

    class Position(String):
        pass

    class Person(Entity):
        flags = TypeFlags(name="person")
        name: Name = Flag(Key)

    class Company(Entity):
        flags = TypeFlags(name="company")
        name: Name = Flag(Key)

    class Employment(Relation):
        flags = TypeFlags(name="employment")
        employee: Role[Person] = Role("employee", Person)
        employer: Role[Company] = Role("employer", Company)
        position: Position

    schema_manager = SchemaManager(db_with_schema)
    schema_manager.register(Person, Company, Employment)
    schema_manager.sync_schema(force=True)

    # Setup data
    person_mgr = Person.manager(db_with_schema)
    company_mgr = Company.manager(db_with_schema)
    employment_mgr = Employment.manager(db_with_schema)

    alice = Person(name=Name("Alice"))
    techcorp = Company(name=Name("TechCorp"))
    person_mgr.insert(alice)
    company_mgr.insert(techcorp)

    emp = Employment(employee=alice, employer=techcorp, position=Position("Engineer"))
    employment_mgr.insert(emp)

    # Verify insertion
    relations_before = employment_mgr.all()
    expected = 1
    actual = len(relations_before)
    assert expected == actual

    # Act - Delete relation using manager.delete() with role player filters
    count = employment_mgr.delete(employee=alice, employer=techcorp)

    # Assert - Verify deletion count
    expected_count = 1
    assert expected_count == count

    # Assert - Relation should be deleted
    relations_after = employment_mgr.all()
    expected = 0
    actual = len(relations_after)
    assert expected == actual


@pytest.mark.integration
@pytest.mark.order(142)
def test_delete_relation_by_attribute_filter(db_with_schema):
    """Test deleting relations filtered by attribute value."""

    # Arrange
    class Name(String):
        pass

    class Position(String):
        pass

    class Person(Entity):
        flags = TypeFlags(name="person")
        name: Name = Flag(Key)

    class Company(Entity):
        flags = TypeFlags(name="company")
        name: Name = Flag(Key)

    class Employment(Relation):
        flags = TypeFlags(name="employment")
        employee: Role[Person] = Role("employee", Person)
        employer: Role[Company] = Role("employer", Company)
        position: Position

    schema_manager = SchemaManager(db_with_schema)
    schema_manager.register(Person, Company, Employment)
    schema_manager.sync_schema(force=True)

    # Setup multiple employments
    person_mgr = Person.manager(db_with_schema)
    company_mgr = Company.manager(db_with_schema)
    employment_mgr = Employment.manager(db_with_schema)

    bob = Person(name=Name("Bob"))
    charlie = Person(name=Name("Charlie"))
    acme = Company(name=Name("Acme"))

    person_mgr.insert_many([bob, charlie])
    company_mgr.insert(acme)

    employments = [
        Employment(employee=bob, employer=acme, position=Position("Intern")),
        Employment(employee=charlie, employer=acme, position=Position("Manager")),
    ]
    employment_mgr.insert_many(employments)

    # Verify both exist
    all_before = employment_mgr.all()
    expected = 2
    actual = len(all_before)
    assert expected == actual

    # Act - Delete only "Intern" position using manager.delete() with attribute filter
    count = employment_mgr.delete(position="Intern")

    # Assert - Verify deletion count
    expected_count = 1
    assert expected_count == count

    # Assert - Only Manager should remain
    all_after = employment_mgr.all()
    expected = 1
    actual = len(all_after)
    assert expected == actual

    assert "Manager" == all_after[0].position.value


@pytest.mark.integration
@pytest.mark.order(143)
def test_delete_all_relations_of_type(db_with_schema):
    """Test deleting all relations of a specific type."""

    # Arrange
    class Name(String):
        pass

    class Position(String):
        pass

    class Person(Entity):
        flags = TypeFlags(name="person")
        name: Name = Flag(Key)

    class Company(Entity):
        flags = TypeFlags(name="company")
        name: Name = Flag(Key)

    class Employment(Relation):
        flags = TypeFlags(name="employment")
        employee: Role[Person] = Role("employee", Person)
        employer: Role[Company] = Role("employer", Company)
        position: Position

    schema_manager = SchemaManager(db_with_schema)
    schema_manager.register(Person, Company, Employment)
    schema_manager.sync_schema(force=True)

    # Setup multiple employments
    person_mgr = Person.manager(db_with_schema)
    company_mgr = Company.manager(db_with_schema)
    employment_mgr = Employment.manager(db_with_schema)

    people = [Person(name=Name(f"Person{i}")) for i in range(3)]
    companies = [Company(name=Name(f"Company{i}")) for i in range(2)]

    person_mgr.insert_many(people)
    company_mgr.insert_many(companies)

    employments = [
        Employment(employee=people[0], employer=companies[0], position=Position("Dev")),
        Employment(employee=people[1], employer=companies[0], position=Position("Manager")),
        Employment(employee=people[2], employer=companies[1], position=Position("CEO")),
    ]
    employment_mgr.insert_many(employments)

    # Verify all exist
    all_before = employment_mgr.all()
    expected = 3
    actual = len(all_before)
    assert expected == actual

    # Act - Delete all employments using manager.delete() with no filters
    count = employment_mgr.delete()

    # Assert - Verify deletion count
    expected_count = 3
    assert expected_count == count

    # Assert - No relations should remain
    all_after = employment_mgr.all()
    expected = 0
    actual = len(all_after)
    assert expected == actual


@pytest.mark.integration
@pytest.mark.order(144)
def test_delete_relation_preserves_role_player_entities(db_with_schema):
    """Test that deleting a relation does not delete the role player entities."""

    # Arrange
    class Name(String):
        pass

    class Position(String):
        pass

    class Person(Entity):
        flags = TypeFlags(name="person")
        name: Name = Flag(Key)

    class Company(Entity):
        flags = TypeFlags(name="company")
        name: Name = Flag(Key)

    class Employment(Relation):
        flags = TypeFlags(name="employment")
        employee: Role[Person] = Role("employee", Person)
        employer: Role[Company] = Role("employer", Company)
        position: Position

    schema_manager = SchemaManager(db_with_schema)
    schema_manager.register(Person, Company, Employment)
    schema_manager.sync_schema(force=True)

    # Setup
    person_mgr = Person.manager(db_with_schema)
    company_mgr = Company.manager(db_with_schema)
    employment_mgr = Employment.manager(db_with_schema)

    diana = Person(name=Name("Diana"))
    startup = Company(name=Name("Startup"))
    person_mgr.insert(diana)
    company_mgr.insert(startup)

    emp = Employment(employee=diana, employer=startup, position=Position("Founder"))
    employment_mgr.insert(emp)

    # Act - Delete relation using manager.delete()
    count = employment_mgr.delete()

    # Assert - Verify deletion count
    expected_count = 1
    assert expected_count == count

    # Assert - Relation deleted
    relations = employment_mgr.all()
    expected = 0
    actual = len(relations)
    assert expected == actual

    # Assert - Entities still exist
    people = person_mgr.all()
    expected_people = 1
    actual_people = len(people)
    assert expected_people == actual_people
    assert "Diana" == people[0].name.value

    companies = company_mgr.all()
    expected_companies = 1
    actual_companies = len(companies)
    assert expected_companies == actual_companies
    assert "Startup" == companies[0].name.value


@pytest.mark.integration
@pytest.mark.order(145)
def test_delete_relation_with_complex_filter(db_with_schema):
    """Test deleting relations with complex filter criteria."""

    # Arrange
    class Name(String):
        pass

    class Position(String):
        pass

    class Salary(Integer):
        pass

    class Person(Entity):
        flags = TypeFlags(name="person")
        name: Name = Flag(Key)

    class Company(Entity):
        flags = TypeFlags(name="company")
        name: Name = Flag(Key)

    class Employment(Relation):
        flags = TypeFlags(name="employment")
        employee: Role[Person] = Role("employee", Person)
        employer: Role[Company] = Role("employer", Company)
        position: Position
        salary: Salary

    schema_manager = SchemaManager(db_with_schema)
    schema_manager.register(Person, Company, Employment)
    schema_manager.sync_schema(force=True)

    # Setup
    person_mgr = Person.manager(db_with_schema)
    company_mgr = Company.manager(db_with_schema)
    employment_mgr = Employment.manager(db_with_schema)

    eve = Person(name=Name("Eve"))
    frank = Person(name=Name("Frank"))
    mega = Company(name=Name("MegaCorp"))

    person_mgr.insert_many([eve, frank])
    company_mgr.insert(mega)

    employments = [
        Employment(employee=eve, employer=mega, position=Position("Junior"), salary=Salary(50000)),
        Employment(
            employee=frank, employer=mega, position=Position("Senior"), salary=Salary(100000)
        ),
    ]
    employment_mgr.insert_many(employments)

    # Act - Delete only Junior position employments using manager.delete() with combined filters
    count = employment_mgr.delete(position="Junior", employer=mega)

    # Assert - Verify deletion count
    expected_count = 1
    assert expected_count == count

    # Assert - Only Senior employment remains
    remaining = employment_mgr.all()
    expected = 1
    actual = len(remaining)
    assert expected == actual

    assert "Senior" == remaining[0].position.value
    assert 100000 == remaining[0].salary.value

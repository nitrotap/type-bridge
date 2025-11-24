"""Integration tests for relation filtering operations using get() method.

Note: RelationManager uses get() with filters instead of having a separate filter() method.
These tests verify filtering relations by attributes and role players.
"""

import pytest

from type_bridge import (
    Entity,
    Flag,
    Key,
    Relation,
    Role,
    SchemaManager,
    String,
    TypeFlags,
)


@pytest.mark.integration
@pytest.mark.order(150)
def test_filter_relations_by_attribute(db_with_schema):
    """Test filtering relations by attribute value using get()."""

    # Arrange
    class Name(String):
        pass

    class Position(String):
        pass

    class Person(Entity):
        flags = TypeFlags(type_name="person")
        name: Name = Flag(Key)

    class Company(Entity):
        flags = TypeFlags(type_name="company")
        name: Name = Flag(Key)

    class Employment(Relation):
        flags = TypeFlags(type_name="employment")
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

    alice = Person(name=Name("Alice"))
    bob = Person(name=Name("Bob"))
    tech = Company(name=Name("Tech"))

    person_mgr.insert_many([alice, bob])
    company_mgr.insert(tech)

    employments = [
        Employment(employee=alice, employer=tech, position=Position("Engineer")),
        Employment(employee=bob, employer=tech, position=Position("Manager")),
    ]
    employment_mgr.insert_many(employments)

    # Act - Filter by position attribute
    result = employment_mgr.get(position="Engineer")

    # Assert
    expected = 1
    actual = len(result)
    assert expected == actual
    assert "Alice" == result[0].employee.name.value
    assert "Engineer" == result[0].position.value


@pytest.mark.integration
@pytest.mark.order(151)
def test_filter_relations_by_role_player(db_with_schema):
    """Test filtering relations by role player entity using get()."""

    # Arrange
    class Name(String):
        pass

    class Position(String):
        pass

    class Person(Entity):
        flags = TypeFlags(type_name="person")
        name: Name = Flag(Key)

    class Company(Entity):
        flags = TypeFlags(type_name="company")
        name: Name = Flag(Key)

    class Employment(Relation):
        flags = TypeFlags(type_name="employment")
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

    charlie = Person(name=Name("Charlie"))
    diana = Person(name=Name("Diana"))
    acme = Company(name=Name("Acme"))
    bigco = Company(name=Name("BigCo"))

    person_mgr.insert_many([charlie, diana])
    company_mgr.insert_many([acme, bigco])

    employments = [
        Employment(employee=charlie, employer=acme, position=Position("Dev")),
        Employment(employee=diana, employer=bigco, position=Position("Dev")),
    ]
    employment_mgr.insert_many(employments)

    # Act - Filter by employee role player
    result = employment_mgr.get(employee=charlie)

    # Assert
    expected = 1
    actual = len(result)
    assert expected == actual
    assert "Charlie" == result[0].employee.name.value
    assert "Acme" == result[0].employer.name.value


@pytest.mark.integration
@pytest.mark.order(152)
def test_filter_relations_combined_attribute_and_role(db_with_schema):
    """Test filtering relations by both attribute and role player."""

    # Arrange
    class Name(String):
        pass

    class Position(String):
        pass

    class Person(Entity):
        flags = TypeFlags(type_name="person")
        name: Name = Flag(Key)

    class Company(Entity):
        flags = TypeFlags(type_name="company")
        name: Name = Flag(Key)

    class Employment(Relation):
        flags = TypeFlags(type_name="employment")
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

    eve = Person(name=Name("Eve"))
    frank = Person(name=Name("Frank"))
    startup = Company(name=Name("Startup"))

    person_mgr.insert_many([eve, frank])
    company_mgr.insert(startup)

    employments = [
        Employment(employee=eve, employer=startup, position=Position("CTO")),
        Employment(employee=frank, employer=startup, position=Position("CEO")),
    ]
    employment_mgr.insert_many(employments)

    # Act - Filter by both position AND employer
    result = employment_mgr.get(position="CTO", employer=startup)

    # Assert
    expected = 1
    actual = len(result)
    assert expected == actual
    assert "Eve" == result[0].employee.name.value
    assert "CTO" == result[0].position.value


@pytest.mark.integration
@pytest.mark.order(153)
def test_filter_relations_with_invalid_attribute_raises_error(db_with_schema):
    """Test that filtering by invalid attribute raises ValueError."""

    # Arrange
    class Name(String):
        pass

    class Position(String):
        pass

    class Person(Entity):
        flags = TypeFlags(type_name="person")
        name: Name = Flag(Key)

    class Company(Entity):
        flags = TypeFlags(type_name="company")
        name: Name = Flag(Key)

    class Employment(Relation):
        flags = TypeFlags(type_name="employment")
        employee: Role[Person] = Role("employee", Person)
        employer: Role[Company] = Role("employer", Company)
        position: Position
        # Employment does NOT have a salary attribute

    schema_manager = SchemaManager(db_with_schema)
    schema_manager.register(Person, Company, Employment)
    schema_manager.sync_schema(force=True)

    employment_mgr = Employment.manager(db_with_schema)

    # Act & Assert - Filter by non-existent attribute should raise error
    with pytest.raises(ValueError) as exc_info:
        employment_mgr.get(salary=100000)

    error_msg = str(exc_info.value)
    assert "Unknown filter" in error_msg or "salary" in error_msg


@pytest.mark.integration
@pytest.mark.order(154)
def test_filter_relations_empty_result(db_with_schema):
    """Test filtering relations that match no results."""

    # Arrange
    class Name(String):
        pass

    class Position(String):
        pass

    class Person(Entity):
        flags = TypeFlags(type_name="person")
        name: Name = Flag(Key)

    class Company(Entity):
        flags = TypeFlags(type_name="company")
        name: Name = Flag(Key)

    class Employment(Relation):
        flags = TypeFlags(type_name="employment")
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

    grace = Person(name=Name("Grace"))
    mega = Company(name=Name("Mega"))

    person_mgr.insert(grace)
    company_mgr.insert(mega)

    emp = Employment(employee=grace, employer=mega, position=Position("Intern"))
    employment_mgr.insert(emp)

    # Act - Filter for non-existent position
    result = employment_mgr.get(position="CEO")

    # Assert - Should return empty list
    expected = 0
    actual = len(result)
    assert expected == actual


@pytest.mark.integration
@pytest.mark.order(155)
def test_filter_relations_with_multiple_matching_results(db_with_schema):
    """Test filtering relations that return multiple matches."""

    # Arrange
    class Name(String):
        pass

    class Position(String):
        pass

    class Person(Entity):
        flags = TypeFlags(type_name="person")
        name: Name = Flag(Key)

    class Company(Entity):
        flags = TypeFlags(type_name="company")
        name: Name = Flag(Key)

    class Employment(Relation):
        flags = TypeFlags(type_name="employment")
        employee: Role[Person] = Role("employee", Person)
        employer: Role[Company] = Role("employer", Company)
        position: Position

    schema_manager = SchemaManager(db_with_schema)
    schema_manager.register(Person, Company, Employment)
    schema_manager.sync_schema(force=True)

    # Setup multiple employments with same position
    person_mgr = Person.manager(db_with_schema)
    company_mgr = Company.manager(db_with_schema)
    employment_mgr = Employment.manager(db_with_schema)

    company = Company(name=Name("DevCorp"))
    company_mgr.insert(company)

    people = [Person(name=Name(f"Dev{i}")) for i in range(3)]
    person_mgr.insert_many(people)

    employments = [
        Employment(employee=person, employer=company, position=Position("Developer"))
        for person in people
    ]
    employment_mgr.insert_many(employments)

    # Act - Filter for all developers
    result = employment_mgr.get(position="Developer")

    # Assert - Should return all 3
    expected = 3
    actual = len(result)
    assert expected == actual

    # Verify all have Developer position
    for emp in result:
        assert "Developer" == emp.position.value


@pytest.mark.integration
@pytest.mark.order(156)
def test_filter_relations_by_both_role_players(db_with_schema):
    """Test filtering relations by multiple role players."""

    # Arrange
    class Name(String):
        pass

    class Position(String):
        pass

    class Person(Entity):
        flags = TypeFlags(type_name="person")
        name: Name = Flag(Key)

    class Company(Entity):
        flags = TypeFlags(type_name="company")
        name: Name = Flag(Key)

    class Employment(Relation):
        flags = TypeFlags(type_name="employment")
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

    henry = Person(name=Name("Henry"))
    iris = Person(name=Name("Iris"))
    corp1 = Company(name=Name("Corp1"))
    corp2 = Company(name=Name("Corp2"))

    person_mgr.insert_many([henry, iris])
    company_mgr.insert_many([corp1, corp2])

    employments = [
        Employment(employee=henry, employer=corp1, position=Position("Tech Lead")),
        Employment(employee=henry, employer=corp2, position=Position("Consultant")),
        Employment(employee=iris, employer=corp1, position=Position("Manager")),
    ]
    employment_mgr.insert_many(employments)

    # Act - Filter by both employee AND employer
    result = employment_mgr.get(employee=henry, employer=corp1)

    # Assert - Should return only Henry at Corp1
    expected = 1
    actual = len(result)
    assert expected == actual
    assert "Henry" == result[0].employee.name.value
    assert "Corp1" == result[0].employer.name.value
    assert "Tech Lead" == result[0].position.value

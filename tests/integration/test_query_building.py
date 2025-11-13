"""Integration tests for query building with real TypeDB."""

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
    String,
)


@pytest.mark.integration
@pytest.mark.order(20)
def test_simple_match_query(db_with_schema):
    """Test simple match query execution."""

    class Name(String):
        pass

    class Age(Integer):
        pass

    class Person(Entity):
        flags = EntityFlags(type_name="person")
        name: Name = Flag(Key)
        age: Age | None

    manager = Person.manager(db_with_schema)

    # Insert test data
    persons = [
        Person(name=Name("Alice"), age=Age(30)),
        Person(name=Name("Bob"), age=Age(25)),
        Person(name=Name("Charlie"), age=Age(30)),
    ]
    manager.insert_many(persons)

    # Execute query
    results = manager.get(age=30)

    assert len(results) == 2
    names = {p.name.value for p in results}
    assert names == {"Alice", "Charlie"}


@pytest.mark.integration
@pytest.mark.order(21)
def test_query_with_multiple_filters(db_with_schema):
    """Test query with multiple attribute filters."""
    from type_bridge import SchemaManager

    class Name(String):
        pass

    class Age(Integer):
        pass

    class City(String):
        pass

    class Person(Entity):
        flags = EntityFlags(type_name="person3")
        name: Name = Flag(Key)
        age: Age | None
        city: City | None

    # Create schema
    schema_manager = SchemaManager(db_with_schema)
    schema_manager.register(Person)
    schema_manager.sync_schema(force=True)

    manager = Person.manager(db_with_schema)

    # Insert test data
    persons = [
        Person(name=Name("Alice"), age=Age(30), city=City("NYC")),
        Person(name=Name("Bob"), age=Age(25), city=City("NYC")),
        Person(name=Name("Charlie"), age=Age(30), city=City("LA")),
    ]
    manager.insert_many(persons)

    # Query with multiple filters
    results = manager.get(age=30, city="NYC")

    assert len(results) == 1
    assert results[0].name.value == "Alice"


@pytest.mark.integration
@pytest.mark.order(22)
def test_query_with_limit_and_offset(db_with_schema):
    """Test query pagination with limit and offset."""

    class Name(String):
        pass

    class Age(Integer):
        pass

    class Person(Entity):
        flags = EntityFlags(type_name="person")
        name: Name = Flag(Key)
        age: Age | None

    manager = Person.manager(db_with_schema)

    # Insert test data
    persons = [Person(name=Name(f"Person{i}"), age=Age(20 + i)) for i in range(10)]
    manager.insert_many(persons)

    # Query with limit
    page1 = manager.filter().limit(5).execute()
    assert len(page1) == 5

    # Query with offset
    page2 = manager.filter().limit(5).offset(5).execute()
    assert len(page2) == 5

    # Verify different results (though order might not be guaranteed)
    # At minimum, we should have 10 total unique persons
    all_names = {p.name.value for p in page1} | {p.name.value for p in page2}
    assert len(all_names) == 10


@pytest.mark.integration
@pytest.mark.order(23)
def test_query_first_method(db_with_schema):
    """Test first() method for getting single result."""

    class Name(String):
        pass

    class Age(Integer):
        pass

    class Person(Entity):
        flags = EntityFlags(type_name="person")
        name: Name = Flag(Key)
        age: Age | None

    manager = Person.manager(db_with_schema)

    # Insert test data
    alice = Person(name=Name("Alice"), age=Age(30))
    manager.insert(alice)

    # Get first result
    result = manager.filter(name="Alice").first()

    assert result is not None
    assert result.name.value == "Alice"
    assert result.age.value == 30

    # Query with no results
    no_result = manager.filter(name="NonExistent").first()
    assert no_result is None


@pytest.mark.integration
@pytest.mark.order(24)
def test_query_count_method(db_with_schema):
    """Test count() method for counting results."""

    class Name(String):
        pass

    class Age(Integer):
        pass

    class Person(Entity):
        flags = EntityFlags(type_name="person")
        name: Name = Flag(Key)
        age: Age | None

    manager = Person.manager(db_with_schema)

    # Insert test data
    persons = [
        Person(name=Name("Alice"), age=Age(30)),
        Person(name=Name("Bob"), age=Age(30)),
        Person(name=Name("Charlie"), age=Age(25)),
    ]
    manager.insert_many(persons)

    # Count all
    total = manager.filter().count()
    assert total == 3

    # Count with filter
    age_30_count = manager.filter(age=30).count()
    assert age_30_count == 2


@pytest.mark.integration
@pytest.mark.order(25)
def test_relation_query_by_role_player(db_with_schema):
    """Test querying relations by role player."""

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

    # Create entities
    person_manager = Person.manager(db_with_schema)
    company_manager = Company.manager(db_with_schema)

    alice = Person(name=Name("Alice"))
    bob = Person(name=Name("Bob"))
    techcorp = Company(name=Name("TechCorp"))
    startupco = Company(name=Name("StartupCo"))

    person_manager.insert_many([alice, bob])
    company_manager.insert_many([techcorp, startupco])

    # Create relations
    employment_manager = Employment.manager(db_with_schema)
    employments = [
        Employment(employee=alice, employer=techcorp, position=Position("Engineer")),
        Employment(employee=bob, employer=techcorp, position=Position("Designer")),
        Employment(employee=alice, employer=startupco, position=Position("Consultant")),
    ]
    employment_manager.insert_many(employments)

    # Query by employee
    alice_jobs = employment_manager.get(employee=alice)
    assert len(alice_jobs) == 2
    positions = {job.position.value for job in alice_jobs}
    assert positions == {"Engineer", "Consultant"}

    # Query by employer
    techcorp_employees = employment_manager.get(employer=techcorp)
    assert len(techcorp_employees) == 2


@pytest.mark.integration
@pytest.mark.order(26)
def test_complex_query_with_relations(db_with_schema):
    """Test complex queries involving relations and attributes."""

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

    # Setup data
    person_manager = Person.manager(db_with_schema)
    company_manager = Company.manager(db_with_schema)
    employment_manager = Employment.manager(db_with_schema)

    alice = Person(name=Name("Alice"))
    techcorp = Company(name=Name("TechCorp"))

    person_manager.insert(alice)
    company_manager.insert(techcorp)

    employment = Employment(
        employee=alice, employer=techcorp, position=Position("Senior Engineer")
    )
    employment_manager.insert(employment)

    # Query by both role player and attribute
    results = employment_manager.get(employee=alice, position="Senior Engineer")

    assert len(results) == 1
    assert results[0].position.value == "Senior Engineer"


@pytest.mark.integration
@pytest.mark.order(27)
def test_query_with_multi_value_attributes(db_with_schema):
    """Test querying entities with multi-value attributes."""
    from type_bridge import SchemaManager

    class Name(String):
        pass

    class Tag(String):
        pass

    class Person(Entity):
        flags = EntityFlags(type_name="person4")
        name: Name = Flag(Key)
        tags: list[Tag] = Flag(Card(min=1))

    # Create schema
    schema_manager = SchemaManager(db_with_schema)
    schema_manager.register(Person)
    schema_manager.sync_schema(force=True)

    manager = Person.manager(db_with_schema)

    # Insert entities with tags
    persons = [
        Person(name=Name("Alice"), tags=[Tag("python"), Tag("ai")]),
        Person(name=Name("Bob"), tags=[Tag("python"), Tag("web")]),
        Person(name=Name("Charlie"), tags=[Tag("java"), Tag("backend")]),
    ]
    manager.insert_many(persons)

    # Fetch all and verify tags
    all_persons = manager.all()
    assert len(all_persons) == 3

    # Find person with specific tag
    alice = manager.get(name="Alice")[0]
    alice_tags = {tag.value for tag in alice.tags}
    assert alice_tags == {"python", "ai"}

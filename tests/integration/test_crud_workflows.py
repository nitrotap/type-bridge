"""Integration tests for CRUD workflows with real TypeDB."""

import pytest

from type_bridge import Card, Entity, EntityFlags, Flag, Integer, Key, String


@pytest.mark.integration
@pytest.mark.order(10)
def test_insert_and_fetch_single_entity(db_with_schema):
    """Test inserting and fetching a single entity."""

    # Define models (matching db_with_schema fixture)
    class Name(String):
        pass

    class Age(Integer):
        pass

    class Person(Entity):
        flags = EntityFlags(type_name="person")
        name: Name = Flag(Key)
        age: Age | None

    # Create manager
    manager = Person.manager(db_with_schema)

    # Insert entity
    alice = Person(name=Name("Alice"), age=Age(30))
    manager.insert(alice)

    # Fetch entity
    results = manager.get(name="Alice")

    assert len(results) == 1
    assert results[0].name.value == "Alice"
    assert results[0].age.value == 30


@pytest.mark.integration
@pytest.mark.order(11)
def test_insert_many_and_fetch_all(db_with_schema):
    """Test bulk insertion and fetching all entities."""

    class Name(String):
        pass

    class Age(Integer):
        pass

    class Person(Entity):
        flags = EntityFlags(type_name="person")
        name: Name = Flag(Key)
        age: Age | None

    manager = Person.manager(db_with_schema)

    # Bulk insert
    persons = [
        Person(name=Name("Bob"), age=Age(25)),
        Person(name=Name("Charlie"), age=Age(35)),
        Person(name=Name("Diana"), age=Age(28)),
    ]
    manager.insert_many(persons)

    # Fetch all
    all_persons = manager.all()

    assert len(all_persons) == 3
    names = {p.name.value for p in all_persons}
    assert names == {"Bob", "Charlie", "Diana"}


@pytest.mark.integration
@pytest.mark.order(12)
def test_fetch_with_filter(db_with_schema):
    """Test fetching entities with attribute filters."""

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
        Person(name=Name("Eve"), age=Age(30)),
        Person(name=Name("Frank"), age=Age(30)),
        Person(name=Name("Grace"), age=Age(40)),
    ]
    manager.insert_many(persons)

    # Filter by age
    age_30 = manager.get(age=30)

    assert len(age_30) == 2
    names = {p.name.value for p in age_30}
    assert names == {"Eve", "Frank"}


@pytest.mark.integration
@pytest.mark.order(13)
def test_update_single_value_attribute(db_with_schema):
    """Test updating a single-value attribute."""

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
    henry = Person(name=Name("Henry"), age=Age(25))
    manager.insert(henry)

    # Fetch and modify
    results = manager.get(name="Henry")
    henry_fetched = results[0]
    henry_fetched.age = Age(26)

    # Update
    manager.update(henry_fetched)

    # Verify update
    updated = manager.get(name="Henry")
    assert updated[0].age.value == 26


@pytest.mark.integration
@pytest.mark.order(14)
def test_update_multi_value_attribute(db_with_schema):
    """Test updating multi-value attributes."""
    from type_bridge import SchemaManager

    # Define extended schema with multi-value attribute
    class Name(String):
        pass

    class Tag(String):
        pass

    class Person(Entity):
        flags = EntityFlags(type_name="person2")
        name: Name = Flag(Key)
        tags: list[Tag] = Flag(Card(min=1))

    # Create schema
    schema_manager = SchemaManager(db_with_schema)
    schema_manager.register(Person)
    schema_manager.sync_schema(force=True)

    manager = Person.manager(db_with_schema)

    # Insert entity with tags
    iris = Person(name=Name("Iris"), tags=[Tag("python"), Tag("typedb")])
    manager.insert(iris)

    # Fetch and modify tags
    results = manager.get(name="Iris")
    iris_fetched = results[0]
    iris_fetched.tags = [Tag("python"), Tag("typedb"), Tag("ai")]

    # Update
    manager.update(iris_fetched)

    # Verify update
    updated = manager.get(name="Iris")
    tag_values = {tag.value for tag in updated[0].tags}
    assert tag_values == {"python", "typedb", "ai"}


@pytest.mark.integration
@pytest.mark.order(15)
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


@pytest.mark.integration
@pytest.mark.order(16)
def test_chainable_query(db_with_schema):
    """Test chainable query API."""

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
        Person(name=Name(f"Person{i}"), age=Age(20 + i)) for i in range(10)
    ]
    manager.insert_many(persons)

    # Chainable query: filter + limit
    query = manager.filter(age=22)
    results = query.limit(1).execute()

    assert len(results) == 1
    assert results[0].age.value == 22

    # Count query
    count = manager.filter(age=25).count()
    assert count == 1


@pytest.mark.integration
@pytest.mark.order(17)
def test_entity_with_optional_attributes(db_with_schema):
    """Test CRUD with optional attributes."""

    class Name(String):
        pass

    class Age(Integer):
        pass

    class Person(Entity):
        flags = EntityFlags(type_name="person")
        name: Name = Flag(Key)
        age: Age | None

    manager = Person.manager(db_with_schema)

    # Insert entity without optional attribute
    kate = Person(name=Name("Kate"), age=None)
    manager.insert(kate)

    # Fetch and verify
    results = manager.get(name="Kate")
    assert len(results) == 1
    assert results[0].name.value == "Kate"
    # Age should be None or not set
    assert results[0].age is None or not hasattr(results[0], "age")


@pytest.mark.integration
@pytest.mark.order(18)
def test_relation_crud(db_with_schema):
    """Test CRUD operations with relations."""
    from type_bridge import Relation, RelationFlags, Role

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
    techcorp = Company(name=Name("TechCorp"))

    person_manager.insert(alice)
    company_manager.insert(techcorp)

    # Create relation
    employment_manager = Employment.manager(db_with_schema)
    employment = Employment(
        employee=alice, employer=techcorp, position=Position("Engineer")
    )
    employment_manager.insert(employment)

    # Fetch relation by role player
    results = employment_manager.get(employee=alice)
    assert len(results) == 1
    assert results[0].position.value == "Engineer"

    # Fetch relation by attribute
    results_by_pos = employment_manager.get(position="Engineer")
    assert len(results_by_pos) == 1

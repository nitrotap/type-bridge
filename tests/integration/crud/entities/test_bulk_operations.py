"""Integration tests for bulk entity operations."""

import pytest

from type_bridge import Card, Entity, Flag, Integer, Key, String, TypeFlags


@pytest.mark.integration
@pytest.mark.order(20)
def test_update_many(db_with_schema):
    """Update multiple entities in a single call."""

    class Name(String):
        pass

    class Age(Integer):
        pass

    class Person(Entity):
        flags = TypeFlags(name="person")
        name: Name = Flag(Key)
        age: Age | None

    manager = Person.manager(db_with_schema)

    people = [
        Person(name=Name("Alice"), age=Age(30)),
        Person(name=Name("Bob"), age=Age(40)),
    ]
    manager.insert_many(people)

    # Bump ages and update in bulk
    people[0].age = Age(31)
    people[1].age = Age(41)
    manager.update_many(people)

    fetched = sorted(manager.all(), key=lambda p: p.name.value)
    assert [p.name.value for p in fetched] == ["Alice", "Bob"]
    # Age is annotated optional, guard before .value for type checkers
    assert fetched[0].age is not None and fetched[1].age is not None
    assert [fetched[0].age.value, fetched[1].age.value] == [31, 41]


@pytest.mark.integration
@pytest.mark.order(20)
def test_update_many_multivalue(db_with_schema):
    """Update many with multi-value attributes handled correctly."""

    class Name(String):
        pass

    class Tag(String):
        pass

    class Person(Entity):
        flags = TypeFlags(name="person_with_tags")
        name: Name = Flag(Key)
        tags: list[Tag] = Flag(Card(min=0))

    mgr = Person.manager(db_with_schema)

    # Register schema for this test entity (additive, does not drop existing schema)
    from type_bridge import SchemaManager

    schema_manager = SchemaManager(db_with_schema)
    schema_manager.register(Person)
    schema_manager.sync_schema(force=False)

    people = [
        Person(name=Name("A"), tags=[Tag("x"), Tag("y")]),
        Person(name=Name("B"), tags=[Tag("y")]),
    ]
    mgr.insert_many(people)

    people[0].tags = [Tag("x"), Tag("z")]
    people[1].tags = []

    mgr.update_many(people)

    updated = sorted(mgr.all(), key=lambda p: p.name.value)
    assert {t.value for t in updated[0].tags} == {"x", "z"}
    assert updated[1].tags == []


@pytest.mark.integration
@pytest.mark.order(21)
def test_delete_many_with_in_filter(db_with_schema):
    """Delete multiple entities using __in filter expansion."""

    class Name(String):
        pass

    class Age(Integer):
        pass

    class Person(Entity):
        flags = TypeFlags(name="person")
        name: Name = Flag(Key)
        age: Age | None

    manager = Person.manager(db_with_schema)

    people = [
        Person(name=Name("Alice"), age=Age(30)),
        Person(name=Name("Bob"), age=Age(40)),
        Person(name=Name("Dora"), age=Age(50)),
    ]
    manager.insert_many(people)

    deleted = manager.delete_many(name__in=[Name("Bob"), "Dora"])
    assert deleted == 2

    remaining = {p.name.value for p in manager.all()}
    assert remaining == {"Alice"}


@pytest.mark.integration
@pytest.mark.order(21)
def test_delete_many_with_base_and_in(db_with_schema):
    """Combine base filter and __in disjunction in bulk delete."""

    class Name(String):
        pass

    class Age(Integer):
        pass

    class Person(Entity):
        flags = TypeFlags(name="person")
        name: Name = Flag(Key)
        age: Age | None

    mgr = Person.manager(db_with_schema)

    people = [
        Person(name=Name("X1"), age=Age(10)),
        Person(name=Name("X2"), age=Age(10)),
        Person(name=Name("X3"), age=Age(20)),
    ]
    mgr.insert_many(people)

    deleted = mgr.delete_many(age=Age(10), name__in=[Name("X1"), "X2", "X999"])
    assert deleted == 2

    remaining = {p.name.value for p in mgr.all()}
    assert remaining == {"X3"}


@pytest.mark.integration
@pytest.mark.order(22)
def test_delete_many_empty_in_returns_zero(db_with_schema):
    """Ensure empty __in filter does not delete anything."""

    class Name(String):
        pass

    class Age(Integer):
        pass

    class Person(Entity):
        flags = TypeFlags(name="person")
        name: Name = Flag(Key)
        age: Age | None

    manager = Person.manager(db_with_schema)

    manager.insert_many([Person(name=Name("Solo"), age=None)])

    deleted = manager.delete_many(name__in=[])
    assert deleted == 0

    remaining = manager.all()
    assert len(remaining) == 1
    assert remaining[0].name.value == "Solo"

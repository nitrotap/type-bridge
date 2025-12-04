"""Integration tests for entity put operations."""

import pytest

from type_bridge import Entity, Flag, Integer, Key, String, TypeFlags


@pytest.mark.integration
@pytest.mark.order(13)
def test_put_single_entity(db_with_schema):
    """Test putting a single entity."""

    class Name(String):
        pass

    class Age(Integer):
        pass

    class Person(Entity):
        flags = TypeFlags(name="person")
        name: Name = Flag(Key)
        age: Age | None

    person_manager = Person.manager(db_with_schema)

    # Create entity
    alice = Person(name=Name("Alice"), age=Age(30))

    # First put should insert
    person_manager.put(alice)

    # Verify entity exists
    results = person_manager.get(name="Alice")
    assert len(results) == 1
    assert results[0].name.value == "Alice"
    assert results[0].age is not None
    assert results[0].age.value == 30

    # Second put should not create duplicate (idempotent)
    person_manager.put(alice)

    # Should still have only 1 person
    results = person_manager.all()
    assert len(results) == 1


@pytest.mark.integration
@pytest.mark.order(14)
def test_put_many_entities(db_with_schema):
    """Test putting multiple entities."""

    class Name(String):
        pass

    class Age(Integer):
        pass

    class Person(Entity):
        flags = TypeFlags(name="person")
        name: Name = Flag(Key)
        age: Age | None

    person_manager = Person.manager(db_with_schema)

    # Create entities
    persons = [
        Person(name=Name("Alice"), age=Age(30)),
        Person(name=Name("Bob"), age=Age(25)),
        Person(name=Name("Charlie"), age=Age(35)),
    ]

    # First put_many should insert all
    person_manager.put_many(persons)

    # Verify all entities exist
    results = person_manager.all()
    assert len(results) == 3

    # Second put_many should not create duplicates
    person_manager.put_many(persons)

    # Should still have only 3 persons
    results = person_manager.all()
    assert len(results) == 3


@pytest.mark.integration
@pytest.mark.order(15)
def test_put_partial_match(db_with_schema):
    """Test put with all-or-nothing semantics.

    According to TypeDB docs, put works on all-or-nothing basis:
    - If the entire pattern matches, nothing is inserted
    - If any part fails to match, the entire pattern is inserted

    This means putting [Alice, Bob] when Alice exists will try to insert
    both Alice and Bob, causing a key constraint violation.
    """

    class Name(String):
        pass

    class Age(Integer):
        pass

    class Person(Entity):
        flags = TypeFlags(name="person")
        name: Name = Flag(Key)
        age: Age | None

    person_manager = Person.manager(db_with_schema)

    # Insert Alice
    alice = Person(name=Name("Alice"), age=Age(30))
    person_manager.insert(alice)

    # Put both Alice and Bob (Alice exists, Bob doesn't)
    # This should fail because put will try to insert the entire pattern
    # including Alice (who already exists), violating @key constraint
    persons = [
        Person(name=Name("Alice"), age=Age(30)),
        Person(name=Name("Bob"), age=Age(25)),
    ]

    # Expect constraint violation due to all-or-nothing semantics
    with pytest.raises(Exception) as exc_info:
        person_manager.put_many(persons)

    # Verify it's a key constraint violation
    assert "unique" in str(exc_info.value).lower() or "key" in str(exc_info.value).lower()

    # Only Alice should exist (Bob was not inserted due to failure)
    results = person_manager.all()
    assert len(results) == 1
    assert results[0].name.value == "Alice"


@pytest.mark.integration
@pytest.mark.order(16)
def test_put_vs_insert_duplicates(db_with_schema):
    """Test that put prevents duplicates while insert creates them."""

    class Name(String):
        pass

    class Age(Integer):
        pass

    class Person(Entity):
        flags = TypeFlags(name="person")
        name: Name = Flag(Key)
        age: Age | None

    person_manager = Person.manager(db_with_schema)

    alice = Person(name=Name("Alice"), age=Age(30))

    # Using insert creates entity
    person_manager.insert(alice)

    # Using put should be idempotent
    person_manager.put(alice)
    person_manager.put(alice)

    # Get all persons - put should not have created extra duplicates
    results = person_manager.all()

    # With @key constraint, we should have exactly 1 person
    assert len(results) == 1
    assert results[0].name.value == "Alice"

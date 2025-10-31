"""Tests for the Card API with Flag system."""

from type_bridge import Card, Entity, EntityFlags, Flag, Integer, String


def test_cardinal_with_min_only():
    """Test Card(min=N) for unbounded maximum."""

    class Tag(String):
        pass

    class Person(Entity):
        flags = EntityFlags(type_name="person")
        tags: list[Tag] = Flag(Card(min=2))  # @card(2..) - at least 2

    owned = Person.get_owned_attributes()
    assert "tags" in owned
    assert owned["tags"].flags.card_min == 2
    assert owned["tags"].flags.card_max is None


def test_cardinal_with_max_only():
    """Test Card(max=N) for maximum cardinality (min defaults to 0)."""

    class Lang(String):
        pass

    class Person(Entity):
        flags = EntityFlags(type_name="person")
        languages: list[Lang] = Flag(Card(max=5))  # @card(0..5) - up to 5 (min defaults to 0)

    owned = Person.get_owned_attributes()
    assert "languages" in owned
    assert owned["languages"].flags.card_min == 0
    assert owned["languages"].flags.card_max == 5


def test_cardinal_with_min_and_max():
    """Test Card(min, max) for bounded cardinality."""

    class Job(String):
        pass

    class Person(Entity):
        flags = EntityFlags(type_name="person")
        jobs: list[Job] = Flag(Card(1, 3))  # @card(1..3) - 1 to 3 jobs

    owned = Person.get_owned_attributes()
    assert "jobs" in owned
    assert owned["jobs"].flags.card_min == 1
    assert owned["jobs"].flags.card_max == 3


def test_cardinal_schema_generation():
    """Test that Card generates correct schema."""

    class Tag(String):
        pass

    class Lang(String):
        pass

    class Job(String):
        pass

    class Person(Entity):
        flags = EntityFlags(type_name="person")
        tags: list[Tag] = Flag(Card(min=2))
        languages: list[Lang] = Flag(Card(max=5))
        jobs: list[Job] = Flag(Card(1, 3))

    schema = Person.to_schema_definition()
    assert "entity person" in schema
    assert "owns tag @card(2..)" in schema
    assert "owns lang @card(0..5)" in schema
    assert "owns job @card(1..3)" in schema


def test_cardinal_with_long_attribute():
    """Test Card works with Long attributes."""

    class Priority(Integer):
        pass

    class Task(Entity):
        flags = EntityFlags(type_name="task")
        priorities: list[Priority] = Flag(Card(1, 5))

    owned = Task.get_owned_attributes()
    assert "priorities" in owned
    assert owned["priorities"].typ is Priority
    assert owned["priorities"].flags.card_min == 1
    assert owned["priorities"].flags.card_max == 5


def test_cardinal_instance_creation():
    """Test creating instances with Card fields."""

    class Tag(String):
        pass

    class Person(Entity):
        flags = EntityFlags(type_name="person")
        tags: list[Tag] = Flag(Card(2, 5))

    # Should accept lists
    person = Person(tags=["python", "rust", "go"]) # pyright: ignore
    assert person.tags == ["python", "rust", "go"]


def test_cardinal_insert_query():
    """Test insert query generation with Card fields."""

    class Tag(String):
        pass

    class Person(Entity):
        flags = EntityFlags(type_name="person")
        tags: list[Tag] = Flag(Card(min=2))

    person = Person(tags=["python", "rust"]) # pyright: ignore
    query = person.to_insert_query()

    assert "$e isa person" in query
    assert 'has tag "python"' in query
    assert 'has tag "rust"' in query


def test_cardinal_pyright_compliance():
    """Test that Card API is pyright-compliant."""

    class Tag(String):
        pass

    # This should not cause pyright errors with proper usage
    class Person(Entity):
        flags = EntityFlags(type_name="person")
        tags: list[Tag] = Flag(Card(2, 5))  # No pyright error!

    # Verify it works at runtime
    owned = Person.get_owned_attributes()
    assert owned["tags"].flags.card_min == 2
    assert owned["tags"].flags.card_max == 5

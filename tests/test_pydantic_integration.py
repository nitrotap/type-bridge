"""Tests for Pydantic integration features."""

import pytest
from pydantic import ValidationError

from type_bridge import Entity, EntityFlags, Integer, String


def test_pydantic_validation():
    """Test that Pydantic validates attribute types."""

    class Name(String):
        pass

    class Age(Integer):
        pass

    class Person(Entity):
        flags = EntityFlags(type_name="person")
        name: Name
        age: Age

    # Valid creation
    alice = Person(name="Alice", age=30)
    assert alice.name == "Alice"
    assert alice.age == 30

    # Type coercion works
    bob = Person(name="Bob", age="25")  # String will be converted to int
    assert bob.age == 25
    assert isinstance(bob.age, int)


def test_pydantic_validation_on_assignment():
    """Test that Pydantic validates on attribute assignment."""

    class Name(String):
        pass

    class Age(Integer):
        pass

    class Person(Entity):
        flags = EntityFlags(type_name="person")
        name: Name
        age: Age

    alice = Person(name="Alice", age=30)

    # Valid assignment
    alice.age = 31
    assert alice.age == 31

    # Type coercion on assignment
    alice.age = "32"
    assert alice.age == 32
    assert isinstance(alice.age, int)


def test_pydantic_json_serialization():
    """Test Pydantic's JSON serialization."""

    class Name(String):
        pass

    class Age(Integer):
        pass

    class Person(Entity):
        flags = EntityFlags(type_name="person")
        name: Name
        age: Age

    alice = Person(name="Alice", age=30)

    # Serialize to dict
    alice_dict = alice.model_dump()
    assert alice_dict == {"name": "Alice", "age": 30}

    # Serialize to JSON
    alice_json = alice.model_dump_json()
    assert '"name":"Alice"' in alice_json
    assert '"age":30' in alice_json


def test_pydantic_json_deserialization():
    """Test Pydantic's JSON deserialization."""

    class Name(String):
        pass

    class Age(Integer):
        pass

    class Person(Entity):
        flags = EntityFlags(type_name="person")
        name: Name
        age: Age

    # Deserialize from dict
    person_data = {"name": "Bob", "age": 25}
    bob = Person(**person_data)
    assert bob.name == "Bob"
    assert bob.age == 25

    # Deserialize from JSON
    json_data = '{"name": "Charlie", "age": 35}'
    charlie = Person.model_validate_json(json_data)
    assert charlie.name == "Charlie"
    assert charlie.age == 35


def test_pydantic_model_copy():
    """Test Pydantic's model copy functionality."""

    class Name(String):
        pass

    class Age(Integer):
        pass

    class Person(Entity):
        flags = EntityFlags(type_name="person")
        name: Name
        age: Age

    alice = Person(name="Alice", age=30)

    # Create a copy with modifications
    alice_older = alice.model_copy(update={"age": 31})
    assert alice_older.name == "Alice"
    assert alice_older.age == 31
    assert alice.age == 30  # Original unchanged


def test_pydantic_with_optional_fields():
    """Test Pydantic with optional fields."""

    class Name(String):
        pass

    class Email(String):
        pass

    class Person(Entity):
        flags = EntityFlags(type_name="person")
        name: Name
        email: Email = None  # Optional field with default

    # Create without optional field
    alice = Person(name="Alice")
    assert alice.name == "Alice"
    assert alice.email is None

    # Create with optional field
    bob = Person(name="Bob", email="bob@example.com")
    assert bob.name == "Bob"
    assert bob.email == "bob@example.com"


def test_pydantic_with_default_values():
    """Test Pydantic with default values."""

    class Name(String):
        pass

    class Age(Integer):
        pass

    class Person(Entity):
        flags = EntityFlags(type_name="person")
        name: Name
        age: Age = 0  # Default value

    # Create without age
    alice = Person(name="Alice")
    assert alice.name == "Alice"
    assert alice.age == 0

    # Create with age
    bob = Person(name="Bob", age=25)
    assert bob.name == "Bob"
    assert bob.age == 25


def test_pydantic_type_coercion():
    """Test Pydantic's type validation."""

    class Name(String):
        pass

    class Age(Integer):
        pass

    class Person(Entity):
        flags = EntityFlags(type_name="person")
        name: Name
        age: Age

    # Valid string accepted
    alice = Person(name="Alice", age=30)
    assert isinstance(alice.name, str)
    assert alice.name == "Alice"
    assert isinstance(alice.age, int)
    assert alice.age == 30

    # Another valid instance
    bob = Person(name="Bob", age=25)
    assert isinstance(bob.name, str)
    assert bob.name == "Bob"
    assert isinstance(bob.age, int)
    assert bob.age == 25


def test_pydantic_validation_errors():
    """Test that Pydantic raises validation errors for invalid data."""

    class Name(String):
        pass

    class Age(Integer):
        pass

    class Person(Entity):
        flags = EntityFlags(type_name="person")
        name: Name
        age: Age

    # Invalid type that can't be coerced
    with pytest.raises(ValidationError) as exc_info:
        Person(name="Alice", age="not_a_number")

    assert "age" in str(exc_info.value)

"""Basic tests for the new Attribute-based API."""

from typing import ClassVar

from type_bridge import Entity, Key, Long, Relation, Role, String


def test_attribute_creation():
    """Test creating attribute types."""

    class Name(String):
        pass

    class Age(Long):
        pass

    assert Name.get_attribute_name() == "name"
    assert Name.get_value_type() == "string"
    assert Age.get_attribute_name() == "age"
    assert Age.get_value_type() == "long"


def test_key_attribute():
    """Test creating key attributes."""

    class Email(String):
        pass

    EmailKey = Key(Email)

    assert EmailKey.is_key() is True
    assert EmailKey.get_attribute_name() == "email"


def test_entity_creation():
    """Test creating entities with owned attributes."""

    class Name(String):
        pass

    class Age(Long):
        pass

    NameKey = Key(Name)

    class Person(Entity):
        __type_name__ = "person"
        name: NameKey
        age: Age

    # Check owned attributes
    owned = Person.get_owned_attributes()
    assert "name" in owned
    assert "age" in owned
    assert owned["name"].is_key() is True
    assert owned["age"].is_key() is False

    # Check type name
    assert Person.get_type_name() == "person"


def test_entity_instance():
    """Test creating entity instances."""

    class Name(String):
        pass

    class Age(Long):
        pass

    class Person(Entity):
        __type_name__ = "person"
        name: Name
        age: Age

    alice = Person(name="Alice", age=30)
    assert alice.name == "Alice"
    assert alice.age == 30


def test_entity_schema_generation():
    """Test generating entity schema."""

    class Name(String):
        pass

    class Age(Long):
        pass

    NameKey = Key(Name)

    class Person(Entity):
        __type_name__ = "person"
        name: NameKey
        age: Age

    schema = Person.to_schema_definition()
    assert "person sub entity" in schema
    assert "owns name @key" in schema
    assert "owns age" in schema


def test_entity_insert_query():
    """Test generating insert query."""

    class Name(String):
        pass

    class Age(Long):
        pass

    class Person(Entity):
        __type_name__ = "person"
        name: Name
        age: Age

    alice = Person(name="Alice", age=30)
    query = alice.to_insert_query()

    assert "$e isa person" in query
    assert 'has name "Alice"' in query
    assert "has age 30" in query


def test_relation_creation():
    """Test creating relations."""

    class Name(String):
        pass

    class Person(Entity):
        __type_name__ = "person"
        name: Name

    class Friendship(Relation):
        __type_name__ = "friendship"

        friend1: ClassVar[Role] = Role("friend", Person)
        friend2: ClassVar[Role] = Role("friend", Person)

    # Check roles
    assert "friend1" in Friendship._roles
    assert "friend2" in Friendship._roles
    assert Friendship._roles["friend1"].role_name == "friend"


def test_relation_with_attributes():
    """Test relations with owned attributes."""

    class Name(String):
        pass

    class SinceYear(Long):
        pass

    class Person(Entity):
        __type_name__ = "person"
        name: Name

    class Friendship(Relation):
        __type_name__ = "friendship"

        friend1: ClassVar[Role] = Role("friend", Person)
        friend2: ClassVar[Role] = Role("friend", Person)

        since_year: SinceYear

    # Check owned attributes
    owned = Friendship.get_owned_attributes()
    assert "since_year" in owned
    assert owned["since_year"].get_attribute_name() == "sinceyear"


def test_relation_schema_generation():
    """Test generating relation schema."""

    class Name(String):
        pass

    class Person(Entity):
        __type_name__ = "person"
        name: Name

    class Friendship(Relation):
        __type_name__ = "friendship"

        friend1: ClassVar[Role] = Role("friend", Person)
        friend2: ClassVar[Role] = Role("friend", Person)

    schema = Friendship.to_schema_definition()
    assert "friendship sub relation" in schema
    assert "relates friend" in schema


def test_attribute_schema_generation():
    """Test generating attribute schema."""

    class Name(String):
        pass

    class Age(Long):
        pass

    name_schema = Name.to_schema_definition()
    age_schema = Age.to_schema_definition()

    assert "name sub attribute, value string;" in name_schema
    assert "age sub attribute, value long;" in age_schema

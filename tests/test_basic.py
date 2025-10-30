"""Basic tests for the new Attribute-based API."""

from typing import ClassVar

from type_bridge import (
    Entity,
    EntityFlags,
    Flag,
    Key,
    Long,
    Min,
    Relation,
    RelationFlags,
    Role,
    String,
)


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


def test_flag_annotation():
    """Test Flag annotation system for Key and Unique."""

    class Email(String):
        pass

    # Test Key flag
    key_flag = Flag(Key)
    assert key_flag.is_key is True
    assert key_flag.to_typeql_annotations() == ["@key"]

    # Test Unique flag
    from type_bridge import Unique
    unique_flag = Flag(Unique)
    assert unique_flag.is_unique is True
    assert unique_flag.to_typeql_annotations() == ["@unique"]

    # Test combined Key + Unique flags
    combined_flag = Flag(Key, Unique)
    assert combined_flag.is_key is True
    assert combined_flag.is_unique is True
    assert combined_flag.to_typeql_annotations() == ["@key", "@unique"]


def test_entity_creation():
    """Test creating entities with owned attributes using generic types."""

    class Name(String):
        pass

    class Age(Long):
        pass

    class Tag(String):
        pass

    class Email(String):
        pass

    class Person(Entity):
        flags = EntityFlags(type_name="person")
        name: Name = Flag(Key)  # @key
        age: Age | None  # @card(0,1) - using Optional
        email: Email | None  # @card(0,1) - using union syntax
        tags: Min[2, Tag]  # @card(2)

    # Check owned attributes
    owned = Person.get_owned_attributes()
    assert "name" in owned
    assert "age" in owned
    assert "email" in owned
    assert "tags" in owned

    # Check Key flag
    assert owned["name"]["flags"].is_key is True
    assert owned["age"]["flags"].is_key is False
    assert owned["email"]["flags"].is_key is False

    # Check cardinality - both Optional and Union syntax work
    assert owned["name"]["flags"].card_min == 1
    assert owned["name"]["flags"].card_max == 1
    assert owned["age"]["flags"].card_min == 0
    assert owned["age"]["flags"].card_max == 1
    assert owned["email"]["flags"].card_min == 0
    assert owned["email"]["flags"].card_max == 1
    assert owned["tags"]["flags"].card_min == 2
    assert owned["tags"]["flags"].card_max is None

    # Check type name
    assert Person.get_type_name() == "person"


def test_entity_instance():
    """Test creating entity instances."""

    class Name(String):
        pass

    class Age(Long):
        pass

    class Person(Entity):
        flags = EntityFlags(type_name="person")
        name: Name
        age: Age

    alice = Person(name="Alice", age=30)
    assert alice.name == "Alice"
    assert alice.age == 30


def test_entity_schema_generation():
    """Test generating entity schema with generic cardinality types."""

    class Name(String):
        pass

    class Age(Long):
        pass

    class Email(String):
        pass

    class Person(Entity):
        flags = EntityFlags(type_name="person")
        name: Name = Flag(Key)  # @key with default card(1,1)
        age: Age | None  # @card(0,1) - Optional syntax
        email: Email | None  # @card(0,1) - Union syntax

    schema = Person.to_schema_definition()
    assert "person sub entity" in schema
    assert "owns name @key @card(1,1)" in schema
    assert "owns age @card(0,1)" in schema
    assert "owns email @card(0,1)" in schema


def test_entity_insert_query():
    """Test generating insert query."""

    class Name(String):
        pass

    class Age(Long):
        pass

    class Person(Entity):
        flags = EntityFlags(type_name="person")
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
        flags = EntityFlags(type_name="person")
        name: Name

    class Friendship(Relation):
        flags = RelationFlags(type_name="friendship")

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
        flags = EntityFlags(type_name="person")
        name: Name

    class Friendship(Relation):
        flags = RelationFlags(type_name="friendship")

        friend1: ClassVar[Role] = Role("friend", Person)
        friend2: ClassVar[Role] = Role("friend", Person)

        since_year: SinceYear  # default card(1,1)

    # Check owned attributes
    owned = Friendship.get_owned_attributes()
    assert "since_year" in owned
    assert owned["since_year"]["type"].get_attribute_name() == "sinceyear"
    assert owned["since_year"]["flags"].card_min == 1
    assert owned["since_year"]["flags"].card_max == 1


def test_relation_schema_generation():
    """Test generating relation schema."""

    class Name(String):
        pass

    class Person(Entity):
        flags = EntityFlags(type_name="person")
        name: Name

    class Friendship(Relation):
        flags = RelationFlags(type_name="friendship")

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



"""Tests for Entity update API.

NOTE: This test file intentionally uses raw values (strings, ints, lists) instead of
wrapped Attribute instances to verify Pydantic's type coercion works correctly.
The type: ignore comments are expected and indicate we're testing runtime validation.
"""

from type_bridge import Card, Entity, EntityFlags, Flag, Integer, Key, String


class Name(String):
    """Name attribute."""


class Age(Integer):
    """Age attribute."""


class Tag(String):
    """Tag attribute."""


class Status(String):
    """Status attribute."""


class Person(Entity):
    """Person entity with single and multi-value attributes."""

    flags = EntityFlags(type_name="person")
    name: Name = Flag(Key)
    age: Age | None
    status: Status
    tags: list[Tag] = Flag(Card(max=5))


def test_update_single_value_attribute():
    """Test updating a single-value attribute."""
    from type_bridge import Database

    db = Database(address="localhost:1729", database="test_update")
    person_manager = Person.manager(db)

    # Should generate correct TypeQL with update clause
    # This is a unit test checking the logic, not integration with TypeDB
    owned_attrs = Person.get_owned_attributes()

    # Check age is single-value
    age_info = owned_attrs["age"]
    assert person_manager._is_multi_value_attribute(age_info.flags) is False

    # Check status is single-value
    status_info = owned_attrs["status"]
    assert person_manager._is_multi_value_attribute(status_info.flags) is False


def test_update_multi_value_attribute():
    """Test updating a multi-value attribute."""
    from type_bridge import Database

    db = Database(address="localhost:1729", database="test_update")
    person_manager = Person.manager(db)

    owned_attrs = Person.get_owned_attributes()

    # Check tags is multi-value
    tags_info = owned_attrs["tags"]
    assert person_manager._is_multi_value_attribute(tags_info.flags) is True


def test_update_reads_entity_state():
    """Test that update reads all attributes from entity state."""
    from type_bridge import Database

    db = Database(address="localhost:1729", database="test_update")
    person_manager = Person.manager(db)

    # Create entity with all attributes set - testing type coercion
    alice = Person(name="Alice", age=30, status="active", tags=["python", "typedb"])  # type: ignore[arg-type]

    # The update should read age, status, and tags from alice's current state
    # This doesn't actually execute against DB, just validates the logic
    owned_attrs = Person.get_owned_attributes()
    assert "name" in owned_attrs
    assert "age" in owned_attrs
    assert "status" in owned_attrs
    assert "tags" in owned_attrs


def test_update_extracts_key_attributes():
    """Test that update correctly identifies key attributes."""
    owned_attrs = Person.get_owned_attributes()

    # Verify name is a key attribute
    name_info = owned_attrs["name"]
    assert name_info.flags.is_key is True

    # Verify others are not keys
    age_info = owned_attrs["age"]
    assert age_info.flags.is_key is False

    status_info = owned_attrs["status"]
    assert status_info.flags.is_key is False


def test_update_handles_attribute_values():
    """Test that update correctly extracts values from Attribute instances."""
    # Test value extraction logic
    from type_bridge.attribute import String

    class TestAttr(String):
        pass

    # Create attribute instance
    attr = TestAttr("test_value")
    assert hasattr(attr, "value")
    assert attr.value == "test_value"

    # Test list of attributes
    attrs = [TestAttr("val1"), TestAttr("val2")]
    values = [a.value for a in attrs]
    assert values == ["val1", "val2"]


def test_is_multi_value_attribute_logic():
    """Test the multi-value detection logic."""
    from type_bridge import AttributeFlags, Database

    db = Database(address="localhost:1729", database="test_update")
    person_manager = Person.manager(db)

    # Single-value: card_max == 1
    flags_single = AttributeFlags(card_min=1, card_max=1)
    assert person_manager._is_multi_value_attribute(flags_single) is False

    # Single-value: card_max == 1 (optional)
    flags_optional = AttributeFlags(card_min=0, card_max=1)
    assert person_manager._is_multi_value_attribute(flags_optional) is False

    # Multi-value: card_max is None (unbounded)
    flags_unbounded = AttributeFlags(card_min=0, card_max=None)
    assert person_manager._is_multi_value_attribute(flags_unbounded) is True

    # Multi-value: card_max > 1
    flags_multi = AttributeFlags(card_min=0, card_max=5)
    assert person_manager._is_multi_value_attribute(flags_multi) is True

"""TypeDB attribute types - base classes for defining attributes."""

from abc import ABC
from typing import Any, ClassVar


class Attribute(ABC):
    """Base class for TypeDB attributes.

    Attributes in TypeDB are value types that can be owned by entities and relations.

    Example:
        class Name(String):
            pass

        class Age(Long):
            pass

        class Person(Entity):
            name: Name
            age: Age
    """

    # Class-level metadata
    value_type: ClassVar[str]  # TypeDB value type (string, long, double, boolean, datetime)
    abstract: ClassVar[bool] = False

    # Instance-level configuration (set via __init_subclass__)
    _attr_name: str | None = None
    _is_key: bool = False
    _supertype: str | None = None

    def __init_subclass__(cls, **kwargs):
        """Called when a subclass is created."""
        super().__init_subclass__(**kwargs)

        # Always set the attribute name for each new subclass (don't inherit from parent)
        # This ensures Name(String) gets _attr_name="name", not "string"
        cls._attr_name = cls.__name__.lower()

    @classmethod
    def get_attribute_name(cls) -> str:
        """Get the TypeDB attribute name."""
        return cls._attr_name or cls.__name__.lower()

    @classmethod
    def get_value_type(cls) -> str:
        """Get the TypeDB value type."""
        return cls.value_type

    @classmethod
    def is_key(cls) -> bool:
        """Check if this attribute is a key."""
        return cls._is_key

    @classmethod
    def is_abstract(cls) -> bool:
        """Check if this attribute is abstract."""
        return cls.abstract

    @classmethod
    def get_supertype(cls) -> str | None:
        """Get the supertype if this attribute extends another."""
        return cls._supertype

    @classmethod
    def to_schema_definition(cls) -> str:
        """Generate TypeQL schema definition for this attribute.

        Returns:
            TypeQL schema definition string
        """
        attr_name = cls.get_attribute_name()
        value_type = cls.get_value_type()

        # Check if this is a subtype
        if cls._supertype:
            definition = f"{attr_name} sub {cls._supertype}, value {value_type}"
        else:
            definition = f"{attr_name} sub attribute, value {value_type}"

        if cls.abstract:
            definition += ", abstract"

        return definition + ";"


class String(Attribute):
    """String attribute type.

    Example:
        class Name(String):
            pass

        class Email(String):
            pass
    """

    value_type: ClassVar[str] = "string"


class Long(Attribute):
    """Long integer attribute type.

    Example:
        class Age(Long):
            pass

        class Count(Long):
            pass
    """

    value_type: ClassVar[str] = "long"


class Double(Attribute):
    """Double precision float attribute type.

    Example:
        class Price(Double):
            pass

        class Score(Double):
            pass
    """

    value_type: ClassVar[str] = "double"


class Boolean(Attribute):
    """Boolean attribute type.

    Example:
        class IsActive(Boolean):
            pass

        class IsVerified(Boolean):
            pass
    """

    value_type: ClassVar[str] = "boolean"


class DateTime(Attribute):
    """DateTime attribute type.

    Example:
        class CreatedAt(DateTime):
            pass

        class UpdatedAt(DateTime):
            pass
    """

    value_type: ClassVar[str] = "datetime"


# Helper function to create key attributes
def Key(attribute_class: type[Attribute]) -> type[Attribute]:
    """Mark an attribute as a key attribute.

    Args:
        attribute_class: The attribute class to mark as a key

    Returns:
        The same class with _is_key set to True

    Example:
        class Email(String):
            pass

        EmailKey = Key(Email)

        class User(Entity):
            email: EmailKey
    """
    # Create a new class that inherits from the attribute class
    class KeyAttribute(attribute_class):  # type: ignore
        _is_key = True

    # Preserve the original name
    KeyAttribute.__name__ = attribute_class.__name__
    KeyAttribute.__qualname__ = attribute_class.__qualname__
    KeyAttribute._attr_name = attribute_class._attr_name

    return KeyAttribute

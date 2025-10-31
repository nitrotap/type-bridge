"""Base Attribute class for TypeDB attribute types."""

from abc import ABC, abstractmethod
from typing import Any, ClassVar


class Attribute(ABC):
    """Base class for TypeDB attributes.

    Attributes in TypeDB are value types that can be owned by entities and relations.

    Attribute instances can store values, allowing type-safe construction:
        Name("Alice")  # Creates Name instance with value "Alice"
        Age(30)        # Creates Age instance with value 30

    Example:
        class Name(String):
            pass

        class Age(Integer):
            pass

        class Person(Entity):
            name: Name
            age: Age

        # Both patterns work:
        person1 = Person(name="Alice", age=30)              # Raw values
        person2 = Person(name=Name("Alice"), age=Age(30))   # Attribute instances
    """

    # Class-level metadata
    value_type: ClassVar[str]  # TypeDB value type (string, integer, double, boolean, datetime)
    abstract: ClassVar[bool] = False

    # Instance-level configuration (set via __init_subclass__)
    _attr_name: str | None = None
    _is_key: bool = False
    _supertype: str | None = None

    # Instance-level value storage
    _value: Any = None

    @abstractmethod
    def __init__(self, value: Any = None):
        """Initialize attribute with a value.

        Args:
            value: The value to store in this attribute instance
        """
        self._value = value

    def __init_subclass__(cls, **kwargs):
        """Called when a subclass is created."""
        super().__init_subclass__(**kwargs)

        # Always set the attribute name for each new subclass (don't inherit from parent)
        # This ensures Name(String) gets _attr_name="name", not "string"
        cls._attr_name = cls.__name__.lower()

    @property
    def value(self) -> Any:
        """Get the stored value."""
        return self._value

    def __str__(self) -> str:
        """String representation returns the stored value."""
        return str(self._value) if self._value is not None else ""

    def __repr__(self) -> str:
        """Repr shows the attribute type and value."""
        cls_name = self.__class__.__name__
        return f"{cls_name}({self._value!r})"

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
            definition = f"attribute {attr_name} sub {cls._supertype}, value {value_type}"
        else:
            definition = f"attribute {attr_name}, value {value_type}"

        if cls.abstract:
            definition += ", abstract"

        return definition + ";"

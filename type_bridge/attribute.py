"""TypeDB attribute types - base classes for defining attributes."""

from abc import ABC
from dataclasses import dataclass
from datetime import datetime as datetime_type
from typing import TYPE_CHECKING, Any, ClassVar, Generic, Literal, Protocol, TypeVar, Union, get_args, get_origin
from typing_extensions import Annotated

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema

# TypeVars for proper type checking
# bound= tells type checkers these types accept their base types
StrValue = TypeVar('StrValue', bound=str)
IntValue = TypeVar('IntValue', bound=int)
FloatValue = TypeVar('FloatValue', bound=float)
BoolValue = TypeVar('BoolValue', bound=bool)
DateTimeValue = TypeVar('DateTimeValue', bound=datetime_type)

@dataclass
class EntityFlags:
    """Metadata flags for Entity classes.

    Args:
        type_name: TypeDB type name (defaults to lowercase class name)
        abstract: Whether this is an abstract entity type

    Example:
        class Person(Entity):
            flags = EntityFlags(type_name="person")
            name: Name

        class AbstractPerson(Entity):
            flags = EntityFlags(abstract=True)
            name: Name
    """

    type_name: str | None = None
    abstract: bool = False


@dataclass
class RelationFlags:
    """Metadata flags for Relation classes.

    Args:
        type_name: TypeDB type name (defaults to lowercase class name)
        abstract: Whether this is an abstract relation type

    Example:
        class Employment(Relation):
            flags = RelationFlags(type_name="employment")
            employee: Role = Role("employee", Person)
    """

    type_name: str | None = None
    abstract: bool = False


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


class String(Attribute, Generic[StrValue]):
    """String attribute type that accepts str values.

    Example:
        class Name(String):
            pass

        class Email(String):
            pass

        # With Literal for type safety
        class Status(String):
            pass

        status: Literal["active", "inactive"] | Status
    """

    value_type: ClassVar[str] = "string"

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        """Pydantic validation: accept str values, Literal types, or attribute instances."""
        # Check if source_type is a Literal type
        if get_origin(source_type) is Literal:
            # Extract literal values
            literal_values = get_args(source_type)
            # Convert tuple to list for literal_schema
            return core_schema.union_schema([
                core_schema.literal_schema(list(literal_values)),
                core_schema.is_instance_schema(cls),
            ])

        # Default: accept str or attribute instance
        return core_schema.union_schema([
            core_schema.str_schema(),
            core_schema.is_instance_schema(cls),
        ])




class Long(Attribute, Generic[IntValue]):
    """Long integer attribute type that accepts int values.

    Example:
        class Age(Long):
            pass

        class Count(Long):
            pass

        # With Literal for type safety
        class Priority(Long):
            pass

        priority: Literal[1, 2, 3] | Priority
    """

    value_type: ClassVar[str] = "long"

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        """Pydantic validation: accept int values, Literal types, or attribute instances."""
        # Check if source_type is a Literal type
        if get_origin(source_type) is Literal:
            # Extract literal values
            literal_values = get_args(source_type)
            # Convert tuple to list for literal_schema
            return core_schema.union_schema([
                core_schema.literal_schema(list(literal_values)),
                core_schema.is_instance_schema(cls),
            ])

        # Default: accept int or attribute instance
        return core_schema.union_schema([
            core_schema.int_schema(),
            core_schema.is_instance_schema(cls),
        ])

    @classmethod
    def __class_getitem__(cls, item: Any) -> type["Long"]:
        """Allow generic subscription for type checking (e.g., Long[int])."""
        return cls


class Double(Attribute, Generic[FloatValue]):
    """Double precision float attribute type that accepts float values.

    Example:
        class Price(Double):
            pass

        class Score(Double):
            pass
    """

    value_type: ClassVar[str] = "double"

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        """Pydantic validation: accept float values directly."""
        # Use union schema to accept both float and the attribute type
        return core_schema.union_schema([
            core_schema.float_schema(),
            core_schema.is_instance_schema(cls),
        ])

    @classmethod
    def __class_getitem__(cls, item: Any) -> type["Double"]:
        """Allow generic subscription for type checking (e.g., Double[float])."""
        return cls


class Boolean(Attribute, Generic[BoolValue]):
    """Boolean attribute type that accepts bool values.

    Example:
        class IsActive(Boolean):
            pass

        class IsVerified(Boolean):
            pass
    """

    value_type: ClassVar[str] = "boolean"

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        """Pydantic validation: accept bool values directly."""
        # Use union schema to accept both bool and the attribute type
        return core_schema.union_schema([
            core_schema.bool_schema(),
            core_schema.is_instance_schema(cls),
        ])

    @classmethod
    def __class_getitem__(cls, item: Any) -> type["Boolean"]:
        """Allow generic subscription for type checking (e.g., Boolean[bool])."""
        return cls


class DateTime(Attribute, Generic[DateTimeValue]):
    """DateTime attribute type that accepts datetime values.

    Example:
        class CreatedAt(DateTime):
            pass

        class UpdatedAt(DateTime):
            pass
    """

    value_type: ClassVar[str] = "datetime"

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        """Pydantic validation: accept datetime values directly."""
        from datetime import datetime as dt
        # Use union schema to accept both datetime and the attribute type
        return core_schema.union_schema([
            core_schema.datetime_schema(),
            core_schema.is_instance_schema(cls),
        ])

    @classmethod
    def __class_getitem__(cls, item: Any) -> type["DateTime"]:
        """Allow generic subscription for type checking (e.g., DateTime[datetime])."""
        return cls


@dataclass
class AttributeFlags:
    """Metadata for attribute ownership.

    Represents TypeDB ownership annotations like @key, @card(min, max), @unique.

    Example:
        class Person(Entity):
            name: Name = Flag(Key, Card(1, 1))        # @key @card(1,1)
            nick_name: Name = Flag(Card(0))           # @card(0)
            tags: Tag = Flag(Card(0, 5))              # @card(0,5)
    """

    is_key: bool = False
    is_unique: bool = False
    card_min: int | None = None
    card_max: int | None = None

    def to_typeql_annotations(self) -> list[str]:
        """Convert to TypeQL annotations like @key, @card(0,5).

        Returns:
            List of TypeQL annotation strings
        """
        annotations = []
        if self.is_key:
            annotations.append("@key")
        if self.is_unique:
            annotations.append("@unique")
        if self.card_min is not None or self.card_max is not None:
            min_val = self.card_min if self.card_min is not None else 0
            if self.card_max is not None:
                annotations.append(f"@card({min_val},{self.card_max})")
            else:
                annotations.append(f"@card({min_val})")
        return annotations


class Key:
    """Marker for @key annotation."""

    pass


class Unique:
    """Marker for @unique annotation."""

    pass


class _CardImpl:
    """Internal implementation of Card cardinality."""

    def __init__(self, min_val: int, max_val: int | None):
        self.min = min_val
        self.max = max_val

    def __repr__(self):
        if self.max is None:
            return f"Card(min={self.min})"
        elif self.min == self.max:
            return f"Card({self.min})"
        else:
            return f"Card({self.min}, {self.max})"


def Card(*args, min: int | None = None, max: int | None = None) -> _CardImpl:
    """Cardinality constraint for @card annotation.

    TypeDB Cardinality Rules:
    - Card(1) -> exactly one (1..1)
    - Card(min=0) -> zero or more (0..∞)
    - Card(max=5) -> one to five (1..5)
    - Card(1, 3) -> one to three (1..3)
    - Card(0, 5) -> zero to five (0..5)

    Args:
        *args: Positional arguments (1 arg = exact, 2 args = min/max range)
        min: Minimum cardinality (keyword-only)
        max: Maximum cardinality (keyword-only). None means unbounded

    Examples:
        Card(1)          # @card(1,1) - exactly one
        Card(min=0)      # @card(0) - zero or more (unbounded max)
        Card(max=5)      # @card(1,5) - one to five (min defaults to 1)
        Card(1, 3)       # @card(1,3) - one to three
        Card(0, 5)       # @card(0,5) - zero to five

    Returns:
        _CardImpl instance with resolved min/max values
    """
    # Positional arguments take precedence
    if len(args) == 1:
        # Card(1) -> exactly one
        return _CardImpl(args[0], args[0])
    elif len(args) == 2:
        # Card(1, 3) -> range
        return _CardImpl(args[0], args[1])
    elif len(args) > 2:
        raise ValueError("Card accepts at most 2 positional arguments")

    # Keyword arguments
    if min is not None and max is not None:
        # Card(min=1, max=3)
        return _CardImpl(min, max)
    elif min is not None:
        # Card(min=0) -> unbounded max
        return _CardImpl(min, None)
    elif max is not None:
        # Card(max=5) -> min defaults to 1
        return _CardImpl(1, max)
    else:
        # Card() -> default to 0..∞
        return _CardImpl(0, None)


def Flag(*annotations: type[Key] | type[Unique] | _CardImpl) -> Annotated[Any, AttributeFlags]:
    """Create attribute flags for use as default values.

    Usage: field: Type = Flag(Key, Card(1))

    Args:
        *annotations: Variable number of Key, Unique, or Card objects

    Returns:
        AttributeFlags instance with the specified flags

    Example:
        class Person(Entity):
            flags = EntityFlags(type_name="person")
            name: Name = Flag(Key, Card(1))  # @key @card(1,1)
            age: Age = Flag(Card(0, 1))       # @card(0,1)
            email: Email                       # No special flags
    """
    flags = AttributeFlags()
    for ann in annotations:
        if ann is Key or isinstance(ann, type) and issubclass(ann, Key):
            flags.is_key = True
        elif ann is Unique or isinstance(ann, type) and issubclass(ann, Unique):
            flags.is_unique = True
        elif isinstance(ann, _CardImpl):
            flags.card_min = ann.min
            flags.card_max = ann.max

    return flags

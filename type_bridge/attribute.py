"""TypeDB attribute types - base classes for defining attributes."""

from abc import ABC
from dataclasses import dataclass
from datetime import datetime as datetime_type
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    ClassVar,
    Literal,
    TypeVar,
    get_args,
    get_origin,
)

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema

# TypeVars for proper type checking
# bound= tells type checkers these types accept their base types
StrValue = TypeVar("StrValue", bound=str)
IntValue = TypeVar("IntValue", bound=int)
FloatValue = TypeVar("FloatValue", bound=float)
BoolValue = TypeVar("BoolValue", bound=bool)
DateTimeValue = TypeVar("DateTimeValue", bound=datetime_type)

T = TypeVar("T")

# A fixed size array
type Array[T, int] = Annotated[list[T], int]


MinRange = TypeVar("MinRange", bound=int)
MaxRange = TypeVar("MaxRange", bound=int)

# Cardinality type wrappers
type Min[MinRange, T] = Annotated[T, MinRange, "min"]
type Max[MaxRange, T] = Annotated[T, MaxRange, "max"]
type Range[MinRange, MaxRange, T] = Annotated[T, MinRange, MaxRange, "range"]

# Key marker type
type Key[T] = Annotated[T, "key"]
# Unique marker type
type Unique[T] = Annotated[T, "unique"]


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


class String(Attribute):
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

    def __init__(self, value: str) -> None:
        pass

    value_type: ClassVar[str] = "string"

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: type[StrValue], handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        """Pydantic validation: accept str values, Literal types, or attribute instances."""
        # Check if source_type is a Literal type
        if get_origin(source_type) is Literal:
            # Extract literal values
            literal_values = get_args(source_type)
            # Convert tuple to list for literal_schema
            return core_schema.union_schema(
                [
                    core_schema.literal_schema(list(literal_values)),
                    core_schema.is_instance_schema(cls),
                ]
            )

        # Default: accept str or attribute instance
        return core_schema.union_schema(
            [
                core_schema.str_schema(),
                core_schema.is_instance_schema(cls),
            ]
        )


class Long(Attribute):
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

    def __init__(self, value: int) -> None:
        pass

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: type[IntValue], handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        """Pydantic validation: accept int values, Literal types, or attribute instances."""
        # Check if source_type is a Literal type
        if get_origin(source_type) is Literal:
            # Extract literal values
            literal_values = get_args(source_type)
            # Convert tuple to list for literal_schema
            return core_schema.union_schema(
                [
                    core_schema.literal_schema(list(literal_values)),
                    core_schema.is_instance_schema(cls),
                ]
            )

        # Default: accept int or attribute instance
        return core_schema.union_schema(
            [
                core_schema.int_schema(),
                core_schema.is_instance_schema(cls),
            ]
        )

    @classmethod
    def __class_getitem__(cls, item: object) -> type["Long"]:
        """Allow generic subscription for type checking (e.g., Long[int])."""
        return cls


class Double(Attribute):
    """Double precision float attribute type that accepts float values.

    Example:
        class Price(Double):
            pass

        class Score(Double):
            pass
    """

    value_type: ClassVar[str] = "double"

    def __init__(self, value: float) -> None:
        pass

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: type[FloatValue], handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        """Pydantic validation: accept float values directly."""
        # Use union schema to accept both float and the attribute type
        return core_schema.union_schema(
            [
                core_schema.float_schema(),
                core_schema.is_instance_schema(cls),
            ]
        )

    @classmethod
    def __class_getitem__(cls, item: object) -> type["Double"]:
        """Allow generic subscription for type checking (e.g., Double[float])."""
        return cls


class Boolean(Attribute):
    """Boolean attribute type that accepts bool values.

    Example:
        class IsActive(Boolean):
            pass

        class IsVerified(Boolean):
            pass
    """

    value_type: ClassVar[str] = "boolean"

    def __init__(self, value: bool) -> None:
        pass

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: type[BoolValue], handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        """Pydantic validation: accept bool values directly."""
        # Use union schema to accept both bool and the attribute type
        return core_schema.union_schema(
            [
                core_schema.bool_schema(),
                core_schema.is_instance_schema(cls),
            ]
        )

    @classmethod
    def __class_getitem__(cls, item: object) -> type["Boolean"]:
        """Allow generic subscription for type checking (e.g., Boolean[bool])."""
        return cls


class DateTime(Attribute):
    """DateTime attribute type that accepts datetime values.

    Example:
        class CreatedAt(DateTime):
            pass

        class UpdatedAt(DateTime):
            pass
    """

    def __init__(self, value: datetime_type) -> None:
        pass

    value_type: ClassVar[str] = "datetime"

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: type[DateTimeValue], handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        """Pydantic validation: accept datetime values directly."""
        # Use union schema to accept both datetime and the attribute type
        return core_schema.union_schema(
            [
                core_schema.datetime_schema(),
                core_schema.is_instance_schema(cls),
            ]
        )

    @classmethod
    def __class_getitem__(cls, item: object) -> type["DateTime"]:
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



def Flag(*annotations: Key | Unique ) -> Annotated[Any, AttributeFlags]:
    """Create attribute flags for Key and Unique markers.

    Usage: field: Type = Flag(Key), field: Type = Flag(Unique), field: Type = Flag(Key, Unique)

    For cardinality, use generic type wrappers instead:
    - Optional[Type] for @card(0,1)
    - Min[N, Type] for @card(N)
    - Max[N, Type] for @card(0,N)
    - Range[Min, Max, Type] for @card(Min,Max)

    Args:
        *annotations: Variable number of Key or Unique marker types

    Returns:
        AttributeFlags instance with the specified flags

    Example:
        class Person(Entity):
            flags = EntityFlags(type_name="person")
            name: Name = Flag(Key)            # @key
            email: Email = Flag(Key, Unique)  # @key @unique
            nick_name: Optional[Name]         # @card(0,1)
            tags: Min[10, Tag]                # @card(10)
    """
    flags = AttributeFlags()
    for ann in annotations:
        if ann is Key:
            flags.is_key = True
        elif ann is Unique:
            flags.is_unique = True

    return flags

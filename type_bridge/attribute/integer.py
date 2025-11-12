"""Integer attribute type for TypeDB."""

from typing import Any, ClassVar, Literal, TypeVar, get_origin

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema

from type_bridge.attribute.base import Attribute

# TypeVar for proper type checking
IntValue = TypeVar("IntValue", bound=int)


class Integer(Attribute):
    """Integer attribute type that accepts int values.

    Example:
        class Age(Integer):
            pass

        class Count(Integer):
            pass

        # With Literal for type safety
        class Priority(Integer):
            pass

        priority: Literal[1, 2, 3] | Priority
    """

    value_type: ClassVar[str] = "integer"

    def __init__(self, value: int):
        """Initialize Integer attribute with an integer value.

        Args:
            value: The integer value to store
        """
        super().__init__(value)

    @property
    def value(self) -> int:
        """Get the stored integer value."""
        return self._value if self._value is not None else 0

    def __int__(self) -> int:
        """Convert to int."""
        return int(self.value)

    def __add__(self, other: object) -> "Integer":
        """Add two integers."""
        if isinstance(other, int):
            return Integer(self.value + other)
        elif isinstance(other, Integer):
            return Integer(self.value + other.value)
        else:
            return NotImplemented

    def __radd__(self, other: object) -> "Integer":
        """Right-hand add (for when left operand doesn't support addition)."""
        if isinstance(other, int):
            return Integer(other + self.value)
        else:
            return NotImplemented

    def __sub__(self, other: object) -> "Integer":
        """Subtract two integers."""
        if isinstance(other, int):
            return Integer(self.value - other)
        elif isinstance(other, Integer):
            return Integer(self.value - other.value)
        else:
            return NotImplemented

    def __rsub__(self, other: object) -> "Integer":
        """Right-hand subtract."""
        if isinstance(other, int):
            return Integer(other - self.value)
        else:
            return NotImplemented

    def __mul__(self, other: object) -> "Integer":
        """Multiply two integers."""
        if isinstance(other, int):
            return Integer(self.value * other)
        elif isinstance(other, Integer):
            return Integer(self.value * other.value)
        else:
            return NotImplemented

    def __rmul__(self, other: object) -> "Integer":
        """Right-hand multiply."""
        if isinstance(other, int):
            return Integer(other * self.value)
        else:
            return NotImplemented

    def __floordiv__(self, other: object) -> "Integer":
        """Floor division."""
        if isinstance(other, int):
            return Integer(self.value // other)
        elif isinstance(other, Integer):
            return Integer(self.value // other.value)
        else:
            return NotImplemented

    def __rfloordiv__(self, other: object) -> "Integer":
        """Right-hand floor division."""
        if isinstance(other, int):
            return Integer(other // self.value)
        else:
            return NotImplemented

    def __mod__(self, other: object) -> "Integer":
        """Modulo operation."""
        if isinstance(other, int):
            return Integer(self.value % other)
        elif isinstance(other, Integer):
            return Integer(self.value % other.value)
        else:
            return NotImplemented

    def __rmod__(self, other: object) -> "Integer":
        """Right-hand modulo."""
        if isinstance(other, int):
            return Integer(other % self.value)
        else:
            return NotImplemented

    def __pow__(self, other: object) -> "Integer":
        """Power operation."""
        if isinstance(other, int):
            return Integer(self.value**other)
        elif isinstance(other, Integer):
            return Integer(self.value**other.value)
        else:
            return NotImplemented

    def __rpow__(self, other: object) -> "Integer":
        """Right-hand power."""
        if isinstance(other, int):
            return Integer(other**self.value)
        else:
            return NotImplemented

    def __neg__(self) -> "Integer":
        """Negate the integer."""
        return Integer(-self.value)

    def __pos__(self) -> "Integer":
        """Positive (unary +)."""
        return Integer(+self.value)

    def __abs__(self) -> "Integer":
        """Absolute value."""
        return Integer(abs(self.value))

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: type[IntValue], handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        """Pydantic validation: accept int values, Literal types, or attribute instances."""

        # Serializer to extract value from attribute instances
        def serialize_long(value: Any) -> int:
            if isinstance(value, cls):
                return int(value._value) if value._value is not None else 0
            return int(value)

        # Check if source_type is a Literal type
        if get_origin(source_type) is Literal:
            # Convert tuple to list for literal_schema
            return core_schema.with_info_plain_validator_function(
                lambda v, _: v._value if isinstance(v, cls) else v,
                serialization=core_schema.plain_serializer_function_ser_schema(
                    serialize_long,
                    return_schema=core_schema.int_schema(),
                ),
            )

        # Default: accept int or attribute instance, always return attribute instance
        def validate_long(value: Any) -> "Integer":
            if isinstance(value, cls):
                return value  # Return attribute instance as-is
            return cls(int(value))  # Wrap raw int in attribute instance

        return core_schema.with_info_plain_validator_function(
            lambda v, _: validate_long(v),
            serialization=core_schema.plain_serializer_function_ser_schema(
                serialize_long,
                return_schema=core_schema.int_schema(),
            ),
        )

    @classmethod
    def __class_getitem__(cls, item: object) -> type["Integer"]:
        """Allow generic subscription for type checking (e.g., Integer[int])."""
        return cls

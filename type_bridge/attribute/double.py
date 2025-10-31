"""Double attribute type for TypeDB."""

from typing import Any, ClassVar, TypeVar

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema

from type_bridge.attribute.base import Attribute

# TypeVar for proper type checking
FloatValue = TypeVar("FloatValue", bound=float)


class Double(Attribute):
    """Double precision float attribute type that accepts float values.

    Example:
        class Price(Double):
            pass

        class Score(Double):
            pass
    """

    value_type: ClassVar[str] = "double"

    def __init__(self, value: float):
        """Initialize Double attribute with a float value.

        Args:
            value: The float value to store
        """
        super().__init__(value)

    @property
    def value(self) -> float:
        """Get the stored float value."""
        return self._value if self._value is not None else 0.0

    def __float__(self) -> float:
        """Convert to float."""
        return float(self.value)

    def __add__(self, other: object) -> "Double":
        """Add two floats."""
        if isinstance(other, (int, float)):
            return Double(self.value + other)
        elif isinstance(other, Double):
            return Double(self.value + other.value)
        else:
            return NotImplemented

    def __radd__(self, other: object) -> "Double":
        """Right-hand add."""
        if isinstance(other, (int, float)):
            return Double(other + self.value)
        else:
            return NotImplemented

    def __sub__(self, other: object) -> "Double":
        """Subtract two floats."""
        if isinstance(other, (int, float)):
            return Double(self.value - other)
        elif isinstance(other, Double):
            return Double(self.value - other.value)
        else:
            return NotImplemented

    def __rsub__(self, other: object) -> "Double":
        """Right-hand subtract."""
        if isinstance(other, (int, float)):
            return Double(other - self.value)
        else:
            return NotImplemented

    def __mul__(self, other: object) -> "Double":
        """Multiply two floats."""
        if isinstance(other, (int, float)):
            return Double(self.value * other)
        elif isinstance(other, Double):
            return Double(self.value * other.value)
        else:
            return NotImplemented

    def __rmul__(self, other: object) -> "Double":
        """Right-hand multiply."""
        if isinstance(other, (int, float)):
            return Double(other * self.value)
        else:
            return NotImplemented

    def __truediv__(self, other: object) -> "Double":
        """True division."""
        if isinstance(other, (int, float)):
            return Double(self.value / other)
        elif isinstance(other, Double):
            return Double(self.value / other.value)
        else:
            return NotImplemented

    def __rtruediv__(self, other: object) -> "Double":
        """Right-hand true division."""
        if isinstance(other, (int, float)):
            return Double(other / self.value)
        else:
            return NotImplemented

    def __floordiv__(self, other: object) -> "Double":
        """Floor division."""
        if isinstance(other, (int, float)):
            return Double(self.value // other)
        elif isinstance(other, Double):
            return Double(self.value // other.value)
        else:
            return NotImplemented

    def __rfloordiv__(self, other: object) -> "Double":
        """Right-hand floor division."""
        if isinstance(other, (int, float)):
            return Double(other // self.value)
        else:
            return NotImplemented

    def __mod__(self, other: object) -> "Double":
        """Modulo operation."""
        if isinstance(other, (int, float)):
            return Double(self.value % other)
        elif isinstance(other, Double):
            return Double(self.value % other.value)
        else:
            return NotImplemented

    def __rmod__(self, other: object) -> "Double":
        """Right-hand modulo."""
        if isinstance(other, (int, float)):
            return Double(other % self.value)
        else:
            return NotImplemented

    def __pow__(self, other: object) -> "Double":
        """Power operation."""
        if isinstance(other, (int, float)):
            return Double(self.value ** other)
        elif isinstance(other, Double):
            return Double(self.value ** other.value)
        else:
            return NotImplemented

    def __rpow__(self, other: object) -> "Double":
        """Right-hand power."""
        if isinstance(other, (int, float)):
            return Double(other ** self.value)
        else:
            return NotImplemented

    def __neg__(self) -> "Double":
        """Negate the float."""
        return Double(-self.value)

    def __pos__(self) -> "Double":
        """Positive (unary +)."""
        return Double(+self.value)

    def __abs__(self) -> "Double":
        """Absolute value."""
        return Double(abs(self.value))

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: type[FloatValue], handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        """Pydantic validation: accept float values or attribute instances."""

        # Serializer to extract value from attribute instances
        def serialize_double(value: Any) -> float:
            if isinstance(value, cls):
                return float(value._value) if value._value is not None else 0.0
            return float(value)

        # Validator: accept float or attribute instance, serialize to float
        def validate_double(value: Any) -> float:
            if isinstance(value, cls):
                return value._value if value._value is not None else 0.0
            return float(value)

        return core_schema.with_info_plain_validator_function(
            lambda v, _: validate_double(v),
            serialization=core_schema.plain_serializer_function_ser_schema(
                serialize_double,
                return_schema=core_schema.float_schema(),
            ),
        )

    @classmethod
    def __class_getitem__(cls, item: object) -> type["Double"]:
        """Allow generic subscription for type checking (e.g., Double[float])."""
        return cls

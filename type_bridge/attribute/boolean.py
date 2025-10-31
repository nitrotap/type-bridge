"""Boolean attribute type for TypeDB."""

from typing import Any, ClassVar, TypeVar

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema

from type_bridge.attribute.base import Attribute

# TypeVar for proper type checking
BoolValue = TypeVar("BoolValue", bound=bool)


class Boolean(Attribute):
    """Boolean attribute type that accepts bool values.

    Example:
        class IsActive(Boolean):
            pass

        class IsVerified(Boolean):
            pass
    """

    value_type: ClassVar[str] = "boolean"

    def __init__(self, value: bool):
        """Initialize Boolean attribute with a bool value.

        Args:
            value: The boolean value to store
        """
        super().__init__(value)

    @property
    def value(self) -> bool:
        """Get the stored boolean value."""
        return self._value if self._value is not None else False

    def __bool__(self) -> bool:
        """Convert to bool."""
        return bool(self.value)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: type[BoolValue], handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        """Pydantic validation: accept bool values or attribute instances."""

        # Serializer to extract value from attribute instances
        def serialize_boolean(value: Any) -> bool:
            if isinstance(value, cls):
                return bool(value._value) if value._value is not None else False
            return bool(value)

        # Validator: accept bool or attribute instance, serialize to bool
        def validate_boolean(value: Any) -> bool:
            if isinstance(value, cls):
                return value._value if value._value is not None else False
            return bool(value)

        return core_schema.with_info_plain_validator_function(
            lambda v, _: validate_boolean(v),
            serialization=core_schema.plain_serializer_function_ser_schema(
                serialize_boolean,
                return_schema=core_schema.bool_schema(),
            ),
        )

    @classmethod
    def __class_getitem__(cls, item: object) -> type["Boolean"]:
        """Allow generic subscription for type checking (e.g., Boolean[bool])."""
        return cls

"""DateTime attribute type for TypeDB."""

from datetime import datetime as datetime_type
from typing import Any, ClassVar, TypeVar

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema

from type_bridge.attribute.base import Attribute

# TypeVar for proper type checking
DateTimeValue = TypeVar("DateTimeValue", bound=datetime_type)


class DateTime(Attribute):
    """DateTime attribute type that accepts datetime values.

    Example:
        class CreatedAt(DateTime):
            pass

        class UpdatedAt(DateTime):
            pass
    """

    value_type: ClassVar[str] = "datetime"

    def __init__(self, value: datetime_type):
        """Initialize DateTime attribute with a datetime value.

        Args:
            value: The datetime value to store
        """
        super().__init__(value)

    @property
    def value(self) -> datetime_type:
        """Get the stored datetime value."""
        return self._value if self._value is not None else datetime_type.now()

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: type[DateTimeValue], handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        """Pydantic validation: accept datetime values or attribute instances."""

        # Serializer to extract value from attribute instances
        def serialize_datetime(value: Any) -> datetime_type:
            if isinstance(value, cls):
                return value._value if value._value is not None else datetime_type.now()
            return (
                value
                if isinstance(value, datetime_type)
                else datetime_type.fromisoformat(str(value))
            )

        # Validator: accept datetime or attribute instance
        def validate_datetime(value: Any) -> datetime_type:
            if isinstance(value, cls):
                return value._value if value._value is not None else datetime_type.now()
            return (
                value
                if isinstance(value, datetime_type)
                else datetime_type.fromisoformat(str(value))
            )

        return core_schema.with_info_plain_validator_function(
            lambda v, _: validate_datetime(v),
            serialization=core_schema.plain_serializer_function_ser_schema(
                serialize_datetime,
                return_schema=core_schema.datetime_schema(),
            ),
        )

    @classmethod
    def __class_getitem__(cls, item: object) -> type["DateTime"]:
        """Allow generic subscription for type checking (e.g., DateTime[datetime])."""
        return cls

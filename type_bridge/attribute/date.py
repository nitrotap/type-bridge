"""Date attribute type for TypeDB."""

from datetime import date as date_type
from datetime import datetime as datetime_type
from typing import Any, ClassVar, TypeVar

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema

from type_bridge.attribute.base import Attribute

# TypeVar for proper type checking
DateValue = TypeVar("DateValue", bound=date_type)


class Date(Attribute):
    """Date attribute type that accepts date values (date only, no time).

    This maps to TypeDB's 'date' type, which is an ISO 8601 compliant date
    without time information.

    Range: January 1, 262144 BCE to December 31, 262142 CE

    Example:
        from datetime import date

        class PublishDate(Date):
            pass

        class BirthDate(Date):
            pass

        # Usage with date values
        published = PublishDate(date(2024, 3, 30))
        birthday = BirthDate(date(1990, 5, 15))
    """

    value_type: ClassVar[str] = "date"

    def __init__(self, value: date_type | str):
        """Initialize Date attribute with a date value.

        Args:
            value: The date value to store. Can be:
                - datetime.date instance
                - str in ISO 8601 format (YYYY-MM-DD)

        Example:
            from datetime import date

            # From date instance
            publish_date = PublishDate(date(2024, 3, 30))

            # From ISO string
            publish_date = PublishDate("2024-03-30")
        """
        if isinstance(value, str):
            value = date_type.fromisoformat(value)
        elif isinstance(value, datetime_type):
            # If passed a datetime, extract just the date part
            value = value.date()
        super().__init__(value)

    @property
    def value(self) -> date_type:
        """Get the stored date value."""
        return self._value if self._value is not None else date_type.today()

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: type[DateValue], handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        """Pydantic validation: accept date values or attribute instances."""

        # Serializer to extract value from attribute instances
        def serialize_date(value: Any) -> date_type:
            if isinstance(value, cls):
                return value._value if value._value is not None else date_type.today()
            if isinstance(value, date_type):
                return value
            if isinstance(value, datetime_type):
                return value.date()
            # Try to parse ISO string
            return date_type.fromisoformat(str(value))

        # Validator: accept date or attribute instance, always return attribute instance
        def validate_date(value: Any) -> "Date":
            if isinstance(value, cls):
                return value  # Return attribute instance as-is
            # Wrap date value in attribute instance
            if isinstance(value, date_type):
                return cls(value)
            if isinstance(value, datetime_type):
                return cls(value.date())
            # Try to parse ISO string
            return cls(date_type.fromisoformat(str(value)))

        return core_schema.with_info_plain_validator_function(
            lambda v, _: validate_date(v),
            serialization=core_schema.plain_serializer_function_ser_schema(
                serialize_date,
                return_schema=core_schema.date_schema(),
            ),
        )

    @classmethod
    def __class_getitem__(cls, item: object) -> type["Date"]:
        """Allow generic subscription for type checking (e.g., Date[date])."""
        return cls

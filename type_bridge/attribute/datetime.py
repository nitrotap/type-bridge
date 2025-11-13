"""DateTime attribute type for TypeDB."""

from datetime import datetime as datetime_type
from datetime import timezone as timezone_type
from typing import TYPE_CHECKING, Any, ClassVar, TypeVar

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema

from type_bridge.attribute.base import Attribute

if TYPE_CHECKING:
    from type_bridge.attribute.datetimetz import DateTimeTZ

# TypeVar for proper type checking
DateTimeValue = TypeVar("DateTimeValue", bound=datetime_type)


class DateTime(Attribute):
    """DateTime attribute type that accepts naive datetime values.

    This maps to TypeDB's 'datetime' type, which does not include timezone information.

    Example:
        class CreatedAt(DateTime):
            pass

        # Usage with naive datetime
        event = Event(created_at=CreatedAt(datetime(2024, 1, 15, 10, 30, 45)))

        # Convert to DateTimeTZ
        aware_dt = created_at.add_timezone()  # Implicit: add system timezone
        aware_dt_utc = created_at.add_timezone(timezone.utc)  # Explicit: add UTC
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

    def add_timezone(self, tz: timezone_type | None = None) -> "DateTimeTZ":
        """Convert DateTime to DateTimeTZ by adding timezone information.

        Implicit conversion (tz=None): Add system/local timezone
        Explicit conversion (tz provided): Add specified timezone

        Args:
            tz: Optional timezone to add to the naive datetime.
                If None, uses system local timezone (astimezone()).
                If provided, uses that specific timezone.

        Returns:
            DateTimeTZ instance with timezone-aware datetime

        Example:
            # Implicit: add system timezone
            aware = naive_dt.add_timezone()

            # Explicit: add UTC timezone
            from datetime import timezone
            aware_utc = naive_dt.add_timezone(timezone.utc)

            # Explicit: add JST (+9) timezone
            from datetime import timezone, timedelta
            jst = timezone(timedelta(hours=9))
            aware_jst = naive_dt.add_timezone(jst)
        """
        from type_bridge.attribute.datetimetz import DateTimeTZ

        dt_value = self.value
        if tz is None:
            # Implicit: add system timezone
            aware_dt = dt_value.astimezone()
        else:
            # Explicit: add specified timezone
            aware_dt = dt_value.replace(tzinfo=tz)

        return DateTimeTZ(aware_dt)

    def __add__(self, other: Any) -> "DateTime":
        """Add a Duration to this DateTime.

        Args:
            other: A Duration to add to this datetime

        Returns:
            New DateTime with the duration added

        Example:
            from type_bridge import Duration
            dt = DateTime(datetime(2024, 1, 31, 14, 0, 0))
            duration = Duration("P1M")
            result = dt + duration  # DateTime(2024-02-28 14:00:00)
        """
        from type_bridge.attribute.duration import Duration

        if isinstance(other, Duration):
            # Add duration to datetime
            # Use isodate's add_duration which handles month/day arithmetic

            new_dt = self.value + other.value
            return DateTime(new_dt)
        return NotImplemented

    def __radd__(self, other: Any) -> "DateTime":
        """Reverse addition for Duration + DateTime."""
        return self.__add__(other)

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

        # Validator: accept datetime or attribute instance, always return attribute instance
        def validate_datetime(value: Any) -> "DateTime":
            if isinstance(value, cls):
                return value  # Return attribute instance as-is
            # Wrap raw datetime in attribute instance
            if isinstance(value, datetime_type):
                return cls(value)
            return cls(datetime_type.fromisoformat(str(value)))

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

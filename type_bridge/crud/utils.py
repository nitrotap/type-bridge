"""Shared utilities for CRUD operations."""

from datetime import date, datetime, timedelta
from decimal import Decimal as DecimalType
from typing import Any

import isodate
from isodate import Duration as IsodateDuration

from type_bridge.attribute import AttributeFlags


def format_value(value: Any) -> str:
    """Format a Python value for TypeQL.

    Handles extraction from Attribute instances and converts Python types
    to their TypeQL literal representation.

    Args:
        value: Python value to format (may be wrapped in Attribute instance)

    Returns:
        TypeQL-formatted string literal

    Examples:
        >>> format_value("hello")
        '"hello"'
        >>> format_value(42)
        '42'
        >>> format_value(True)
        'true'
        >>> format_value(Decimal("123.45"))
        '123.45dec'
    """
    # Extract value from Attribute instances first
    if hasattr(value, "value"):
        value = value.value

    if isinstance(value, str):
        # Escape backslashes first, then double quotes for TypeQL string literals
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    elif isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, DecimalType):
        # TypeDB decimal literals use 'dec' suffix
        return f"{value}dec"
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, datetime):
        # TypeDB datetime/datetimetz literals are unquoted ISO 8601 strings
        return value.isoformat()
    elif isinstance(value, date):
        # TypeDB date literals are unquoted ISO 8601 date strings
        return value.isoformat()
    elif isinstance(value, (IsodateDuration, timedelta)):
        # TypeDB duration literals are unquoted ISO 8601 duration strings
        return isodate.duration_isoformat(value)
    else:
        # For other types, convert to string and escape
        str_value = str(value)
        escaped = str_value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'


def is_multi_value_attribute(flags: AttributeFlags) -> bool:
    """Check if attribute is multi-value based on cardinality.

    Multi-value attributes have either:
    - Unbounded cardinality (card_max is None)
    - Maximum cardinality > 1

    Single-value attributes have:
    - Maximum cardinality == 1 (including 0..1 and 1..1)

    Args:
        flags: AttributeFlags instance containing cardinality information

    Returns:
        True if multi-value (card_max is None or > 1), False if single-value

    Examples:
        >>> flags = AttributeFlags(card_min=0, card_max=1)
        >>> is_multi_value_attribute(flags)
        False
        >>> flags = AttributeFlags(card_min=0, card_max=5)
        >>> is_multi_value_attribute(flags)
        True
        >>> flags = AttributeFlags(card_min=2, card_max=None)
        >>> is_multi_value_attribute(flags)
        True
    """
    # Single-value: card_max == 1 (including 0..1 and 1..1)
    # Multi-value: card_max is None (unbounded) or > 1
    if flags.card_max is None:
        # Unbounded means multi-value
        return True
    return flags.card_max > 1

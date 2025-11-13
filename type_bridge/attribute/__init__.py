"""TypeDB attribute types - base classes and concrete implementations.

This package provides the attribute type system for TypeBridge, including:
- Base Attribute ABC
- Concrete attribute types (String, Integer, Double, Boolean, Date, DateTime, DateTimeTZ, Decimal)
- Flag system for annotations (Key, Unique, Card)
"""

from type_bridge.attribute.base import Attribute
from type_bridge.attribute.boolean import Boolean
from type_bridge.attribute.date import Date
from type_bridge.attribute.datetime import DateTime
from type_bridge.attribute.datetimetz import DateTimeTZ
from type_bridge.attribute.decimal import Decimal
from type_bridge.attribute.double import Double
from type_bridge.attribute.flags import (
    AttributeFlags,
    Card,
    EntityFlags,
    Flag,
    Key,
    RelationFlags,
    TypeFlags,
    TypeNameCase,
    Unique,
)
from type_bridge.attribute.integer import Integer
from type_bridge.attribute.string import String

__all__ = [
    # Base class
    "Attribute",
    # Concrete types
    "String",
    "Integer",
    "Double",
    "Boolean",
    "Date",
    "DateTime",
    "DateTimeTZ",
    "Decimal",
    # Flag system
    "Flag",
    "Key",
    "Unique",
    "Card",
    "AttributeFlags",
    "TypeFlags",
    "EntityFlags",  # Backward compatibility
    "RelationFlags",  # Backward compatibility
    "TypeNameCase",
]

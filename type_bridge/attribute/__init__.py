"""TypeDB attribute types - base classes and concrete implementations.

This package provides the attribute type system for TypeBridge, including:
- Base Attribute ABC
- Concrete attribute types (String, Integer, Double, Boolean, DateTime)
- Flag system for annotations (Key, Unique, Card)
"""

from type_bridge.attribute.base import Attribute
from type_bridge.attribute.boolean import Boolean
from type_bridge.attribute.datetime import DateTime
from type_bridge.attribute.double import Double
from type_bridge.attribute.flags import (
    AttributeFlags,
    Card,
    EntityFlags,
    Flag,
    Key,
    RelationFlags,
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
    "DateTime",
    # Flag system
    "Flag",
    "Key",
    "Unique",
    "Card",
    "AttributeFlags",
    "EntityFlags",
    "RelationFlags",
]

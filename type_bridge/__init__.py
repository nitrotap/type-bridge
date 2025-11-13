"""TypeBridge - A Python ORM for TypeDB with Attribute-based API."""

from type_bridge.attribute import (
    Attribute,
    AttributeFlags,
    Boolean,
    Card,
    Date,
    DateTime,
    DateTimeTZ,
    Decimal,
    Double,
    EntityFlags,
    Flag,
    Integer,
    Key,
    RelationFlags,
    String,
    TypeFlags,
    TypeNameCase,
    Unique,
)
from type_bridge.crud import EntityManager, RelationManager
from type_bridge.models import Entity, Relation, Role, TypeDBType
from type_bridge.query import Query, QueryBuilder
from type_bridge.schema import MigrationManager, SchemaManager
from type_bridge.session import Database

__version__ = "0.1.0"

__all__ = [
    # Database and session
    "Database",
    # Models
    "TypeDBType",
    "Entity",
    "Relation",
    "Role",
    # Attributes
    "Attribute",
    "String",
    "Integer",
    "Double",
    "Boolean",
    "Date",
    "DateTime",
    "DateTimeTZ",
    "Decimal",
    # Attribute annotations
    "AttributeFlags",
    "Flag",
    "Key",
    "Unique",
    # Cardinality types
    "Card",
    # Entity/Relation flags
    "TypeFlags",
    "EntityFlags",  # Backward compatibility
    "RelationFlags",  # Backward compatibility
    "TypeNameCase",
    # Query
    "Query",
    "QueryBuilder",
    # CRUD
    "EntityManager",
    "RelationManager",
    # Schema
    "SchemaManager",
    "MigrationManager",
]

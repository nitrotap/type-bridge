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
    Duration,
    Flag,
    Integer,
    Key,
    String,
    TypeFlags,
    TypeNameCase,
    Unique,
)
from type_bridge.crud import (
    EntityManager,
    EntityNotFoundError,
    KeyAttributeError,
    NotUniqueError,
    RelationManager,
    RelationNotFoundError,
)
from type_bridge.models import Entity, Relation, Role, TypeDBType
from type_bridge.query import Query, QueryBuilder
from type_bridge.schema import MigrationManager, SchemaManager
from type_bridge.session import Connection, Database, TransactionContext
from type_bridge.typedb_driver import Credentials, TransactionType, TypeDB

__version__ = "0.9.3"

__all__ = [
    # Database and session
    "Connection",
    "Database",
    "TransactionContext",
    # TypeDB driver (re-exported for convenience)
    "Credentials",
    "TransactionType",
    "TypeDB",
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
    "Duration",
    # Attribute annotations
    "AttributeFlags",
    "Flag",
    "Key",
    "Unique",
    # Cardinality types
    "Card",
    # Entity/Relation flags
    "TypeFlags",
    "TypeNameCase",
    # Query
    "Query",
    "QueryBuilder",
    # CRUD
    "EntityManager",
    "RelationManager",
    # CRUD Exceptions
    "EntityNotFoundError",
    "RelationNotFoundError",
    "NotUniqueError",
    "KeyAttributeError",
    # Schema
    "SchemaManager",
    "MigrationManager",
]

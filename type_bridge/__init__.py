"""TypeBridge - A Python ORM for TypeDB with Attribute-based API."""

from type_bridge.attribute import Attribute, Boolean, DateTime, Double, Key, Long, String
from type_bridge.crud import EntityManager, RelationManager
from type_bridge.models import Entity, Relation, Role
from type_bridge.query import Query, QueryBuilder
from type_bridge.schema import MigrationManager, SchemaManager
from type_bridge.session import Database

__version__ = "0.1.0"

__all__ = [
    # Database and session
    "Database",
    # Models
    "Entity",
    "Relation",
    "Role",
    # Attributes
    "Attribute",
    "String",
    "Long",
    "Double",
    "Boolean",
    "DateTime",
    "Key",
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

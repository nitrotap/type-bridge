"""CRUD operations for TypeDB entities and relations.

This module provides managers and query builders for performing
CRUD (Create, Read, Update, Delete) operations on TypeDB entities
and relations with type safety.

The module is organized into submodules:
- entity: Entity-related CRUD operations
- relation: Relation-related CRUD operations
- utils: Shared utilities
- base: Base type definitions
"""

# Re-export for backward compatibility
from .entity import EntityManager, EntityQuery, GroupByQuery
from .relation import RelationGroupByQuery, RelationManager, RelationQuery

__all__ = [
    # Entity operations
    "EntityManager",
    "EntityQuery",
    "GroupByQuery",
    # Relation operations
    "RelationManager",
    "RelationQuery",
    "RelationGroupByQuery",
]

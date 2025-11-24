"""Relation CRUD operations module.

This module provides type-safe CRUD operations for TypeDB relations,
including:
- RelationManager: Main interface for relation CRUD operations
- RelationQuery: Chainable query builder for filtering and aggregations
- RelationGroupByQuery: Grouped aggregations on relations
"""

from .group_by import RelationGroupByQuery
from .manager import RelationManager
from .query import RelationQuery

__all__ = [
    "RelationManager",
    "RelationQuery",
    "RelationGroupByQuery",
]

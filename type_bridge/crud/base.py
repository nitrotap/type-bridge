"""Base types and type variables for CRUD operations."""

from typing import TypeVar

from type_bridge.models import Entity, Relation

# Type variables bound to Entity and Relation
E = TypeVar("E", bound=Entity)
R = TypeVar("R", bound=Relation)

"""
Type-safe query expression system for TypeBridge.

This module provides expression classes for building type-safe TypeQL queries.
"""

from type_bridge.expressions.aggregate import AggregateExpr
from type_bridge.expressions.base import Expression
from type_bridge.expressions.boolean import BooleanExpr
from type_bridge.expressions.comparison import AttributeExistsExpr, ComparisonExpr
from type_bridge.expressions.functions import (
    FunctionCall,
    FunctionCallExpr,
    FunctionQuery,
    ReturnType,
)
from type_bridge.expressions.role_player import RolePlayerExpr
from type_bridge.expressions.string import StringExpr

__all__ = [
    "Expression",
    "ComparisonExpr",
    "AttributeExistsExpr",
    "StringExpr",
    "BooleanExpr",
    "AggregateExpr",
    "FunctionCallExpr",
    "FunctionCall",
    "FunctionQuery",
    "ReturnType",
    "RolePlayerExpr",
]

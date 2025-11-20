"""Base expression class for TypeQL query building."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from type_bridge.attribute.base import Attribute
    from type_bridge.expressions.boolean import BooleanExpr


class Expression(ABC):
    """
    Base class for all query expressions.

    Expressions represent query constraints that can be composed using
    boolean operators and converted to TypeQL patterns.
    """

    @abstractmethod
    def to_typeql(self, var: str) -> str:
        """
        Convert this expression to a TypeQL pattern.

        Args:
            var: The variable name to use in the pattern (e.g., "$e")

        Returns:
            TypeQL pattern string
        """
        ...

    def get_attribute_types(self) -> set[type["Attribute"]]:
        """
        Get all attribute types referenced by this expression.

        Returns:
            Set of attribute types used in this expression

        Note:
            Default implementation returns attr_type if present.
            BooleanExpr overrides to recursively collect from operands.
        """
        # Check if this expression has attr_type attribute
        attr_type = getattr(self, "attr_type", None)
        if attr_type is not None:
            return {attr_type}
        return set()

    def and_(self, other: "Expression") -> "BooleanExpr":
        """
        Combine this expression with another using AND logic.

        Args:
            other: Another expression to AND with this one

        Returns:
            BooleanExpr representing the conjunction
        """
        from type_bridge.expressions.boolean import BooleanExpr

        return BooleanExpr(operation="and", operands=[self, other])

    def or_(self, other: "Expression") -> "BooleanExpr":
        """
        Combine this expression with another using OR logic.

        Args:
            other: Another expression to OR with this one

        Returns:
            BooleanExpr representing the disjunction
        """
        from type_bridge.expressions.boolean import BooleanExpr

        return BooleanExpr(operation="or", operands=[self, other])

    def not_(self) -> "BooleanExpr":
        """
        Negate this expression using NOT logic.

        Returns:
            BooleanExpr representing the negation
        """
        from type_bridge.expressions.boolean import BooleanExpr

        return BooleanExpr(operation="not", operands=[self])

"""Comparison expressions for value-based filtering."""

from typing import TYPE_CHECKING, Literal

from type_bridge.expressions.base import Expression

if TYPE_CHECKING:
    from type_bridge.attribute.base import Attribute


class ComparisonExpr[T: "Attribute"](Expression):
    """
    Type-safe comparison expression for filtering by attribute values.

    Represents comparisons like age > 30, score <= 100, etc.
    """

    def __init__(
        self,
        attr_type: type[T],
        operator: Literal[">", "<", ">=", "<=", "==", "!="],
        value: T,
    ):
        """
        Create a comparison expression.

        Args:
            attr_type: Attribute type to filter on
            operator: Comparison operator
            value: Value to compare against
        """
        self.attr_type = attr_type
        self.operator = operator
        self.value = value

    def to_typeql(self, var: str) -> str:
        """
        Generate TypeQL pattern for this comparison.

        Example output: "$e has Age $age; $age > 30"

        Args:
            var: Entity variable name

        Returns:
            TypeQL pattern string (without trailing semicolon)
        """
        from type_bridge.query import _format_value

        # Format the value for TypeQL
        formatted_value = _format_value(self.value.value)

        # Get attribute type name for schema
        attr_type_name = self.attr_type.get_attribute_name()

        # Generate attribute variable name (lowercased to avoid conflicts)
        attr_var = f"${attr_type_name.lower()}"

        # Generate pattern (no trailing semicolon - QueryBuilder adds those)
        pattern = (
            f"{var} has {attr_type_name} {attr_var}; {attr_var} {self.operator} {formatted_value}"
        )

        return pattern

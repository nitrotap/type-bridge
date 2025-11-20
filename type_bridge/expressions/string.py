"""String-specific expressions for text filtering."""

from typing import TYPE_CHECKING, Literal

from type_bridge.expressions.base import Expression

if TYPE_CHECKING:
    from type_bridge.attribute.string import String


class StringExpr[T: "String"](Expression):
    """
    Type-safe string expression for text-based filtering.

    Represents string operations like contains, like (regex), etc.
    """

    def __init__(
        self,
        attr_type: type[T],
        operation: Literal["contains", "like", "regex"],
        pattern: T,
    ):
        """
        Create a string expression.

        Args:
            attr_type: String attribute type to filter on
            operation: String operation type
            pattern: Pattern to match
        """
        self.attr_type = attr_type
        self.operation = operation
        self.pattern = pattern

    def to_typeql(self, var: str) -> str:
        """
        Generate TypeQL pattern for this string operation.

        Example output: "$e has Name $name; $name contains 'Alice'"

        Args:
            var: Entity variable name

        Returns:
            TypeQL pattern string (without trailing semicolon)
        """
        # Get attribute type name for schema
        attr_type_name = self.attr_type.get_attribute_name()

        # Generate attribute variable name (lowercased to avoid conflicts)
        attr_var = f"${attr_type_name.lower()}"

        # Escape and quote the pattern
        escaped_pattern = self.pattern.value.replace("\\", "\\\\").replace('"', '\\"')
        quoted_pattern = f'"{escaped_pattern}"'

        # Map operation to TypeQL keyword
        # AUTOMATIC CONVERSION: regex() → 'like' in TypeQL
        if self.operation == "regex":
            # TypeQL uses 'like' for regex patterns (both do the same thing)
            typeql_op = "like"
        else:
            typeql_op = self.operation

        # Generate pattern (no trailing semicolon - QueryBuilder adds those)
        pattern = f"{var} has {attr_type_name} {attr_var}; {attr_var} {typeql_op} {quoted_pattern}"

        return pattern

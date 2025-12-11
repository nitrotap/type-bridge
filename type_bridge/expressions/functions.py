"""Function call expression support."""

from dataclasses import dataclass
from typing import Any

from .base import Expression


@dataclass
class FunctionCallExpr[T](Expression):
    """Represents a call to a TypeDB function.

    The generic type parameter T represents the return type of the function,
    allowing for type-safe function call expressions.

    Example:
        >>> # A function returning an integer stream
        >>> expr: FunctionCallExpr[int] = calculate_age(birth_date)
        >>> # A function returning a tuple
        >>> expr: FunctionCallExpr[tuple[int, int]] = divide(10, 3)
    """

    name: str
    args: list[Any]

    def to_typeql(self, var: str) -> str:
        """Convert to TypeQL function call syntax."""
        # Note: Argument resolution (Attributes -> Variables) typically happens
        # in the QueryBuilder before this string generation.
        # This is a basic implementation.
        arg_strs = []
        for arg in self.args:
            if isinstance(arg, Expression):
                arg_strs.append(arg.to_typeql(var))
            else:
                arg_strs.append(str(arg))

        return f"{self.name}({', '.join(arg_strs)})"

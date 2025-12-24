"""Boolean expressions for logical combinations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from type_bridge.expressions.base import Expression

if TYPE_CHECKING:
    from type_bridge.attribute.base import Attribute


class BooleanExpr(Expression):
    """
    Boolean expression for combining other expressions with AND, OR, NOT.

    Represents logical combinations of query constraints.
    """

    def __init__(
        self,
        operation: Literal["and", "or", "not"],
        operands: list[Expression],
    ):
        """
        Create a boolean expression.

        Args:
            operation: Boolean operation type
            operands: List of expressions to combine
        """
        self.operation = operation
        self.operands = operands

        # Validate operand count
        if operation == "not" and len(operands) != 1:
            raise ValueError("NOT operation requires exactly 1 operand")
        if operation in ("and", "or") and len(operands) < 2:
            raise ValueError(f"{operation.upper()} operation requires at least 2 operands")

    def get_attribute_types(self) -> set[type[Attribute]]:
        """
        Get all attribute types referenced by this boolean expression.

        Recursively collects attribute types from all operands.

        Returns:
            Set of attribute types used in this expression and its operands
        """
        result = set()
        for operand in self.operands:
            result.update(operand.get_attribute_types())
        return result

    def to_typeql(self, var: str) -> str:
        """
        Generate TypeQL pattern for this boolean expression.

        Example outputs:
        - AND: "$e has age $age; $age > 30; $e has city $city; $city == 'NYC'"
        - OR: "{ ... } or { ... }"
        - NOT: "not { ... }"

        Args:
            var: Entity variable name

        Returns:
            TypeQL pattern string (without trailing semicolon)
        """
        if self.operation == "and":
            # AND is just concatenating patterns with semicolons
            patterns = [op.to_typeql(var) for op in self.operands]
            return "; ".join(patterns)

        if self.operation == "or":
            # OR creates disjunction blocks (no trailing semicolon)
            # TypeDB requires OR blocks to be on separate lines
            patterns = [op.to_typeql(var) for op in self.operands]
            # Each pattern becomes a block
            blocks = [f"{{ {pattern}; }}" for pattern in patterns]
            return "\nor\n".join(blocks)

        if self.operation == "not":
            # NOT creates a negation block (no trailing semicolon)
            pattern = self.operands[0].to_typeql(var)
            return f"not {{ {pattern}; }}"

        # This should never happen due to Literal type, but for safety
        raise ValueError(f"Unknown boolean operation: {self.operation}")

    def and_(self, other: Expression) -> BooleanExpr:
        """
        Combine with another expression using AND, flattening if possible.

        If this is already an AND expression, adds the new operand to create
        a flat structure instead of a nested binary tree.

        Args:
            other: Another expression to AND with this one

        Returns:
            BooleanExpr with flattened operands
        """
        if self.operation == "and":
            # Flatten: (a AND b).and_(c) -> (a AND b AND c)
            return BooleanExpr("and", [*self.operands, other])
        # Different operation, must wrap
        return BooleanExpr("and", [self, other])

    def or_(self, other: Expression) -> BooleanExpr:
        """
        Combine with another expression using OR, flattening if possible.

        If this is already an OR expression, adds the new operand to create
        a flat structure instead of a nested binary tree. This is critical
        for avoiding TypeDB query planner stack overflow with many values.

        Args:
            other: Another expression to OR with this one

        Returns:
            BooleanExpr with flattened operands
        """
        if self.operation == "or":
            # Flatten: (a OR b).or_(c) -> (a OR b OR c)
            return BooleanExpr("or", [*self.operands, other])
        # Different operation, must wrap
        return BooleanExpr("or", [self, other])

"""Unit tests for lookup filter parsing on EntityManager."""

import pytest

from type_bridge import Entity, Flag, Integer, Key, String, TypeFlags
from type_bridge.crud.entity.manager import EntityManager
from type_bridge.expressions import AttributeExistsExpr, ComparisonExpr
from type_bridge.session import Database


class Name(String):
    pass


class Age(Integer):
    pass


class Person(Entity):
    flags = TypeFlags(name="person")
    name: Name = Flag(Key)
    age: Age | None


def build_manager():
    # Database is not connected; _parse_lookup_filters doesn't execute queries
    return EntityManager(Database(database="typedb"), Person)


def test_lookup_in_builds_or_expression():
    mgr = build_manager()
    base, exprs = mgr._parse_lookup_filters({"name__in": ["Alice", Name("Bob")]})
    assert base == {}
    assert len(exprs) == 1
    expr = exprs[0]
    # Should be an OR of eq comparisons
    from type_bridge.expressions import BooleanExpr

    assert isinstance(expr, BooleanExpr)
    assert expr.operation == "or"


def test_lookup_in_creates_flat_or_not_nested():
    """Test that __in lookup creates a flat OR with all operands at same level.

    This is critical for avoiding TypeDB query planner stack overflow with
    many values. A flat OR like (a or b or c or d) is safe, but a nested
    binary tree like (((a or b) or c) or d) causes stack overflow with 75+ values.

    See: https://github.com/ds1sqe/type-bridge/issues/76
    """
    from type_bridge.expressions import BooleanExpr

    mgr = build_manager()
    values = [f"name_{i}" for i in range(100)]  # 100 values
    base, exprs = mgr._parse_lookup_filters({"name__in": values})

    assert len(exprs) == 1
    expr = exprs[0]
    assert isinstance(expr, BooleanExpr)
    assert expr.operation == "or"
    # All operands should be at the same level (flat structure)
    assert len(expr.operands) == 100
    # Each operand should be a ComparisonExpr, not a nested BooleanExpr
    for operand in expr.operands:
        assert isinstance(operand, ComparisonExpr)


def test_lookup_in_single_value_no_boolean_expr():
    """Test that __in lookup with a single value returns just the comparison."""
    mgr = build_manager()
    base, exprs = mgr._parse_lookup_filters({"name__in": ["Alice"]})

    assert len(exprs) == 1
    expr = exprs[0]
    # Single value should not wrap in BooleanExpr
    assert isinstance(expr, ComparisonExpr)


def test_lookup_gt_and_base_filters_split():
    mgr = build_manager()
    base, exprs = mgr._parse_lookup_filters({"name": Name("Alice"), "age__gt": 30})
    assert base == {"name": Name("Alice")}
    assert len(exprs) == 1
    assert isinstance(exprs[0], ComparisonExpr)


def test_isnull_builds_exists_expr():
    mgr = build_manager()
    base, exprs = mgr._parse_lookup_filters({"age__isnull": True})
    assert base == {}
    assert len(exprs) == 1
    assert isinstance(exprs[0], AttributeExistsExpr)


def test_string_lookups_require_string_attr():
    mgr = build_manager()
    with pytest.raises(ValueError):
        mgr._parse_lookup_filters({"age__contains": 1})


def test_in_lookup_requires_iterable_and_non_empty():
    mgr = build_manager()
    with pytest.raises(ValueError):
        mgr._parse_lookup_filters({"name__in": 123})
    with pytest.raises(ValueError):
        mgr._parse_lookup_filters({"name__in": []})


def test_unknown_lookup_raises():
    mgr = build_manager()
    with pytest.raises(ValueError):
        mgr._parse_lookup_filters({"name__bogus": "x"})


def test_field_with_double_underscore_rejected():
    mgr = build_manager()
    with pytest.raises(ValueError):
        mgr._parse_lookup_filters({"name__part__eq": "x"})


# ============================================================
# Additional comparison lookup tests
# ============================================================


def test_lookup_gte_builds_comparison_expr():
    """Test __gte lookup creates greater-than-or-equal comparison."""
    mgr = build_manager()
    base, exprs = mgr._parse_lookup_filters({"age__gte": 30})
    assert base == {}
    assert len(exprs) == 1
    assert isinstance(exprs[0], ComparisonExpr)


def test_lookup_lt_builds_comparison_expr():
    """Test __lt lookup creates less-than comparison."""
    mgr = build_manager()
    base, exprs = mgr._parse_lookup_filters({"age__lt": 30})
    assert base == {}
    assert len(exprs) == 1
    assert isinstance(exprs[0], ComparisonExpr)


def test_lookup_lte_builds_comparison_expr():
    """Test __lte lookup creates less-than-or-equal comparison."""
    mgr = build_manager()
    base, exprs = mgr._parse_lookup_filters({"age__lte": 30})
    assert base == {}
    assert len(exprs) == 1
    assert isinstance(exprs[0], ComparisonExpr)


# ============================================================
# Exact/eq alias tests
# ============================================================


def test_lookup_exact_is_alias_for_base_filter():
    """Test __exact lookup is treated as base filter (exact match)."""
    mgr = build_manager()
    base, exprs = mgr._parse_lookup_filters({"name__exact": "Alice"})
    assert base == {"name": "Alice"}
    assert exprs == []


def test_lookup_eq_is_alias_for_base_filter():
    """Test __eq lookup is treated as base filter (exact match)."""
    mgr = build_manager()
    base, exprs = mgr._parse_lookup_filters({"name__eq": Name("Alice")})
    assert base == {"name": Name("Alice")}
    assert exprs == []


# ============================================================
# isnull=False test
# ============================================================


def test_isnull_false_builds_exists_expr_present():
    """Test __isnull=False creates AttributeExistsExpr with present=True."""
    mgr = build_manager()
    base, exprs = mgr._parse_lookup_filters({"age__isnull": False})
    assert base == {}
    assert len(exprs) == 1
    assert isinstance(exprs[0], AttributeExistsExpr)
    assert exprs[0].present is True


# ============================================================
# Combined/mixed lookup tests
# ============================================================


def test_multiple_lookups_combined():
    """Test multiple lookup filters on different fields."""
    mgr = build_manager()
    base, exprs = mgr._parse_lookup_filters(
        {"name__startswith": "A", "age__gte": 18, "age__lt": 65}
    )
    assert base == {}
    assert len(exprs) == 3


def test_mixed_base_and_lookup_filters():
    """Test mixing base filters with lookup filters."""
    mgr = build_manager()
    base, exprs = mgr._parse_lookup_filters({"name": Name("Alice"), "age__gt": 25})
    assert base == {"name": Name("Alice")}
    assert len(exprs) == 1
    assert isinstance(exprs[0], ComparisonExpr)


def test_multiple_lookups_same_field():
    """Test multiple lookups on the same field (range query)."""
    mgr = build_manager()
    base, exprs = mgr._parse_lookup_filters({"age__gte": 18, "age__lte": 65})
    assert base == {}
    assert len(exprs) == 2
    # Both should be ComparisonExpr
    assert all(isinstance(e, ComparisonExpr) for e in exprs)

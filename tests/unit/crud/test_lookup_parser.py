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

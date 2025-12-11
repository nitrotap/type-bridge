"""Unit tests for order_by() method on EntityQuery and RelationQuery."""

from typing import Any, cast

import pytest

from type_bridge import (
    Card,
    Entity,
    Flag,
    Integer,
    Key,
    Relation,
    Role,
    String,
    TypeFlags,
)
from type_bridge.crud.entity.query import EntityQuery
from type_bridge.crud.relation.query import RelationQuery
from type_bridge.session import Connection


# Test attribute types
class Name(String):
    pass


class Age(Integer):
    pass


class City(String):
    pass


class Tags(String):
    pass


class Salary(Integer):
    pass


class Position(String):
    pass


# Test entity
class Person(Entity):
    flags = TypeFlags(name="ob_person")
    name: Name = Flag(Key)
    age: Age | None = None
    city: City | None = None
    tags: list[Tags] = Flag(Card(min=0, max=None))


# Test company entity for relations
class Company(Entity):
    flags = TypeFlags(name="ob_company")
    name: Name = Flag(Key)


# Test relation
class Employment(Relation):
    flags = TypeFlags(name="ob_employment")
    employee: Role[Person] = Role("employee", Person)
    employer: Role[Company] = Role("employer", Company)
    position: Position | None = None
    salary: Salary | None = None


def mock_connection() -> Connection:
    """Create a mock connection for unit tests that don't execute queries."""
    # Cast Any to Connection for tests that only validate parsing (never execute)
    return cast(Connection, cast(Any, None))


class TestEntityQueryOrderByValidation:
    """Tests for EntityQuery.order_by() validation."""

    def test_order_by_unknown_field_raises_error(self):
        """Should raise ValueError for unknown field."""
        query = EntityQuery(mock_connection(), Person)

        with pytest.raises(ValueError, match="Unknown sort field 'unknown'"):
            query.order_by("unknown")

    def test_order_by_multi_value_attr_raises_error(self):
        """Should raise ValueError for multi-value attribute."""
        query = EntityQuery(mock_connection(), Person)

        with pytest.raises(ValueError, match="Cannot sort by multi-value attribute 'tags'"):
            query.order_by("tags")

    def test_order_by_returns_self(self):
        """order_by() should return self for chaining."""
        query = EntityQuery(mock_connection(), Person)
        result = query.order_by("name")
        assert result is query

    def test_order_by_single_field_asc(self):
        """Should parse single ascending field."""
        query = EntityQuery(mock_connection(), Person)
        query.order_by("name")

        assert len(query._order_by_fields) == 1
        assert query._order_by_fields[0] == ("name", "asc")

    def test_order_by_single_field_desc(self):
        """Should parse single descending field with '-' prefix."""
        query = EntityQuery(mock_connection(), Person)
        query.order_by("-age")

        assert len(query._order_by_fields) == 1
        assert query._order_by_fields[0] == ("age", "desc")

    def test_order_by_multiple_fields(self):
        """Should parse multiple sort fields."""
        query = EntityQuery(mock_connection(), Person)
        query.order_by("city", "-age", "name")

        assert len(query._order_by_fields) == 3
        assert query._order_by_fields[0] == ("city", "asc")
        assert query._order_by_fields[1] == ("age", "desc")
        assert query._order_by_fields[2] == ("name", "asc")

    def test_order_by_combined_with_limit(self):
        """order_by() should work with limit()."""
        query = EntityQuery(mock_connection(), Person)
        result = query.order_by("name").limit(10)

        assert result._order_by_fields == [("name", "asc")]
        assert result._limit_value == 10

    def test_order_by_combined_with_offset(self):
        """order_by() should work with offset()."""
        query = EntityQuery(mock_connection(), Person)
        result = query.order_by("-age").offset(5)

        assert result._order_by_fields == [("age", "desc")]
        assert result._offset_value == 5

    def test_order_by_chained_calls(self):
        """Multiple order_by() calls should accumulate fields."""
        query = EntityQuery(mock_connection(), Person)
        query.order_by("name").order_by("-age")

        assert len(query._order_by_fields) == 2
        assert query._order_by_fields[0] == ("name", "asc")
        assert query._order_by_fields[1] == ("age", "desc")


class TestRelationQueryOrderByValidation:
    """Tests for RelationQuery.order_by() validation."""

    def test_order_by_unknown_field_raises_error(self):
        """Should raise ValueError for unknown relation field."""
        query = RelationQuery(mock_connection(), Employment)

        with pytest.raises(ValueError, match="Unknown sort field 'unknown'"):
            query.order_by("unknown")

    def test_order_by_returns_self(self):
        """order_by() should return self for chaining."""
        query = RelationQuery(mock_connection(), Employment)
        result = query.order_by("salary")
        assert result is query

    def test_order_by_relation_attribute_asc(self):
        """Should parse relation attribute ascending."""
        query = RelationQuery(mock_connection(), Employment)
        query.order_by("salary")

        assert len(query._order_by_fields) == 1
        assert query._order_by_fields[0] == ("salary", "asc", None)

    def test_order_by_relation_attribute_desc(self):
        """Should parse relation attribute descending."""
        query = RelationQuery(mock_connection(), Employment)
        query.order_by("-position")

        assert len(query._order_by_fields) == 1
        assert query._order_by_fields[0] == ("position", "desc", None)

    def test_order_by_role_player_attribute(self):
        """Should parse role__attr syntax."""
        query = RelationQuery(mock_connection(), Employment)
        query.order_by("employee__age")

        assert len(query._order_by_fields) == 1
        assert query._order_by_fields[0] == ("age", "asc", "employee")

    def test_order_by_role_player_attribute_desc(self):
        """Should parse -role__attr syntax for descending."""
        query = RelationQuery(mock_connection(), Employment)
        query.order_by("-employee__age")

        assert len(query._order_by_fields) == 1
        assert query._order_by_fields[0] == ("age", "desc", "employee")

    def test_order_by_unknown_role_raises_error(self):
        """Should raise ValueError for unknown role."""
        query = RelationQuery(mock_connection(), Employment)

        with pytest.raises(ValueError, match="Unknown role 'unknown'"):
            query.order_by("unknown__age")

    def test_order_by_unknown_role_attr_raises_error(self):
        """Should raise ValueError for unknown role attribute."""
        query = RelationQuery(mock_connection(), Employment)

        with pytest.raises(ValueError, match="do not have attribute 'unknown'"):
            query.order_by("employee__unknown")

    def test_order_by_mixed_relation_and_role_player(self):
        """Should parse mixed relation and role-player sort fields."""
        query = RelationQuery(mock_connection(), Employment)
        query.order_by("employee__age", "-salary")

        assert len(query._order_by_fields) == 2
        assert query._order_by_fields[0] == ("age", "asc", "employee")
        assert query._order_by_fields[1] == ("salary", "desc", None)

    def test_order_by_multiple_role_players(self):
        """Should parse multiple role-player sort fields."""
        query = RelationQuery(mock_connection(), Employment)
        query.order_by("employee__name", "-employer__name")

        assert len(query._order_by_fields) == 2
        assert query._order_by_fields[0] == ("name", "asc", "employee")
        assert query._order_by_fields[1] == ("name", "desc", "employer")

    def test_order_by_combined_with_limit(self):
        """order_by() should work with limit()."""
        query = RelationQuery(mock_connection(), Employment)
        result = query.order_by("employee__age").limit(10)

        assert result._order_by_fields == [("age", "asc", "employee")]
        assert result._limit_value == 10

    def test_order_by_combined_with_offset(self):
        """order_by() should work with offset()."""
        query = RelationQuery(mock_connection(), Employment)
        result = query.order_by("-salary").offset(5)

        assert result._order_by_fields == [("salary", "desc", None)]
        assert result._offset_value == 5

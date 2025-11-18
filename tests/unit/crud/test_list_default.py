"""Tests for list field default values and serialization."""

from datetime import UTC, datetime

import pytest

from type_bridge.attribute.datetime import DateTime
from type_bridge.attribute.flags import Card, Flag, Key
from type_bridge.attribute.string import String
from type_bridge.models.entity import Entity


class IssueKey(String):
    pass


class IssueLabel(String):
    pass


class CreatedAt(DateTime):
    pass


class ModifiedAt(DateTime):
    pass


class Issue(Entity):
    """Test entity with list field."""

    key: IssueKey = Flag(Key)
    labels: list[IssueLabel] = Flag(Card(min=0))
    created_at: CreatedAt
    last_modified: ModifiedAt


class TestListFieldDefaults:
    """Test that list fields with Card(min=0) default to empty list."""

    def test_list_field_defaults_to_empty_when_not_provided(self):
        """When a list field with Card(min=0) is not provided, it should default to []."""
        _now = datetime.now(UTC)

        issue = Issue(
            key=IssueKey("TEST-123"),
            # labels not provided
            created_at=CreatedAt(_now),
            last_modified=ModifiedAt(_now),
        )

        assert issue.labels == []
        assert isinstance(issue.labels, list)

    def test_list_field_with_values_works(self):
        """List field with provided values should work normally."""
        _now = datetime.now(UTC)

        issue = Issue(
            key=IssueKey("TEST-123"),
            labels=[IssueLabel("bug"), IssueLabel("critical")],
            created_at=CreatedAt(_now),
            last_modified=ModifiedAt(_now),
        )

        assert len(issue.labels) == 2
        assert all(isinstance(label, IssueLabel) for label in issue.labels)
        assert issue.labels[0].value == "bug"
        assert issue.labels[1].value == "critical"

    def test_list_field_with_empty_list_works(self):
        """Explicitly providing empty list should work."""
        _now = datetime.now(UTC)

        issue = Issue(
            key=IssueKey("TEST-123"),
            labels=[],
            created_at=CreatedAt(_now),
            last_modified=ModifiedAt(_now),
        )

        assert issue.labels == []

    def test_serialization_when_list_not_provided(self):
        """model_dump should work when list field is not provided."""
        _now = datetime.now(UTC)

        issue = Issue(
            key=IssueKey("TEST-123"),
            created_at=CreatedAt(_now),
            last_modified=ModifiedAt(_now),
        )

        # Should not raise any error
        data = issue.model_dump(mode="json")
        assert data["labels"] == []
        assert data["key"] == "TEST-123"

    def test_serialization_with_list_values(self):
        """model_dump should work when list field has values."""
        _now = datetime.now(UTC)

        issue = Issue(
            key=IssueKey("TEST-123"),
            labels=[IssueLabel("bug"), IssueLabel("auth")],
            created_at=CreatedAt(_now),
            last_modified=ModifiedAt(_now),
        )

        data = issue.model_dump(mode="json")
        assert data["labels"] == ["bug", "auth"]

    def test_model_dump_json_when_list_not_provided(self):
        """model_dump_json should work when list field is not provided."""
        _now = datetime.now(UTC)

        issue = Issue(
            key=IssueKey("TEST-123"),
            created_at=CreatedAt(_now),
            last_modified=ModifiedAt(_now),
        )

        # Should not raise any error
        json_str = issue.model_dump_json()
        assert '"labels":[]' in json_str

    def test_insert_query_when_list_not_provided(self):
        """Insert query should work when list field is not provided."""
        _now = datetime.now(UTC)

        issue = Issue(
            key=IssueKey("TEST-123"),
            created_at=CreatedAt(_now),
            last_modified=ModifiedAt(_now),
        )

        query = issue.to_insert_query()
        assert "$e isa Issue" in query
        assert 'has IssueKey "TEST-123"' in query
        # Empty list should not generate any 'has IssueLabel' clauses
        assert "has IssueLabel" not in query

    def test_insert_query_with_list_values(self):
        """Insert query should include all list values."""
        _now = datetime.now(UTC)

        issue = Issue(
            key=IssueKey("TEST-123"),
            labels=[IssueLabel("bug"), IssueLabel("auth")],
            created_at=CreatedAt(_now),
            last_modified=ModifiedAt(_now),
        )

        query = issue.to_insert_query()
        assert 'has IssueLabel "bug"' in query
        assert 'has IssueLabel "auth"' in query

    def test_none_for_list_field_raises_error(self):
        """Explicitly providing None for list field should raise validation error."""
        _now = datetime.now(UTC)

        with pytest.raises(Exception):  # Pydantic ValidationError
            Issue(
                key=IssueKey("TEST-123"),
                labels=None,  # type: ignore
                created_at=CreatedAt(_now),
                last_modified=ModifiedAt(_now),
            )

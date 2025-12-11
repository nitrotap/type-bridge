"""Unit tests for annotation parsing."""

from __future__ import annotations

from type_bridge.generator.annotations import (
    extract_annotations,
    parse_annotation,
    parse_annotation_value,
)


class TestParseAnnotationValue:
    """Tests for parse_annotation_value."""

    def test_string_unquoted(self) -> None:
        """Parse unquoted string."""
        assert parse_annotation_value("PROJ") == "PROJ"

    def test_string_double_quoted(self) -> None:
        """Parse double-quoted string."""
        assert parse_annotation_value('"hello world"') == "hello world"

    def test_string_single_quoted(self) -> None:
        """Parse single-quoted string."""
        assert parse_annotation_value("'hello'") == "hello"

    def test_integer(self) -> None:
        """Parse integer."""
        assert parse_annotation_value("42") == 42
        assert parse_annotation_value("-5") == -5

    def test_float(self) -> None:
        """Parse float."""
        assert parse_annotation_value("3.14") == 3.14
        assert parse_annotation_value("-2.5") == -2.5

    def test_boolean_true(self) -> None:
        """Parse boolean true."""
        assert parse_annotation_value("true") is True
        assert parse_annotation_value("True") is True
        assert parse_annotation_value("TRUE") is True

    def test_boolean_false(self) -> None:
        """Parse boolean false."""
        assert parse_annotation_value("false") is False
        assert parse_annotation_value("False") is False
        assert parse_annotation_value("FALSE") is False

    def test_empty_string(self) -> None:
        """Parse empty string."""
        assert parse_annotation_value("") == ""
        assert parse_annotation_value("  ") == ""


class TestParseAnnotation:
    """Tests for parse_annotation."""

    def test_flag_annotation(self) -> None:
        """Parse boolean flag annotation."""
        result = parse_annotation("# @searchable")
        assert result == ("searchable", True)

    def test_single_value_string(self) -> None:
        """Parse annotation with single string value."""
        result = parse_annotation("# @prefix(PROJ)")
        assert result == ("prefix", "PROJ")

    def test_single_value_integer(self) -> None:
        """Parse annotation with integer value."""
        result = parse_annotation("# @priority(3)")
        assert result == ("priority", 3)

    def test_single_value_boolean(self) -> None:
        """Parse annotation with boolean value."""
        result = parse_annotation("# @enabled(true)")
        assert result == ("enabled", True)

    def test_multiple_values(self) -> None:
        """Parse annotation with multiple values."""
        result = parse_annotation("# @tags(api, public, v2)")
        assert result == ("tags", ["api", "public", "v2"])

    def test_empty_parens(self) -> None:
        """Parse annotation with empty parentheses."""
        result = parse_annotation("# @flag()")
        assert result == ("flag", True)

    def test_quoted_value(self) -> None:
        """Parse annotation with quoted value containing spaces."""
        result = parse_annotation('# @label("My Label")')
        assert result == ("label", "My Label")

    def test_hyphenated_name(self) -> None:
        """Parse annotation with hyphenated name."""
        result = parse_annotation("# @my-annotation(value)")
        assert result == ("my-annotation", "value")

    def test_not_annotation(self) -> None:
        """Non-annotation line returns None."""
        assert parse_annotation("# Just a comment") is None
        assert parse_annotation("entity person;") is None
        assert parse_annotation("") is None

    def test_with_whitespace(self) -> None:
        """Parse annotation with various whitespace."""
        result = parse_annotation("  #   @prefix(PROJ)  ")
        assert result == ("prefix", "PROJ")


class TestExtractAnnotations:
    """Tests for extract_annotations."""

    def test_entity_annotations(self) -> None:
        """Extract annotations for entities."""
        schema = """
define
# @prefix(PROJ)
# @searchable
entity project,
    owns name;
"""
        entity_annots, attr_annots, rel_annots, role_annots = extract_annotations(schema)

        assert "project" in entity_annots
        assert entity_annots["project"] == {"prefix": "PROJ", "searchable": True}
        assert attr_annots == {}

    def test_attribute_annotations(self) -> None:
        """Extract annotations for attributes."""
        schema = """
define
# @default(new)
# @transform(lower)
attribute status, value string;
"""
        entity_annots, attr_annots, rel_annots, role_annots = extract_annotations(schema)

        assert "status" in attr_annots
        assert attr_annots["status"] == {"default": "new", "transform": "lower"}
        assert entity_annots == {}

    def test_relation_annotations(self) -> None:
        """Extract annotations for relations."""
        schema = """
define
# @bidirectional
relation friendship,
    relates friend;
"""
        entity_annots, attr_annots, rel_annots, role_annots = extract_annotations(schema)

        assert "friendship" in rel_annots
        assert rel_annots["friendship"] == {"bidirectional": True}

    def test_role_annotations(self) -> None:
        """Extract annotations for relation roles."""
        schema = """
define
relation ownership,
    # @required
    relates owner,
    # @cascade(delete)
    relates owned;
"""
        entity_annots, attr_annots, rel_annots, role_annots = extract_annotations(schema)

        assert "ownership" in role_annots
        assert role_annots["ownership"]["owner"] == {"required": True}
        assert role_annots["ownership"]["owned"] == {"cascade": "delete"}

    def test_multiple_definitions(self) -> None:
        """Extract annotations from multiple definitions."""
        schema = """
define
# @prefix(P)
entity person, owns name;

# @prefix(O)
entity organization, owns name;

# @default(active)
attribute status, value string;
"""
        entity_annots, attr_annots, rel_annots, role_annots = extract_annotations(schema)

        assert entity_annots["person"] == {"prefix": "P"}
        assert entity_annots["organization"] == {"prefix": "O"}
        assert attr_annots["status"] == {"default": "active"}

    def test_no_annotations(self) -> None:
        """Handle schema with no annotations."""
        schema = """
define
entity person, owns name;
attribute name, value string;
"""
        entity_annots, attr_annots, rel_annots, role_annots = extract_annotations(schema)

        assert entity_annots == {}
        assert attr_annots == {}
        assert rel_annots == {}
        assert role_annots == {}

    def test_mixed_annotations_and_comments(self) -> None:
        """Regular comments don't become annotations."""
        schema = """
define
# This is just a regular comment
# @prefix(PROJ)
# Another regular comment gets ignored because @prefix was already consumed
entity project, owns name;
"""
        entity_annots, attr_annots, rel_annots, role_annots = extract_annotations(schema)

        assert "project" in entity_annots
        assert entity_annots["project"] == {"prefix": "PROJ"}

"""Tests for the TQL schema parser."""

from __future__ import annotations

import pytest

from type_bridge.generator.models import Cardinality
from type_bridge.generator.parser import parse_tql_schema


class TestParseAttributes:
    """Tests for attribute parsing."""

    def test_simple_attribute(self) -> None:
        """Parse a simple attribute with value type."""
        schema = parse_tql_schema("""
            define
            attribute name, value string;
        """)
        assert "name" in schema.attributes
        attr = schema.attributes["name"]
        assert attr.name == "name"
        assert attr.value_type == "string"
        assert attr.parent is None
        assert attr.abstract is False

    def test_attribute_inheritance(self) -> None:
        """Parse attribute with sub (inheritance)."""
        schema = parse_tql_schema("""
            define
            attribute isbn @abstract, value string;

            define
            attribute isbn-13 sub isbn;
        """)
        assert "isbn" in schema.attributes
        assert "isbn-13" in schema.attributes

        parent = schema.attributes["isbn"]
        assert parent.abstract is True
        assert parent.value_type == "string"

        child = schema.attributes["isbn-13"]
        assert child.parent == "isbn"
        assert child.value_type == ""  # Inherited from parent

    def test_attribute_with_regex(self) -> None:
        """Parse attribute with @regex constraint."""
        schema = parse_tql_schema("""
            define
            attribute status, value string @regex("^(active|inactive)$");
        """)
        attr = schema.attributes["status"]
        assert attr.regex == "^(active|inactive)$"

    def test_attribute_with_values(self) -> None:
        """Parse attribute with @values constraint."""
        schema = parse_tql_schema("""
            define
            attribute emoji, value string @values("like", "love", "sad");
        """)
        attr = schema.attributes["emoji"]
        assert attr.allowed_values == ("like", "love", "sad")


class TestParseEntities:
    """Tests for entity parsing."""

    def test_simple_entity(self) -> None:
        """Parse a simple entity with owns."""
        schema = parse_tql_schema("""
            define
            attribute name, value string;

            define
            entity person,
                owns name;
        """)
        assert "person" in schema.entities
        entity = schema.entities["person"]
        assert entity.name == "person"
        assert "name" in entity.owns
        assert entity.parent is None
        assert entity.abstract is False

    def test_entity_inheritance(self) -> None:
        """Parse entity with sub (inheritance)."""
        schema = parse_tql_schema("""
            define
            entity company @abstract,
                owns name;

            define
            entity publisher sub company;
        """)
        parent = schema.entities["company"]
        assert parent.abstract is True

        child = schema.entities["publisher"]
        assert child.parent == "company"
        # After inheritance accumulation, child inherits owns
        assert "name" in child.owns

    def test_entity_with_key(self) -> None:
        """Parse entity with @key attribute."""
        schema = parse_tql_schema("""
            define
            attribute id, value string;

            define
            entity user,
                owns id @key;
        """)
        entity = schema.entities["user"]
        assert "id" in entity.keys
        assert "id" in entity.owns

    def test_entity_with_unique(self) -> None:
        """Parse entity with @unique attribute."""
        schema = parse_tql_schema("""
            define
            attribute email, value string;

            define
            entity user,
                owns email @unique;
        """)
        entity = schema.entities["user"]
        assert "email" in entity.uniques

    def test_entity_with_cardinality(self) -> None:
        """Parse entity with @card on owns."""
        schema = parse_tql_schema("""
            define
            attribute tag, value string;
            attribute bio, value string;

            define
            entity profile,
                owns tag @card(0..),
                owns bio @card(1);
        """)
        entity = schema.entities["profile"]

        tag_card = entity.cardinalities["tag"]
        assert tag_card.min == 0
        assert tag_card.max is None  # Unbounded
        assert tag_card.is_multi is True

        bio_card = entity.cardinalities["bio"]
        assert bio_card.min == 1
        assert bio_card.max == 1
        assert bio_card.is_required is True
        assert bio_card.is_single is True

    def test_entity_with_plays(self) -> None:
        """Parse entity with plays."""
        schema = parse_tql_schema("""
            define
            entity person,
                plays friendship:friend,
                plays employment:employee;
        """)
        entity = schema.entities["person"]
        assert "friendship:friend" in entity.plays
        assert "employment:employee" in entity.plays


class TestParseRelations:
    """Tests for relation parsing."""

    def test_simple_relation(self) -> None:
        """Parse a simple relation with relates."""
        schema = parse_tql_schema("""
            define
            relation friendship,
                relates friend;
        """)
        assert "friendship" in schema.relations
        rel = schema.relations["friendship"]
        assert rel.name == "friendship"
        assert len(rel.roles) == 1
        assert rel.roles[0].name == "friend"

    def test_relation_with_owns(self) -> None:
        """Parse relation that owns attributes."""
        schema = parse_tql_schema("""
            define
            attribute since, value datetime;

            define
            relation friendship,
                relates friend,
                owns since;
        """)
        rel = schema.relations["friendship"]
        assert "since" in rel.owns

    def test_relation_inheritance(self) -> None:
        """Parse relation with sub (inheritance)."""
        schema = parse_tql_schema("""
            define
            relation contribution,
                relates contributor,
                relates work;

            define
            relation authoring sub contribution,
                relates author as contributor;
        """)
        parent = schema.relations["contribution"]
        assert len(parent.roles) == 2

        child = schema.relations["authoring"]
        assert child.parent == "contribution"
        # Child has "author" role which overrides "contributor"
        assert any(r.name == "author" for r in child.roles)
        author_role = next(r for r in child.roles if r.name == "author")
        assert author_role.overrides == "contributor"

    def test_relation_abstract(self) -> None:
        """Parse abstract relation."""
        schema = parse_tql_schema("""
            define
            relation interaction @abstract,
                relates subject,
                relates content;
        """)
        rel = schema.relations["interaction"]
        assert rel.abstract is True


class TestParseFunctionsHandling:
    """Tests for function handling."""

    def test_functions_parsed(self) -> None:
        """Functions should be parsed correctly."""
        schema = parse_tql_schema("""
            define
            entity person,
                owns name;

            attribute name, value string;

            fun get_person($name: string) -> { person }:
              match
                $p isa person, has name $name;
              return { $p };
        """)
        # Should still parse the entity and attribute
        assert "person" in schema.entities
        assert "name" in schema.attributes

        # Should parse the function
        assert "get_person" in schema.functions
        assert schema.functions["get_person"].return_type == "person"



class TestParseCardinality:
    """Tests for cardinality parsing."""

    @pytest.mark.parametrize(
        ("card_str", "expected_min", "expected_max"),
        [
            ("@card(0..1)", 0, 1),
            ("@card(1)", 1, 1),
            ("@card(0..)", 0, None),
            ("@card(1..)", 1, None),
            ("@card(1..3)", 1, 3),
            ("@card(2..5)", 2, 5),
        ],
    )
    def test_cardinality_formats(
        self, card_str: str, expected_min: int, expected_max: int | None
    ) -> None:
        """Test various cardinality annotation formats."""
        schema = parse_tql_schema(f"""
            define
            attribute tag, value string;

            define
            entity item,
                owns tag {card_str};
        """)
        card = schema.entities["item"].cardinalities["tag"]
        assert card.min == expected_min
        assert card.max == expected_max


class TestCardinalityModel:
    """Tests for Cardinality dataclass properties."""

    def test_optional_single(self) -> None:
        card = Cardinality(0, 1)
        assert card.is_optional_single is True
        assert card.is_required is False
        assert card.is_single is True
        assert card.is_multi is False

    def test_required_single(self) -> None:
        card = Cardinality(1, 1)
        assert card.is_optional_single is False
        assert card.is_required is True
        assert card.is_single is True
        assert card.is_multi is False

    def test_optional_multi(self) -> None:
        card = Cardinality(0, None)
        assert card.is_optional_single is False
        assert card.is_required is False
        assert card.is_single is False
        assert card.is_multi is True

    def test_required_multi(self) -> None:
        card = Cardinality(1, None)
        assert card.is_required is True
        assert card.is_multi is True


class TestInheritanceAccumulation:
    """Tests for inheritance accumulation logic."""

    def test_entity_inherits_owns(self) -> None:
        """Child entity should inherit parent's owns."""
        schema = parse_tql_schema("""
            define
            attribute name, value string;
            attribute stock, value integer;

            define
            entity book @abstract,
                owns name;

            define
            entity paperback sub book,
                owns stock;
        """)
        child = schema.entities["paperback"]
        assert "name" in child.owns  # Inherited
        assert "stock" in child.owns  # Own

    def test_entity_inherits_keys(self) -> None:
        """Child entity should inherit parent's keys."""
        schema = parse_tql_schema("""
            define
            attribute isbn, value string;

            define
            entity book @abstract,
                owns isbn @key;

            define
            entity paperback sub book;
        """)
        child = schema.entities["paperback"]
        assert "isbn" in child.keys

    def test_deep_inheritance(self) -> None:
        """Multi-level inheritance should work."""
        schema = parse_tql_schema("""
            define
            attribute a, value string;
            attribute b, value string;
            attribute c, value string;

            define
            entity level1,
                owns a;

            define
            entity level2 sub level1,
                owns b;

            define
            entity level3 sub level2,
                owns c;
        """)
        child = schema.entities["level3"]
        assert "a" in child.owns
        assert "b" in child.owns
        assert "c" in child.owns

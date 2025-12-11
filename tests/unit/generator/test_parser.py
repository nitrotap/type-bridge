"""Tests for the TQL schema parser."""

from __future__ import annotations

import pytest

from type_bridge.generator import parse_tql_schema
from type_bridge.generator.models import Cardinality


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

    def test_attribute_independent(self) -> None:
        """Parse attribute with @independent flag."""
        schema = parse_tql_schema("""
            define
            attribute language @independent, value string;
        """)
        attr = schema.attributes["language"]
        assert attr.independent is True
        assert attr.value_type == "string"

    def test_attribute_independent_with_abstract(self) -> None:
        """Parse attribute with both @abstract and @independent."""
        schema = parse_tql_schema("""
            define
            attribute tag @abstract @independent, value string;
        """)
        attr = schema.attributes["tag"]
        assert attr.abstract is True
        assert attr.independent is True

    def test_attribute_not_independent_by_default(self) -> None:
        """Attribute without @independent should have independent=False."""
        schema = parse_tql_schema("""
            define
            attribute name, value string;
        """)
        attr = schema.attributes["name"]
        assert attr.independent is False


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
        assert schema.functions["get_person"].return_type == "{ person }"


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


class TestParseRange:
    """Tests for @range annotation on attributes."""

    def test_range_integer(self) -> None:
        """Parse @range on integer attribute."""
        schema = parse_tql_schema("""
            define
            attribute age, value integer @range(0..150);
        """)
        attr = schema.attributes["age"]
        assert attr.range_min == "0"
        assert attr.range_max == "150"

    def test_range_negative(self) -> None:
        """Parse @range with negative values."""
        schema = parse_tql_schema("""
            define
            attribute temperature, value double @range(-50..50);
        """)
        attr = schema.attributes["temperature"]
        assert attr.range_min == "-50"
        assert attr.range_max == "50"

    def test_range_float(self) -> None:
        """Parse @range with float values."""
        schema = parse_tql_schema("""
            define
            attribute percentage, value double @range(0.0..100.0);
        """)
        attr = schema.attributes["percentage"]
        assert attr.range_min == "0.0"
        assert attr.range_max == "100.0"

    def test_range_date(self) -> None:
        """Parse @range with date values."""
        schema = parse_tql_schema("""
            define
            attribute birth-date, value date @range(1900-01-01..2100-12-31);
        """)
        attr = schema.attributes["birth-date"]
        assert attr.range_min == "1900-01-01"
        assert attr.range_max == "2100-12-31"

    def test_range_datetime(self) -> None:
        """Parse @range with datetime (timestamp) values."""
        schema = parse_tql_schema("""
            define
            attribute event-time, value datetime @range(2020-01-01T00:00:00..2030-12-31T23:59:59);
        """)
        attr = schema.attributes["event-time"]
        assert attr.range_min == "2020-01-01T00:00:00"
        assert attr.range_max == "2030-12-31T23:59:59"

    def test_range_open_ended_min_only(self) -> None:
        """Parse @range with only minimum value (open-ended)."""
        schema = parse_tql_schema("""
            define
            attribute creation-timestamp, value datetime @range(1970-01-01T00:00:00..);
        """)
        attr = schema.attributes["creation-timestamp"]
        assert attr.range_min == "1970-01-01T00:00:00"
        assert attr.range_max is None

    def test_range_open_ended_integer(self) -> None:
        """Parse @range with only minimum integer value."""
        schema = parse_tql_schema("""
            define
            attribute score, value integer @range(0..);
        """)
        attr = schema.attributes["score"]
        assert attr.range_min == "0"
        assert attr.range_max is None


class TestParseCardOnPlays:
    """Tests for @card annotation on plays declarations."""

    def test_plays_with_card(self) -> None:
        """Parse plays with @card annotation."""
        schema = parse_tql_schema("""
            define
            entity person,
                owns name,
                plays friendship:friend @card(0..10);
            attribute name, value string;
            relation friendship, relates friend;
        """)
        entity = schema.entities["person"]
        assert "friendship:friend" in entity.plays
        assert "friendship:friend" in entity.plays_cardinalities
        card = entity.plays_cardinalities["friendship:friend"]
        assert card.min == 0
        assert card.max == 10

    def test_plays_unbounded_card(self) -> None:
        """Parse plays with unbounded @card."""
        schema = parse_tql_schema("""
            define
            entity person,
                plays friendship:friend @card(1..);
            relation friendship, relates friend;
        """)
        entity = schema.entities["person"]
        card = entity.plays_cardinalities["friendship:friend"]
        assert card.min == 1
        assert card.max is None

    def test_plays_without_card(self) -> None:
        """Parse plays without @card - no cardinality recorded."""
        schema = parse_tql_schema("""
            define
            entity person,
                plays friendship:friend;
            relation friendship, relates friend;
        """)
        entity = schema.entities["person"]
        assert "friendship:friend" in entity.plays
        assert "friendship:friend" not in entity.plays_cardinalities

    def test_plays_cardinality_inheritance(self) -> None:
        """Plays cardinalities should be inherited."""
        schema = parse_tql_schema("""
            define
            entity person @abstract,
                plays friendship:friend @card(0..5);
            entity employee sub person;
            relation friendship, relates friend;
        """)
        child = schema.entities["employee"]
        assert "friendship:friend" in child.plays
        assert "friendship:friend" in child.plays_cardinalities
        card = child.plays_cardinalities["friendship:friend"]
        assert card.min == 0
        assert card.max == 5


class TestParseCardOnRelates:
    """Tests for @card annotation on relates declarations in relations."""

    def test_relates_with_card(self) -> None:
        """Parse relates with @card annotation."""
        schema = parse_tql_schema("""
            define
            relation social-relation @abstract,
                relates related @card(0..);
        """)
        rel = schema.relations["social-relation"]
        assert len(rel.roles) == 1
        role = rel.roles[0]
        assert role.name == "related"
        assert role.cardinality is not None
        assert role.cardinality.min == 0
        assert role.cardinality.max is None

    def test_relates_with_card_bounded(self) -> None:
        """Parse relates with bounded @card annotation."""
        schema = parse_tql_schema("""
            define
            relation family,
                relates relative @card(0..1000);
        """)
        rel = schema.relations["family"]
        role = rel.roles[0]
        assert role.cardinality is not None
        assert role.cardinality.min == 0
        assert role.cardinality.max == 1000

    def test_relates_with_card_exact(self) -> None:
        """Parse relates with exact @card annotation."""
        schema = parse_tql_schema("""
            define
            relation parentship,
                relates parent @card(1..2),
                relates child @card(1..);
        """)
        rel = schema.relations["parentship"]

        parent_role = next(r for r in rel.roles if r.name == "parent")
        assert parent_role.cardinality is not None
        assert parent_role.cardinality.min == 1
        assert parent_role.cardinality.max == 2

        child_role = next(r for r in rel.roles if r.name == "child")
        assert child_role.cardinality is not None
        assert child_role.cardinality.min == 1
        assert child_role.cardinality.max is None

    def test_relates_with_overrides_and_card(self) -> None:
        """Parse relates with both 'as' override and @card annotation."""
        schema = parse_tql_schema("""
            define
            relation friendship,
                relates friend as related @card(0..100);
        """)
        rel = schema.relations["friendship"]
        role = rel.roles[0]
        assert role.name == "friend"
        assert role.overrides == "related"
        assert role.cardinality is not None
        assert role.cardinality.min == 0
        assert role.cardinality.max == 100

    def test_relates_without_card(self) -> None:
        """Parse relates without @card - no cardinality recorded."""
        schema = parse_tql_schema("""
            define
            relation viewing,
                relates viewer,
                relates viewed;
        """)
        rel = schema.relations["viewing"]
        for role in rel.roles:
            assert role.cardinality is None

    def test_relates_mixed_card(self) -> None:
        """Parse relation with some roles having @card and some not."""
        schema = parse_tql_schema("""
            define
            relation siblingship,
                relates sibling @card(2..),
                relates family;
        """)
        rel = schema.relations["siblingship"]

        sibling_role = next(r for r in rel.roles if r.name == "sibling")
        assert sibling_role.cardinality is not None
        assert sibling_role.cardinality.min == 2
        assert sibling_role.cardinality.max is None

        family_role = next(r for r in rel.roles if r.name == "family")
        assert family_role.cardinality is None


class TestParseComments:
    """Tests for comment handling."""

    def test_hash_comments(self) -> None:
        """Parse schema with # style comments."""
        schema = parse_tql_schema("""
            define
            # This is a hash comment
            attribute name, value string;
            entity person,
                owns name;  # inline comment
        """)
        assert "name" in schema.attributes
        assert "person" in schema.entities

    def test_cpp_style_comments(self) -> None:
        """Parse schema with // style comments."""
        schema = parse_tql_schema("""
            define
            // This is a C++ style comment
            attribute name, value string;
            entity person,
                owns name;  // inline comment
        """)
        assert "name" in schema.attributes
        assert "person" in schema.entities

    def test_mixed_comments(self) -> None:
        """Parse schema with both # and // style comments."""
        schema = parse_tql_schema("""
            define
            # Hash comment
            // C++ comment
            attribute name, value string;
            // Another C++ comment
            entity person,
                owns name;  # inline hash
        """)
        assert "name" in schema.attributes
        assert "person" in schema.entities

"""Tests for the code generator."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from type_bridge.generator import generate_models, parse_tql_schema
from type_bridge.generator.naming import build_class_name_map
from type_bridge.generator.render import (
    render_attributes,
    render_entities,
    render_package_init,
    render_relations,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"
BOOKSTORE_SCHEMA = FIXTURES_DIR / "bookstore.tql"


class TestRenderAttributes:
    """Tests for attribute rendering."""

    def test_simple_attribute(self) -> None:
        """Render a simple string attribute."""
        schema = parse_tql_schema("""
            define
            attribute name, value string;
        """)
        class_names = build_class_name_map(schema.attributes)
        source = render_attributes(schema, class_names)

        assert "class Name(String):" in source
        assert 'flags = AttributeFlags(name="name")' in source
        assert "from type_bridge import" in source

    def test_attribute_inheritance(self) -> None:
        """Render attributes with inheritance."""
        schema = parse_tql_schema("""
            define
            attribute isbn @abstract, value string;

            define
            attribute isbn-13 sub isbn;
        """)
        class_names = build_class_name_map(schema.attributes)
        source = render_attributes(schema, class_names)

        assert "class Isbn(String):" in source
        assert "class Isbn13(Isbn):" in source  # Inherits from Isbn, not String

    def test_attribute_with_constraints(self) -> None:
        """Render attribute with @regex and @values."""
        schema = parse_tql_schema("""
            define
            attribute status, value string @regex("^(active|inactive)$");
            attribute emoji, value string @values("like", "love");
        """)
        class_names = build_class_name_map(schema.attributes)
        source = render_attributes(schema, class_names)

        assert 'regex: ClassVar[str] = r"^(active|inactive)$"' in source
        assert 'allowed_values: ClassVar[tuple[str, ...]] = ("like", "love",)' in source

    def test_attribute_with_range(self) -> None:
        """Render attribute with @range constraint."""
        schema = parse_tql_schema("""
            define
            attribute age, value integer @range(0..150);
            attribute temperature, value double @range(-50.0..50.0);
        """)
        class_names = build_class_name_map(schema.attributes)
        source = render_attributes(schema, class_names)

        assert 'range_constraint: ClassVar[tuple[str | None, str | None]] = ("0", "150")' in source
        assert (
            'range_constraint: ClassVar[tuple[str | None, str | None]] = ("-50.0", "50.0")'
            in source
        )

    def test_attribute_with_open_range(self) -> None:
        """Render attribute with open-ended @range constraint."""
        schema = parse_tql_schema("""
            define
            attribute score, value integer @range(0..);
        """)
        class_names = build_class_name_map(schema.attributes)
        source = render_attributes(schema, class_names)

        assert 'range_constraint: ClassVar[tuple[str | None, str | None]] = ("0", None)' in source


class TestRenderEntities:
    """Tests for entity rendering."""

    def test_simple_entity(self) -> None:
        """Render a simple entity."""
        schema = parse_tql_schema("""
            define
            attribute name, value string;

            define
            entity person,
                owns name;
        """)
        attr_names = build_class_name_map(schema.attributes)
        entity_names = build_class_name_map(schema.entities)
        source = render_entities(schema, attr_names, entity_names)

        assert "class Person(Entity):" in source
        assert 'flags = TypeFlags(name="person")' in source
        assert "name: attributes.Name | None = None" in source

    def test_entity_with_key(self) -> None:
        """Render entity with @key attribute."""
        schema = parse_tql_schema("""
            define
            attribute id, value string;

            define
            entity user,
                owns id @key;
        """)
        attr_names = build_class_name_map(schema.attributes)
        entity_names = build_class_name_map(schema.entities)
        source = render_entities(schema, attr_names, entity_names)

        assert "id: attributes.Id = Flag(Key)" in source

    def test_entity_inheritance(self) -> None:
        """Render entity with inheritance."""
        schema = parse_tql_schema("""
            define
            attribute name, value string;

            define
            entity company @abstract,
                owns name;

            define
            entity publisher sub company;
        """)
        attr_names = build_class_name_map(schema.attributes)
        entity_names = build_class_name_map(schema.entities)
        source = render_entities(schema, attr_names, entity_names)

        assert "class Company(Entity):" in source
        assert "abstract=True" in source
        assert "class Publisher(Company):" in source  # Inherits from Company

    def test_entity_with_cardinality(self) -> None:
        """Render entity with various cardinalities."""
        schema = parse_tql_schema("""
            define
            attribute tag, value string;
            attribute title, value string;

            define
            entity article,
                owns title @card(1),
                owns tag @card(0..);
        """)
        attr_names = build_class_name_map(schema.attributes)
        entity_names = build_class_name_map(schema.entities)
        source = render_entities(schema, attr_names, entity_names)

        assert "title: attributes.Title" in source  # Required single
        assert "list[attributes.Tag]" in source  # Multi-value


class TestRenderRelations:
    """Tests for relation rendering."""

    def test_simple_relation(self) -> None:
        """Render a simple relation."""
        schema = parse_tql_schema("""
            define
            entity person,
                plays friendship:friend;

            define
            relation friendship,
                relates friend;
        """)
        attr_names = build_class_name_map(schema.attributes)
        entity_names = build_class_name_map(schema.entities)
        relation_names = build_class_name_map(schema.relations)
        source = render_relations(schema, attr_names, entity_names, relation_names)

        assert "class Friendship(Relation):" in source
        assert 'flags = TypeFlags(name="friendship")' in source
        assert "friend: Role[entities.Person]" in source

    def test_relation_with_owns(self) -> None:
        """Render relation that owns attributes."""
        schema = parse_tql_schema("""
            define
            attribute since, value datetime;
            entity person,
                plays friendship:friend;

            define
            relation friendship,
                relates friend,
                owns since;
        """)
        attr_names = build_class_name_map(schema.attributes)
        entity_names = build_class_name_map(schema.entities)
        relation_names = build_class_name_map(schema.relations)
        source = render_relations(schema, attr_names, entity_names, relation_names)

        assert "since: attributes.Since" in source


class TestRenderPackageInit:
    """Tests for package __init__.py rendering."""

    def test_basic_init(self) -> None:
        """Render basic __init__.py."""
        source = render_package_init(
            {"name": "Name"},
            {"person": "Person"},
            {"friendship": "Friendship"},
            schema_version="2.0.0",
        )

        assert 'SCHEMA_VERSION = "2.0.0"' in source
        assert "from . import attributes, entities, registry, relations" in source
        assert "attributes.Name," in source
        assert "entities.Person," in source
        assert "relations.Friendship," in source
        assert "def schema_text()" in source

    def test_without_schema_loader(self) -> None:
        """Render without schema_text helper."""
        source = render_package_init(
            {},
            {},
            {},
            include_schema_loader=False,
        )

        assert "def schema_text()" not in source
        assert "importlib" not in source


class TestGenerateModels:
    """Tests for the main generate_models function."""

    def test_generates_package(self) -> None:
        """Generate a complete package from schema text."""
        schema_text = """
            define
            attribute name, value string;

            define
            entity person,
                owns name @key;
        """

        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "models"
            generate_models(schema_text, output)

            # Check all files exist
            assert (output / "__init__.py").exists()
            assert (output / "attributes.py").exists()
            assert (output / "entities.py").exists()
            assert (output / "relations.py").exists()
            assert (output / "schema.tql").exists()

            # Check content is valid Python
            for py_file in output.glob("*.py"):
                content = py_file.read_text()
                compile(content, py_file.name, "exec")

    def test_generates_from_file(self) -> None:
        """Generate from a schema file path."""
        if not BOOKSTORE_SCHEMA.exists():
            pytest.skip("Bookstore schema fixture not found")

        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "bookstore"
            generate_models(BOOKSTORE_SCHEMA, output)

            # Check files exist
            assert (output / "__init__.py").exists()
            assert (output / "attributes.py").exists()
            assert (output / "entities.py").exists()
            assert (output / "relations.py").exists()

            # Verify generated code compiles
            for py_file in output.glob("*.py"):
                content = py_file.read_text()
                compile(content, py_file.name, "exec")


@pytest.mark.skipif(
    not BOOKSTORE_SCHEMA.exists(),
    reason="Bookstore schema fixture not found",
)
class TestBookstoreSchema:
    """Integration tests using the bookstore schema from TypeDB docs."""

    @pytest.fixture
    def bookstore_schema(self) -> str:
        """Load the bookstore schema."""
        return BOOKSTORE_SCHEMA.read_text()

    def test_parses_without_error(self, bookstore_schema: str) -> None:
        """The bookstore schema should parse completely."""
        schema = parse_tql_schema(bookstore_schema)

        # Check we got meaningful content
        assert len(schema.attributes) > 0
        assert len(schema.entities) > 0
        assert len(schema.relations) > 0

    def test_entity_inheritance(self, bookstore_schema: str) -> None:
        """Test entity inheritance in bookstore schema."""
        schema = parse_tql_schema(bookstore_schema)

        # book is abstract with subtypes
        assert "book" in schema.entities
        assert schema.entities["book"].abstract is True

        # hardback, paperback, ebook extend book
        for subtype in ["hardback", "paperback", "ebook"]:
            assert subtype in schema.entities
            assert schema.entities[subtype].parent == "book"

    def test_relation_inheritance(self, bookstore_schema: str) -> None:
        """Test relation inheritance in bookstore schema."""
        schema = parse_tql_schema(bookstore_schema)

        # contribution is parent of authoring, editing, illustrating
        assert "contribution" in schema.relations
        for subtype in ["authoring", "editing", "illustrating"]:
            assert subtype in schema.relations
            assert schema.relations[subtype].parent == "contribution"

    def test_generates_valid_code(self, bookstore_schema: str) -> None:
        """Generated code should compile."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "bookstore"
            generate_models(bookstore_schema, output)

            # All Python files should compile
            for py_file in output.glob("*.py"):
                content = py_file.read_text()
                compile(content, py_file.name, "exec")

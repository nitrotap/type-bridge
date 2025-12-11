"""Unit tests for registry generation."""

from __future__ import annotations

import tempfile
from pathlib import Path

from type_bridge.generator import generate_models, parse_tql_schema
from type_bridge.generator.naming import build_class_name_map
from type_bridge.generator.render.registry import render_registry


class TestRenderRegistry:
    """Tests for render_registry."""

    def test_basic_registry(self) -> None:
        """Render registry with basic types."""
        schema = parse_tql_schema("""
define
entity person, owns name @key;
attribute name, value string;
relation friendship, relates friend;
""")
        attr_names = build_class_name_map(schema.attributes)
        entity_names = build_class_name_map(schema.entities)
        relation_names = build_class_name_map(schema.relations)

        source = render_registry(
            schema,
            attr_names,
            entity_names,
            relation_names,
            schema_version="1.0.0",
        )

        # Check type collections
        assert "ENTITY_TYPES: tuple[str, ...] = (" in source
        assert '"person",' in source
        assert "RELATION_TYPES: tuple[str, ...] = (" in source
        assert '"friendship",' in source
        assert "ATTRIBUTE_TYPES: tuple[str, ...] = (" in source
        assert '"name",' in source

        # Check enums
        assert "class EntityType(StrEnum):" in source
        assert 'PERSON = "person"' in source
        assert "class RelationType(StrEnum):" in source
        assert 'FRIENDSHIP = "friendship"' in source

        # Check maps
        assert 'ENTITY_MAP: dict[str, type["Entity"]] = {' in source
        assert '"person": entities.Person,' in source

        # Check schema version
        assert 'SCHEMA_VERSION: str = "1.0.0"' in source

    def test_relation_roles(self) -> None:
        """Render relation role metadata."""
        schema = parse_tql_schema("""
define
entity person, owns name, plays friendship:friend;
attribute name, value string;
relation friendship, relates friend;
""")
        attr_names = build_class_name_map(schema.attributes)
        entity_names = build_class_name_map(schema.entities)
        relation_names = build_class_name_map(schema.relations)

        source = render_registry(
            schema,
            attr_names,
            entity_names,
            relation_names,
        )

        assert "RELATION_ROLES: dict[str, dict[str, RoleInfo]] = {" in source
        assert '"friendship": {' in source
        assert 'RoleInfo("friend"' in source
        assert '"person"' in source  # Player type

    def test_entity_attributes(self) -> None:
        """Render entity attribute ownership."""
        schema = parse_tql_schema("""
define
entity person, owns name @key, owns age;
attribute name, value string;
attribute age, value integer;
""")
        attr_names = build_class_name_map(schema.attributes)
        entity_names = build_class_name_map(schema.entities)
        relation_names = build_class_name_map(schema.relations)

        source = render_registry(
            schema,
            attr_names,
            entity_names,
            relation_names,
        )

        assert "ENTITY_ATTRIBUTES: dict[str, frozenset[str]] = {" in source
        assert '"person": frozenset({' in source
        assert '"age"' in source
        assert '"name"' in source

        assert "ENTITY_KEYS: dict[str, frozenset[str]] = {" in source
        assert '"name"' in source

    def test_attribute_value_types(self) -> None:
        """Render attribute value type mappings."""
        schema = parse_tql_schema("""
define
attribute name, value string;
attribute age, value integer;
attribute score, value double;
attribute active, value boolean;
""")
        attr_names = build_class_name_map(schema.attributes)

        source = render_registry(
            schema,
            attr_names,
            {},
            {},
        )

        assert "ATTRIBUTE_VALUE_TYPES: dict[str, str] = {" in source
        assert '"name": "string"' in source
        assert '"age": "integer"' in source
        assert '"score": "double"' in source
        assert '"active": "boolean"' in source

    def test_inheritance_metadata(self) -> None:
        """Render inheritance parent mappings."""
        schema = parse_tql_schema("""
define
entity artifact @abstract, owns name;
entity project sub artifact, owns description;
attribute name, value string;
attribute description, value string;
""")
        attr_names = build_class_name_map(schema.attributes)
        entity_names = build_class_name_map(schema.entities)
        relation_names = build_class_name_map(schema.relations)

        source = render_registry(
            schema,
            attr_names,
            entity_names,
            relation_names,
        )

        assert "ENTITY_PARENTS: dict[str, str | None] = {" in source
        assert '"artifact": None,' in source
        assert '"project": "artifact",' in source

        assert "ENTITY_ABSTRACT: frozenset[str] = frozenset({" in source
        assert '"artifact",' in source

    def test_annotations(self) -> None:
        """Render custom annotations."""
        schema = parse_tql_schema("""
define
# @prefix(PROJ)
# @searchable
entity project, owns name;
# @default(active)
attribute name, value string;
""")
        attr_names = build_class_name_map(schema.attributes)
        entity_names = build_class_name_map(schema.entities)
        relation_names = build_class_name_map(schema.relations)

        source = render_registry(
            schema,
            attr_names,
            entity_names,
            relation_names,
        )

        assert (
            "ENTITY_ANNOTATIONS: dict[str, dict[str, bool | int | float | str | list]] = {"
            in source
        )
        assert '"project": {' in source
        assert '"prefix": "PROJ"' in source
        assert '"searchable": True' in source

        assert (
            "ATTRIBUTE_ANNOTATIONS: dict[str, dict[str, bool | int | float | str | list]] = {"
            in source
        )
        assert '"name": {' in source
        assert '"default": "active"' in source

    def test_json_schema_fragments(self) -> None:
        """Render JSON schema fragments."""
        schema = parse_tql_schema("""
define
entity person;
""")
        attr_names = build_class_name_map(schema.attributes)
        entity_names = build_class_name_map(schema.entities)
        relation_names = build_class_name_map(schema.relations)

        source = render_registry(
            schema,
            attr_names,
            entity_names,
            relation_names,
        )

        assert "ENTITY_TYPE_JSON_SCHEMA: dict = {" in source
        assert '"type": "string"' in source
        assert '"enum": list(ENTITY_TYPES)' in source

    def test_convenience_functions(self) -> None:
        """Render convenience functions."""
        schema = parse_tql_schema("""
define
entity person;
""")
        attr_names = build_class_name_map(schema.attributes)
        entity_names = build_class_name_map(schema.entities)
        relation_names = build_class_name_map(schema.relations)

        source = render_registry(
            schema,
            attr_names,
            entity_names,
            relation_names,
        )

        assert "def get_entity_class(type_name: str)" in source
        assert "def get_relation_class(type_name: str)" in source
        assert "def get_attribute_class(type_name: str)" in source
        assert "def get_role_players(relation_type: str, role_name: str)" in source
        assert "def get_entity_attributes(entity_type: str)" in source
        assert "def is_abstract_entity(entity_type: str)" in source

    def test_schema_hash(self) -> None:
        """Render schema hash when text provided."""
        schema = parse_tql_schema("""
define
entity person;
""")

        source = render_registry(
            schema,
            {},
            {"person": "Person"},
            {},
            schema_text="define\nentity person;",
        )

        assert 'SCHEMA_HASH: str = "sha256:' in source

    def test_generated_code_compiles(self) -> None:
        """Generated registry code compiles."""
        schema = parse_tql_schema("""
define
entity person, owns name @key, plays friendship:friend;
entity organization, owns name @key;
attribute name, value string;
relation friendship, relates friend;
""")
        attr_names = build_class_name_map(schema.attributes)
        entity_names = build_class_name_map(schema.entities)
        relation_names = build_class_name_map(schema.relations)

        source = render_registry(
            schema,
            attr_names,
            entity_names,
            relation_names,
        )

        # Should compile without errors
        compile(source, "registry.py", "exec")


class TestGenerateModelsWithRegistry:
    """Integration tests for generate_models with registry."""

    def test_generates_registry_file(self) -> None:
        """generate_models creates registry.py."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "models"

            generate_models(
                """
define
entity person, owns name @key;
attribute name, value string;
""",
                output,
            )

            assert (output / "registry.py").exists()

            # Check registry imports work
            init_content = (output / "__init__.py").read_text()
            assert "registry" in init_content

    def test_registry_code_is_valid(self) -> None:
        """Generated registry compiles and runs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "models"

            generate_models(
                """
define
# @prefix(P)
entity person, owns name @key, plays friendship:friend;
attribute name, value string;
relation friendship, relates friend;
""",
                output,
            )

            # Compile all modules
            for filename in ["registry.py", "attributes.py", "entities.py", "relations.py"]:
                content = (output / filename).read_text()
                compile(content, filename, "exec")

            # Check registry has expected content
            registry_content = (output / "registry.py").read_text()
            assert "ENTITY_TYPES" in registry_content
            assert "EntityType" in registry_content
            assert "ENTITY_MAP" in registry_content
            assert "RELATION_ROLES" in registry_content
            assert '"prefix": "P"' in registry_content

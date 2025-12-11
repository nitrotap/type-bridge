"""Render registry.py with pre-computed schema metadata.

The registry provides static, type-safe access to schema metadata without
runtime introspection. It includes:

- Type name collections (tuples and StrEnums)
- Type-to-class mappings
- Relation role metadata
- Entity attribute ownership
- Attribute value types
- Custom annotations from TQL comments
- Convenience lookup functions
- JSON schema fragments for LLM tools
"""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

from ..models import minimal_role_players

if TYPE_CHECKING:
    from ..models import AnnotationValue, ParsedSchema


def _render_annotation_value(value: AnnotationValue) -> str:
    """Render an annotation value as Python literal."""
    if isinstance(value, bool):
        return "True" if value else "False"
    elif isinstance(value, str):
        # Escape quotes and backslashes
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    elif isinstance(value, (int, float)):
        return repr(value)
    elif isinstance(value, list):
        items = ", ".join(_render_annotation_value(v) for v in value)
        return f"[{items}]"
    else:
        return repr(value)


def _render_annotations_dict(
    annotations: dict[str, dict[str, AnnotationValue]],
    indent: int = 4,
) -> list[str]:
    """Render a nested annotations dict as Python code."""
    lines: list[str] = []
    base_indent = " " * indent
    inner_indent = " " * (indent + 4)

    if not annotations:
        lines.append(f"{base_indent}# (none)")
        return lines

    for name in sorted(annotations.keys()):
        annots = annotations[name]
        if not annots:
            continue
        lines.append(f'{base_indent}"{name}": {{')
        for key, value in sorted(annots.items()):
            lines.append(f'{inner_indent}"{key}": {_render_annotation_value(value)},')
        lines.append(f"{base_indent}}},")

    return lines


def render_registry(
    schema: ParsedSchema,
    attr_class_names: dict[str, str],
    entity_class_names: dict[str, str],
    relation_class_names: dict[str, str],
    *,
    schema_version: str = "1.0.0",
    schema_text: str | None = None,
) -> str:
    """Render the registry.py module source.

    Args:
        schema: Parsed schema with all type information
        attr_class_names: Mapping from TypeDB attr names to Python class names
        entity_class_names: Mapping from TypeDB entity names to Python class names
        relation_class_names: Mapping from TypeDB relation names to Python class names
        schema_version: Version string for SCHEMA_VERSION constant
        schema_text: Original schema text for hash computation

    Returns:
        Complete Python source code for registry.py
    """
    lines: list[str] = [
        '"""TypeBridge registry - Pre-computed schema metadata.',
        "",
        "This module provides static, type-safe access to schema information",
        "without runtime introspection. All data is computed at generation time.",
        '"""',
        "",
        "from __future__ import annotations",
        "",
        "from dataclasses import dataclass",
        "from enum import StrEnum",
        "from typing import TYPE_CHECKING",
        "",
        "from . import attributes, entities, relations",
        "",
        "if TYPE_CHECKING:",
        "    from type_bridge import Attribute, Entity, Relation",
        "",
    ]

    # ==========================================================================
    # SCHEMA METADATA
    # ==========================================================================
    lines.extend(
        [
            "# " + "=" * 70,
            "# SCHEMA METADATA",
            "# " + "=" * 70,
            "",
            f'SCHEMA_VERSION: str = "{schema_version}"',
        ]
    )

    if schema_text:
        schema_hash = hashlib.sha256(schema_text.encode("utf-8")).hexdigest()[:16]
        lines.append(f'SCHEMA_HASH: str = "sha256:{schema_hash}"')
    else:
        lines.append('SCHEMA_HASH: str = ""')

    lines.append("")

    # ==========================================================================
    # TYPE NAME COLLECTIONS
    # ==========================================================================
    lines.extend(
        [
            "# " + "=" * 70,
            "# TYPE NAME COLLECTIONS",
            "# " + "=" * 70,
            "",
        ]
    )

    # ENTITY_TYPES tuple
    entity_names = sorted(schema.entities.keys())
    lines.append("ENTITY_TYPES: tuple[str, ...] = (")
    for name in entity_names:
        lines.append(f'    "{name}",')
    lines.append(")")
    lines.append("")

    # RELATION_TYPES tuple
    relation_names = sorted(schema.relations.keys())
    lines.append("RELATION_TYPES: tuple[str, ...] = (")
    for name in relation_names:
        lines.append(f'    "{name}",')
    lines.append(")")
    lines.append("")

    # ATTRIBUTE_TYPES tuple
    attribute_names = sorted(schema.attributes.keys())
    lines.append("ATTRIBUTE_TYPES: tuple[str, ...] = (")
    for name in attribute_names:
        lines.append(f'    "{name}",')
    lines.append(")")
    lines.append("")

    # ==========================================================================
    # TYPE NAME ENUMS
    # ==========================================================================
    lines.extend(
        [
            "# " + "=" * 70,
            "# TYPE NAME ENUMS (for API validation, Pydantic models)",
            "# " + "=" * 70,
            "",
        ]
    )

    # EntityType enum
    lines.append("class EntityType(StrEnum):")
    lines.append('    """Enum of all entity type names."""')
    if entity_names:
        for name in entity_names:
            enum_name = name.upper().replace("-", "_")
            lines.append(f'    {enum_name} = "{name}"')
    else:
        lines.append("    pass")
    lines.append("")
    lines.append("")

    # RelationType enum
    lines.append("class RelationType(StrEnum):")
    lines.append('    """Enum of all relation type names."""')
    if relation_names:
        for name in relation_names:
            enum_name = name.upper().replace("-", "_")
            lines.append(f'    {enum_name} = "{name}"')
    else:
        lines.append("    pass")
    lines.append("")
    lines.append("")

    # AttributeType enum
    lines.append("class AttributeType(StrEnum):")
    lines.append('    """Enum of all attribute type names."""')
    if attribute_names:
        for name in attribute_names:
            enum_name = name.upper().replace("-", "_")
            lines.append(f'    {enum_name} = "{name}"')
    else:
        lines.append("    pass")
    lines.append("")

    # ==========================================================================
    # TYPE-TO-CLASS MAPPINGS
    # ==========================================================================
    lines.extend(
        [
            "# " + "=" * 70,
            "# TYPE-TO-CLASS MAPPINGS",
            "# " + "=" * 70,
            "",
        ]
    )

    # ENTITY_MAP
    lines.append('ENTITY_MAP: dict[str, type["Entity"]] = {')
    for name in entity_names:
        class_name = entity_class_names[name]
        lines.append(f'    "{name}": entities.{class_name},')
    lines.append("}")
    lines.append("")

    # RELATION_MAP
    lines.append('RELATION_MAP: dict[str, type["Relation"]] = {')
    for name in relation_names:
        class_name = relation_class_names[name]
        lines.append(f'    "{name}": relations.{class_name},')
    lines.append("}")
    lines.append("")

    # ATTRIBUTE_MAP
    lines.append('ATTRIBUTE_MAP: dict[str, type["Attribute"]] = {')
    for name in attribute_names:
        class_name = attr_class_names[name]
        lines.append(f'    "{name}": attributes.{class_name},')
    lines.append("}")
    lines.append("")

    # ==========================================================================
    # RELATION ROLE METADATA
    # ==========================================================================
    lines.extend(
        [
            "# " + "=" * 70,
            "# RELATION ROLE METADATA",
            "# " + "=" * 70,
            "",
            "@dataclass(frozen=True, slots=True)",
            "class RoleInfo:",
            '    """Metadata for a relation role."""',
            "",
            "    role_name: str",
            "    player_types: tuple[str, ...]",
            "",
            "",
        ]
    )

    # RELATION_ROLES dict
    lines.append("RELATION_ROLES: dict[str, dict[str, RoleInfo]] = {")
    for rel_name in relation_names:
        relation = schema.relations[rel_name]
        if not relation.roles:
            continue
        lines.append(f'    "{rel_name}": {{')
        for role in relation.roles:
            players = minimal_role_players(schema, rel_name, role.name)
            players_tuple = ", ".join(f'"{p}"' for p in players)
            if len(players) == 1:
                players_tuple += ","
            lines.append(f'        "{role.name}": RoleInfo("{role.name}", ({players_tuple})),')
        lines.append("    },")
    lines.append("}")
    lines.append("")

    # ==========================================================================
    # ENTITY ATTRIBUTE METADATA
    # ==========================================================================
    lines.extend(
        [
            "# " + "=" * 70,
            "# ENTITY ATTRIBUTE METADATA",
            "# " + "=" * 70,
            "",
        ]
    )

    # ENTITY_ATTRIBUTES - all owned attributes per entity
    lines.append("ENTITY_ATTRIBUTES: dict[str, frozenset[str]] = {")
    for name in entity_names:
        entity = schema.entities[name]
        if entity.owns:
            attrs = ", ".join(f'"{a}"' for a in sorted(entity.owns))
            lines.append(f'    "{name}": frozenset({{{attrs}}}),')
        else:
            lines.append(f'    "{name}": frozenset(),')
    lines.append("}")
    lines.append("")

    # ENTITY_KEYS - key attributes per entity
    lines.append("ENTITY_KEYS: dict[str, frozenset[str]] = {")
    for name in entity_names:
        entity = schema.entities[name]
        if entity.keys:
            keys = ", ".join(f'"{k}"' for k in sorted(entity.keys))
            lines.append(f'    "{name}": frozenset({{{keys}}}),')
    lines.append("}")
    lines.append("")

    # ==========================================================================
    # ATTRIBUTE VALUE TYPES
    # ==========================================================================
    lines.extend(
        [
            "# " + "=" * 70,
            "# ATTRIBUTE VALUE TYPES",
            "# " + "=" * 70,
            "",
        ]
    )

    lines.append("ATTRIBUTE_VALUE_TYPES: dict[str, str] = {")
    for name in attribute_names:
        attr = schema.attributes[name]
        if attr.value_type:
            lines.append(f'    "{name}": "{attr.value_type}",')
    lines.append("}")
    lines.append("")

    # ==========================================================================
    # INHERITANCE METADATA
    # ==========================================================================
    lines.extend(
        [
            "# " + "=" * 70,
            "# INHERITANCE METADATA",
            "# " + "=" * 70,
            "",
        ]
    )

    # ENTITY_PARENTS
    lines.append("ENTITY_PARENTS: dict[str, str | None] = {")
    for name in entity_names:
        entity = schema.entities[name]
        if entity.parent:
            lines.append(f'    "{name}": "{entity.parent}",')
        else:
            lines.append(f'    "{name}": None,')
    lines.append("}")
    lines.append("")

    # RELATION_PARENTS
    lines.append("RELATION_PARENTS: dict[str, str | None] = {")
    for name in relation_names:
        relation = schema.relations[name]
        if relation.parent:
            lines.append(f'    "{name}": "{relation.parent}",')
        else:
            lines.append(f'    "{name}": None,')
    lines.append("}")
    lines.append("")

    # ENTITY_ABSTRACT
    lines.append("ENTITY_ABSTRACT: frozenset[str] = frozenset({")
    abstract_entities = [n for n in entity_names if schema.entities[n].abstract]
    for name in abstract_entities:
        lines.append(f'    "{name}",')
    lines.append("})")
    lines.append("")

    # RELATION_ABSTRACT
    lines.append("RELATION_ABSTRACT: frozenset[str] = frozenset({")
    abstract_relations = [n for n in relation_names if schema.relations[n].abstract]
    for name in abstract_relations:
        lines.append(f'    "{name}",')
    lines.append("})")
    lines.append("")

    # ==========================================================================
    # CUSTOM ANNOTATIONS
    # ==========================================================================
    lines.extend(
        [
            "# " + "=" * 70,
            "# CUSTOM ANNOTATIONS (from TQL comments)",
            "# " + "=" * 70,
            "",
        ]
    )

    # Collect annotations
    entity_annotations = {
        name: dict(spec.annotations) for name, spec in schema.entities.items() if spec.annotations
    }
    attribute_annotations = {
        name: dict(spec.annotations) for name, spec in schema.attributes.items() if spec.annotations
    }
    relation_annotations = {
        name: dict(spec.annotations) for name, spec in schema.relations.items() if spec.annotations
    }

    # ENTITY_ANNOTATIONS
    lines.append("ENTITY_ANNOTATIONS: dict[str, dict[str, bool | int | float | str | list]] = {")
    lines.extend(_render_annotations_dict(entity_annotations))
    lines.append("}")
    lines.append("")

    # ATTRIBUTE_ANNOTATIONS
    lines.append("ATTRIBUTE_ANNOTATIONS: dict[str, dict[str, bool | int | float | str | list]] = {")
    lines.extend(_render_annotations_dict(attribute_annotations))
    lines.append("}")
    lines.append("")

    # RELATION_ANNOTATIONS
    lines.append("RELATION_ANNOTATIONS: dict[str, dict[str, bool | int | float | str | list]] = {")
    lines.extend(_render_annotations_dict(relation_annotations))
    lines.append("}")
    lines.append("")

    # ==========================================================================
    # JSON SCHEMA FRAGMENTS
    # ==========================================================================
    lines.extend(
        [
            "# " + "=" * 70,
            "# JSON SCHEMA FRAGMENTS (for LLM tools, OpenAPI)",
            "# " + "=" * 70,
            "",
        ]
    )

    lines.append("ENTITY_TYPE_JSON_SCHEMA: dict = {")
    lines.append('    "type": "string",')
    lines.append('    "enum": list(ENTITY_TYPES),')
    lines.append('    "description": "Valid entity type names",')
    lines.append("}")
    lines.append("")

    lines.append("RELATION_TYPE_JSON_SCHEMA: dict = {")
    lines.append('    "type": "string",')
    lines.append('    "enum": list(RELATION_TYPES),')
    lines.append('    "description": "Valid relation type names",')
    lines.append("}")
    lines.append("")

    lines.append("ATTRIBUTE_TYPE_JSON_SCHEMA: dict = {")
    lines.append('    "type": "string",')
    lines.append('    "enum": list(ATTRIBUTE_TYPES),')
    lines.append('    "description": "Valid attribute type names",')
    lines.append("}")
    lines.append("")

    # ==========================================================================
    # CONVENIENCE FUNCTIONS
    # ==========================================================================
    lines.extend(
        [
            "# " + "=" * 70,
            "# CONVENIENCE FUNCTIONS",
            "# " + "=" * 70,
            "",
            "",
            'def get_entity_class(type_name: str) -> type["Entity"] | None:',
            '    """Get entity class by TypeDB type name."""',
            "    return ENTITY_MAP.get(type_name)",
            "",
            "",
            'def get_relation_class(type_name: str) -> type["Relation"] | None:',
            '    """Get relation class by TypeDB type name."""',
            "    return RELATION_MAP.get(type_name)",
            "",
            "",
            'def get_attribute_class(type_name: str) -> type["Attribute"] | None:',
            '    """Get attribute class by TypeDB type name."""',
            "    return ATTRIBUTE_MAP.get(type_name)",
            "",
            "",
            "def get_role_players(relation_type: str, role_name: str) -> tuple[str, ...]:",
            '    """Get allowed player entity types for a relation role."""',
            "    roles = RELATION_ROLES.get(relation_type, {})",
            "    role_info = roles.get(role_name)",
            "    return role_info.player_types if role_info else ()",
            "",
            "",
            "def get_entity_attributes(entity_type: str) -> frozenset[str]:",
            '    """Get attribute names owned by an entity type."""',
            "    return ENTITY_ATTRIBUTES.get(entity_type, frozenset())",
            "",
            "",
            "def get_entity_keys(entity_type: str) -> frozenset[str]:",
            '    """Get key attribute names for an entity type."""',
            "    return ENTITY_KEYS.get(entity_type, frozenset())",
            "",
            "",
            "def is_abstract_entity(entity_type: str) -> bool:",
            '    """Check if an entity type is abstract."""',
            "    return entity_type in ENTITY_ABSTRACT",
            "",
            "",
            "def is_abstract_relation(relation_type: str) -> bool:",
            '    """Check if a relation type is abstract."""',
            "    return relation_type in RELATION_ABSTRACT",
            "",
        ]
    )

    # ==========================================================================
    # __all__ EXPORT
    # ==========================================================================
    all_exports = [
        # Metadata
        "SCHEMA_VERSION",
        "SCHEMA_HASH",
        # Collections
        "ENTITY_TYPES",
        "RELATION_TYPES",
        "ATTRIBUTE_TYPES",
        # Enums
        "EntityType",
        "RelationType",
        "AttributeType",
        # Maps
        "ENTITY_MAP",
        "RELATION_MAP",
        "ATTRIBUTE_MAP",
        # Role metadata
        "RoleInfo",
        "RELATION_ROLES",
        # Entity metadata
        "ENTITY_ATTRIBUTES",
        "ENTITY_KEYS",
        # Attribute metadata
        "ATTRIBUTE_VALUE_TYPES",
        # Inheritance
        "ENTITY_PARENTS",
        "RELATION_PARENTS",
        "ENTITY_ABSTRACT",
        "RELATION_ABSTRACT",
        # Annotations
        "ENTITY_ANNOTATIONS",
        "ATTRIBUTE_ANNOTATIONS",
        "RELATION_ANNOTATIONS",
        # JSON schemas
        "ENTITY_TYPE_JSON_SCHEMA",
        "RELATION_TYPE_JSON_SCHEMA",
        "ATTRIBUTE_TYPE_JSON_SCHEMA",
        # Functions
        "get_entity_class",
        "get_relation_class",
        "get_attribute_class",
        "get_role_players",
        "get_entity_attributes",
        "get_entity_keys",
        "is_abstract_entity",
        "is_abstract_relation",
    ]

    lines.append("")
    lines.append("__all__ = [")
    for export in all_exports:
        lines.append(f'    "{export}",')
    lines.append("]")

    return "\n".join(lines) + "\n"

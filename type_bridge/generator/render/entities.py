"""Render entity class definitions from parsed schema."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ..naming import render_all_export, to_python_name

if TYPE_CHECKING:
    from ..models import Cardinality, ParsedSchema

logger = logging.getLogger(__name__)


def _render_attr_field(
    attr_name: str,
    attr_class: str,
    is_key: bool,
    is_unique: bool,
    cardinality: Cardinality | None,
) -> str:
    """Render a single attribute field declaration.

    Returns a string like:
    - "    name: attributes.Name = Flag(Key)"
    - "    age: attributes.Age | None = None"
    - "    tags: list[attributes.Tag] = Flag(Card(min=0))"
    """
    py_name = to_python_name(attr_name)

    if is_key:
        return f"    {py_name}: attributes.{attr_class} = Flag(Key)"

    if is_unique:
        return f"    {py_name}: attributes.{attr_class} = Flag(Unique)"

    # Handle cardinality
    if cardinality is None or cardinality.is_optional_single:
        return f"    {py_name}: attributes.{attr_class} | None = None"

    if cardinality.is_multi:
        # Multi-value attributes require Flag(Card(...))
        if cardinality.max is None:
            # Unbounded: @card(min..)
            return (
                f"    {py_name}: list[attributes.{attr_class}] = Flag(Card(min={cardinality.min}))"
            )
        # Bounded: @card(min..max)
        return f"    {py_name}: list[attributes.{attr_class}] = Flag(Card({cardinality.min}, {cardinality.max}))"

    # Single required value
    if cardinality.is_required and cardinality.is_single:
        return f"    {py_name}: attributes.{attr_class}"

    return f"    {py_name}: attributes.{attr_class} | None = None"


def _render_plays_tuple(plays: set[str]) -> list[str]:
    """Render plays ClassVar as multi-line tuple for readability."""
    if not plays:
        return []

    sorted_plays = sorted(plays)
    if len(sorted_plays) == 1:
        return [f'    plays: ClassVar[tuple[str, ...]] = ("{sorted_plays[0]}",)']

    lines = ["    plays: ClassVar[tuple[str, ...]] = ("]
    for play in sorted_plays:
        lines.append(f'        "{play}",')
    lines.append("    )")
    return lines


def _render_entity_class(
    entity_name: str,
    schema: ParsedSchema,
    attr_class_names: dict[str, str],
    entity_class_names: dict[str, str],
    implicit_keys: set[str],
) -> list[str]:
    """Render a single entity class definition."""
    entity = schema.entities[entity_name]
    cls_name = entity_class_names[entity_name]

    # Determine base class
    if entity.parent and entity.parent in entity_class_names:
        base_class = entity_class_names[entity.parent]
    else:
        base_class = "Entity"

    lines: list[str] = []
    lines.append(f"class {cls_name}({base_class}):")

    # Docstring
    if entity.docstring:
        lines.append(f'    """{entity.docstring}"""')
    else:
        lines.append(f'    """Entity generated from `{entity_name}`."""')

    # TypeFlags
    flag_args = [f'name="{entity_name}"']
    if entity.abstract:
        flag_args.append("abstract=True")
    lines.append(f"    flags = TypeFlags({', '.join(flag_args)})")

    # Prefix (legacy custom annotation)
    if entity.prefix:
        lines.append(f'    prefix: ClassVar[str] = "{entity.prefix}"')

    # Plays tuple
    if entity.plays:
        lines.extend(_render_plays_tuple(entity.plays))

    # Attributes - only render those not inherited from parent
    parent_owns = set()
    if entity.parent and entity.parent in schema.entities:
        parent_owns = schema.entities[entity.parent].owns

    own_attrs = [a for a in entity.owns_order if a not in parent_owns]
    key_attrs = (entity.keys | implicit_keys) & entity.owns
    unique_attrs = entity.uniques & entity.owns

    for attr in own_attrs:
        if attr not in attr_class_names:
            continue
        attr_class = attr_class_names[attr]
        cardinality = entity.cardinalities.get(attr)
        lines.append(
            _render_attr_field(
                attr_name=attr,
                attr_class=attr_class,
                is_key=attr in key_attrs,
                is_unique=attr in unique_attrs,
                cardinality=cardinality,
            )
        )

    lines.append("")
    lines.append("")

    return lines


def _topological_sort_entities(schema: ParsedSchema) -> list[str]:
    """Sort entities so parents come before children."""
    result: list[str] = []
    visited: set[str] = set()

    def visit(name: str) -> None:
        if name in visited or name not in schema.entities:
            return
        visited.add(name)

        entity = schema.entities[name]
        if entity.parent and entity.parent in schema.entities:
            visit(entity.parent)

        result.append(name)

    for name in schema.entities:
        visit(name)

    return result


def _needs_card_import(schema: ParsedSchema) -> bool:
    """Check if any entity uses multi-valued attributes requiring Card."""
    return any(
        card.is_multi
        for entity in schema.entities.values()
        for card in entity.cardinalities.values()
    )


def render_entities(
    schema: ParsedSchema,
    attr_class_names: dict[str, str],
    entity_class_names: dict[str, str],
    implicit_key_attributes: set[str] | None = None,
) -> str:
    """Render the complete entities module source.

    Args:
        schema: Parsed schema containing entity definitions
        attr_class_names: Mapping from TypeDB attr names to Python class names
        entity_class_names: Mapping from TypeDB entity names to Python class names
        implicit_key_attributes: Attributes to treat as keys even without @key

    Returns:
        Complete Python source code for entities.py
    """
    logger.debug(f"Rendering {len(schema.entities)} entity classes")
    implicit_keys = implicit_key_attributes or set()
    needs_card = _needs_card_import(schema)

    # Build header
    lines: list[str] = [
        '"""Entity type definitions generated from a TypeDB schema."""',
        "",
        "from typing import ClassVar",
        "",
    ]

    # Build type_bridge imports
    imports = ["Entity", "Flag", "Key", "TypeFlags", "Unique"]
    if needs_card:
        imports.insert(1, "Card")  # Insert after Entity alphabetically
    lines.append(f"from type_bridge import {', '.join(imports)}")
    lines.append("")
    lines.append("from . import attributes")
    lines.append("")
    lines.append("")

    # Render classes in topological order
    rendered_names: list[str] = []
    for entity_name in _topological_sort_entities(schema):
        rendered_names.append(entity_class_names[entity_name])
        lines.extend(
            _render_entity_class(
                entity_name,
                schema,
                attr_class_names,
                entity_class_names,
                implicit_keys,
            )
        )

    # Add __all__ export
    lines.extend(render_all_export(rendered_names))

    logger.info(f"Rendered {len(rendered_names)} entity classes")
    return "\n".join(lines)

"""Render package __init__.py with exports and schema utilities."""

from __future__ import annotations


def render_package_init(
    attr_class_names: dict[str, str],
    entity_class_names: dict[str, str],
    relation_class_names: dict[str, str],
    *,
    schema_version: str = "1.0.0",
    include_schema_loader: bool = True,
    functions_present: bool = False,
) -> str:
    """Render the package __init__.py source.

    Args:
        attr_class_names: Mapping from TypeDB attr names to Python class names
        entity_class_names: Mapping from TypeDB entity names to Python class names
        relation_class_names: Mapping from TypeDB relation names to Python class names
        schema_version: Version string for SCHEMA_VERSION constant
        include_schema_loader: Whether to include schema_text() helper
        functions_present: Whether to export functions module

    Returns:
        Complete Python source code for __init__.py
    """
    lines: list[str] = [
        '"""TypeBridge schema package generated from a TypeDB schema."""',
        "",
        "from __future__ import annotations",
        "",
    ]

    if include_schema_loader:
        lines.extend(
            [
                "from importlib import resources",
                "",
            ]
        )

    imports = ["attributes", "entities", "relations"]
    if functions_present:
        imports.append("functions")

    lines.extend(
        [
            f"from . import {', '.join(imports)}",
            "",
            f'SCHEMA_VERSION = "{schema_version}"',
            "",
            "",
        ]
    )

    if include_schema_loader:
        lines.extend(
            [
                "def schema_text() -> str:",
                '    """Return the canonical TypeDB schema text bundled with the package."""',
                "    return (",
                "        resources.files(__package__)",
                '        .joinpath("schema.tql")',
                '        .read_text(encoding="utf-8")',
                "    )",
                "",
                "",
            ]
        )

    # ATTRIBUTES list
    lines.append("ATTRIBUTES = [")
    for name in sorted(attr_class_names):
        lines.append(f"    attributes.{attr_class_names[name]},")
    lines.append("]")
    lines.append("")

    # ENTITIES list
    lines.append("ENTITIES = [")
    for name in sorted(entity_class_names):
        lines.append(f"    entities.{entity_class_names[name]},")
    lines.append("]")
    lines.append("")

    # RELATIONS list
    lines.append("RELATIONS = [")
    for name in sorted(relation_class_names):
        lines.append(f"    relations.{relation_class_names[name]},")
    lines.append("]")
    lines.append("")

    # __all__ export
    all_exports = [
        "ATTRIBUTES",
        "ENTITIES",
        "RELATIONS",
        "SCHEMA_VERSION",
        "attributes",
        "entities",
        "relations",
    ]
    if functions_present:
        all_exports.append("functions")

    if include_schema_loader:
        all_exports.append("schema_text")

    lines.append("__all__ = [")
    for export in sorted(all_exports):
        lines.append(f'    "{export}",')
    lines.append("]")

    return "\n".join(lines) + "\n"

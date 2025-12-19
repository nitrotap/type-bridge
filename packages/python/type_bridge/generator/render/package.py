"""Render package __init__.py with exports and schema utilities."""

from __future__ import annotations

from .template_loader import get_template


def render_package_init(
    attr_class_names: dict[str, str],
    entity_class_names: dict[str, str],
    relation_class_names: dict[str, str],
    *,
    schema_version: str = "1.0.0",
    include_schema_loader: bool = True,
    schema_filename: str | None = "schema.tql",
    functions_present: bool = False,
) -> str:
    """Render the package __init__.py source.

    Args:
        attr_class_names: Mapping from TypeDB attr names to Python class names
        entity_class_names: Mapping from TypeDB entity names to Python class names
        relation_class_names: Mapping from TypeDB relation names to Python class names
        schema_version: Version string for SCHEMA_VERSION constant
        include_schema_loader: Whether to include schema_text() helper
        schema_filename: Filename for the schema file (used in schema_text() loader)
        functions_present: Whether to export functions module

    Returns:
        Complete Python source code for __init__.py
    """
    # Don't include loader if no filename provided
    if schema_filename is None:
        include_schema_loader = False

    module_imports = ["attributes", "entities", "registry", "relations"]
    if functions_present:
        module_imports.append("functions")
    module_imports = sorted(module_imports)

    all_exports = [
        "ATTRIBUTES",
        "ENTITIES",
        "RELATIONS",
        "SCHEMA_VERSION",
        "attributes",
        "entities",
        "registry",
        "relations",
    ]
    if functions_present:
        all_exports.append("functions")
    if include_schema_loader:
        all_exports.append("schema_text")
    all_exports = sorted(all_exports)

    template = get_template("package_init.py.jinja")
    return template.render(
        module_imports=module_imports,
        schema_version=schema_version,
        include_schema_loader=include_schema_loader,
        schema_filename=schema_filename or "schema.tql",
        attributes=sorted(attr_class_names[name] for name in attr_class_names),
        entities=sorted(entity_class_names[name] for name in entity_class_names),
        relations=sorted(relation_class_names[name] for name in relation_class_names),
        all_exports=all_exports,
    )

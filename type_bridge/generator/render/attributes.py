"""Render attribute class definitions from parsed schema."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from ..naming import render_all_export

if TYPE_CHECKING:
    from ..models import ParsedSchema

# Mapping from TypeDB value types to type-bridge attribute classes
VALUE_TYPE_MAP: Mapping[str, str] = {
    "string": "String",
    "integer": "Integer",
    "long": "Integer",  # TypeDB long maps to type-bridge Integer
    "double": "Double",
    "datetime": "DateTime",
    "datetime-tz": "DateTimeTZ",
    "date": "Date",
    "duration": "Duration",
    "boolean": "Boolean",
    "decimal": "Decimal",
}


def _resolve_value_type(
    attr_name: str,
    schema: ParsedSchema,
    visited: set[str] | None = None,
) -> str:
    """Resolve the value type for an attribute, following inheritance."""
    if visited is None:
        visited = set()

    if attr_name in visited:
        # Circular inheritance - shouldn't happen but handle gracefully
        return "String"

    visited.add(attr_name)
    attr = schema.attributes.get(attr_name)

    if attr is None:
        return "String"

    if attr.value_type:
        return attr.value_type

    if attr.parent:
        return _resolve_value_type(attr.parent, schema, visited)

    return "String"


def _resolve_base_class(
    attr_name: str,
    schema: ParsedSchema,
    class_names: dict[str, str],
) -> str:
    """Determine the base class for an attribute.

    Returns either a type-bridge base class (String, Integer, etc.)
    or a parent attribute class name for inheritance.
    """
    attr = schema.attributes[attr_name]

    if attr.parent and attr.parent in schema.attributes:
        # Inherit from parent attribute class
        return class_names[attr.parent]

    # Use the value type to determine base class
    value_type = _resolve_value_type(attr_name, schema)
    return VALUE_TYPE_MAP.get(value_type, "String")


def _get_required_imports(schema: ParsedSchema, class_names: dict[str, str]) -> set[str]:
    """Determine which type-bridge imports are needed."""
    imports: set[str] = {"AttributeFlags"}

    for attr in schema.attributes.values():
        base = _resolve_base_class(attr.name, schema, class_names)
        # Only add to imports if it's a type-bridge class, not a parent attribute
        if base in VALUE_TYPE_MAP.values():
            imports.add(base)

    # Check if any attribute uses case (needs TypeNameCase import)
    if any(attr.case for attr in schema.attributes.values()):
        imports.add("TypeNameCase")

    return imports


def _render_attribute_class(
    attr_name: str,
    schema: ParsedSchema,
    class_names: dict[str, str],
) -> list[str]:
    """Render a single attribute class definition."""
    attr = schema.attributes[attr_name]
    cls_name = class_names[attr_name]
    base_class = _resolve_base_class(attr_name, schema, class_names)

    lines: list[str] = []
    lines.append(f"class {cls_name}({base_class}):")

    # Docstring
    if attr.docstring:
        lines.append(f'    """{attr.docstring}"""')
    else:
        lines.append(f'    """Attribute for `{attr_name}`."""')

    # Build flags arguments
    # Note: AttributeFlags doesn't support abstract - abstract attributes use Python inheritance
    flags_args = [f'name="{attr_name}"']
    if attr.case:
        flags_args.append(f"case=TypeNameCase.{attr.case}")

    lines.append(f"    flags = AttributeFlags({', '.join(flags_args)})")

    # Regex constraint
    if attr.regex:
        lines.append(f'    regex: ClassVar[str] = r"{attr.regex}"')

    # Allowed values constraint
    if attr.allowed_values:
        values_str = ", ".join(f'"{v}"' for v in attr.allowed_values)
        lines.append(f"    allowed_values: ClassVar[tuple[str, ...]] = ({values_str},)")

    # Legacy fields
    if attr.default is not None:
        lines.append(f"    default_value = {attr.default!r}")
    if attr.transform is not None:
        lines.append(f"    transform = {attr.transform!r}")

    lines.append("")
    lines.append("")

    return lines


def _topological_sort_attributes(schema: ParsedSchema) -> list[str]:
    """Sort attributes so parents come before children."""
    result: list[str] = []
    visited: set[str] = set()

    def visit(name: str) -> None:
        if name in visited or name not in schema.attributes:
            return
        visited.add(name)

        attr = schema.attributes[name]
        if attr.parent and attr.parent in schema.attributes:
            visit(attr.parent)

        result.append(name)

    for name in schema.attributes:
        visit(name)

    return result


def render_attributes(schema: ParsedSchema, class_names: dict[str, str]) -> str:
    """Render the complete attributes module source.

    Args:
        schema: Parsed schema containing attribute definitions
        class_names: Mapping from TypeDB names to Python class names

    Returns:
        Complete Python source code for attributes.py
    """
    # Check what imports we need
    imports = _get_required_imports(schema, class_names)
    uses_classvar = any(attr.allowed_values or attr.regex for attr in schema.attributes.values())

    # Build header
    lines: list[str] = [
        '"""Attribute type definitions generated from a TypeDB schema."""',
        "",
    ]

    if uses_classvar:
        lines.append("from typing import ClassVar")
        lines.append("")

    # type-bridge imports
    import_list = sorted(imports)
    lines.append(f"from type_bridge import {', '.join(import_list)}")
    lines.append("")
    lines.append("")

    # Render classes in topological order (parents first)
    rendered_names: list[str] = []
    for attr_name in _topological_sort_attributes(schema):
        rendered_names.append(class_names[attr_name])
        lines.extend(_render_attribute_class(attr_name, schema, class_names))

    # Add __all__ export
    lines.extend(render_all_export(rendered_names))

    return "\n".join(lines)

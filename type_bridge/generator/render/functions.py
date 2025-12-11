"""Render function definitions from parsed schema."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..naming import render_all_export, to_python_name

if TYPE_CHECKING:
    from ..models import FunctionSpec, ParsedSchema

# TypeDB type -> Python type hint
TYPE_MAPPING = {
    "string": "str",
    "integer": "int",
    "int": "int",
    "long": "int",
    "double": "float",
    "boolean": "bool",
    "bool": "bool",
    "date": "date",
    "datetime": "datetime",
    "datetime-tz": "datetime",
    "decimal": "Decimal",
    "duration": "Duration",
}


def _get_python_type(type_name: str, for_param: bool = True) -> str:
    """Get Python type hint for TypeDB type.

    Args:
        type_name: The TypeDB type name
        for_param: If True, adds `| Expression` for parameter types
    """
    # Handle optional types (name?)
    is_optional = type_name.endswith("?")
    if is_optional:
        type_name = type_name[:-1]

    base = TYPE_MAPPING.get(type_name, type_name)  # Keep entity names as-is

    if is_optional:
        base = f"{base} | None"

    if for_param:
        return f"{base} | Expression"
    return base


def _parse_return_type(return_type: str) -> tuple[bool, list[str]]:
    """Parse return type string into components.

    Returns:
        Tuple of (is_stream, list_of_types)
    """
    is_stream = return_type.startswith("{") and return_type.endswith("}")
    if is_stream:
        inner = return_type[1:-1].strip()  # Remove { }
    else:
        inner = return_type

    # Split by comma, handling spaces
    types = [t.strip() for t in inner.split(",")]
    return is_stream, types


def _get_return_type_hint(return_type: str) -> str:
    """Convert TypeDB return type to Python type hint for FunctionCallExpr generic."""
    is_stream, types = _parse_return_type(return_type)

    # Convert each type
    py_types = [_get_python_type(t, for_param=False) for t in types]

    if len(py_types) == 1:
        inner_type = py_types[0]
    else:
        inner_type = f"tuple[{', '.join(py_types)}]"

    # Stream returns Iterator, single returns the type directly
    if is_stream:
        return f"FunctionCallExpr[Iterator[{inner_type}]]"
    return f"FunctionCallExpr[{inner_type}]"


def _render_function(name: str, spec: FunctionSpec) -> list[str]:
    """Render a single function definition."""
    py_name = to_python_name(name)
    lines = []

    # Signature
    params = []
    for p in spec.parameters:
        p_name = to_python_name(p.name)
        p_type = _get_python_type(p.type, for_param=True)
        params.append(f"{p_name}: {p_type}")

    return_hint = _get_return_type_hint(spec.return_type)
    lines.append(f"def {py_name}({', '.join(params)}) -> {return_hint}:")

    # Docstring with return type info
    is_stream, types = _parse_return_type(spec.return_type)
    stream_info = "stream of " if is_stream else ""
    type_info = ", ".join(types)

    if spec.docstring:
        lines.append(f'    """{spec.docstring}')
        lines.append("")
        lines.append(f"    Returns: {stream_info}{type_info}")
        lines.append('    """')
    else:
        lines.append(f'    """Call TypeDB function `{name}`.')
        lines.append("")
        lines.append(f"    Returns: {stream_info}{type_info}")
        lines.append('    """')

    # Body
    args = [to_python_name(p.name) for p in spec.parameters]
    lines.append(f'    return FunctionCallExpr("{name}", [{", ".join(args)}])')
    lines.append("")

    return lines


def render_functions(schema: ParsedSchema) -> str:
    """Render the complete functions module."""
    if not schema.functions:
        return ""

    lines = [
        '"""Function wrappers generated from a TypeDB schema."""',
        "",
        "from __future__ import annotations",
        "",
        "from datetime import date, datetime",
        "from decimal import Decimal",
        "from typing import Any, Iterator",
        "",
        "from isodate import Duration",
        "",
        "from type_bridge.expressions import Expression, FunctionCallExpr",
        "",
        "",
    ]

    func_names = []
    for name, spec in schema.functions.items():
        py_name = to_python_name(name)
        func_names.append(py_name)
        lines.extend(_render_function(name, spec))

    lines.extend(render_all_export(func_names))

    return "\n".join(lines)

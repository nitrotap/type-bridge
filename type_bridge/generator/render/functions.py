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
    "date": "date",
    "datetime": "datetime",
    "datetime-tz": "datetime",
    "decimal": "Decimal",
    "duration": "Duration",
}


def _get_python_type(type_name: str) -> str:
    """Get Python type hint for TypeDB type."""
    base = TYPE_MAPPING.get(type_name, "Any")
    return f"{base} | Expression"


def _render_function(name: str, spec: FunctionSpec) -> list[str]:
    """Render a single function definition."""
    py_name = to_python_name(name)
    lines = []

    # Signature
    params = []
    for p in spec.parameters:
        p_name = to_python_name(p.name)
        p_type = _get_python_type(p.type)
        params.append(f"{p_name}: {p_type}")

    lines.append(f"def {py_name}({', '.join(params)}) -> FunctionCallExpr:")

    if spec.docstring:
        lines.append(f'    """{spec.docstring}"""')
    else:
        lines.append(f'    """Wrapper for TypeDB function `{name}`."""')

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
        "from typing import Any",
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

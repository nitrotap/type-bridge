"""Render relation class definitions from parsed schema."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..models import minimal_role_players
from ..naming import render_all_export, to_class_name, to_python_name

if TYPE_CHECKING:
    from ..models import ParsedSchema


def _render_role_field(
    role_name: str,
    player_classes: list[str],
) -> str | None:
    """Render a single role field declaration.

    Returns a string like:
    - "    author: Role[entities.Person] = Role('author', entities.Person)"
    - "    item: Role[entities.Book | entities.Magazine] = _multi(Role.multi(...))"

    Returns None if no players are found (shouldn't happen in valid schema).
    """
    if not player_classes:
        return None

    py_name = to_python_name(role_name)

    if len(player_classes) == 1:
        player = player_classes[0]
        return f'    {py_name}: Role[entities.{player}] = Role("{role_name}", entities.{player})'

    # Multiple players - use union type and Role.multi()
    primary, *rest = player_classes
    extras = ", ".join(f"entities.{p}" for p in rest)
    union_type = " | ".join(f"entities.{p}" for p in player_classes)

    return (
        f"    {py_name}: Role[{union_type}] = "
        f'_multi(Role.multi("{role_name}", entities.{primary}, {extras}))'
    )


def _render_relation_class(
    relation_name: str,
    schema: ParsedSchema,
    attr_class_names: dict[str, str],
    entity_class_names: dict[str, str],
    relation_class_names: dict[str, str],
) -> list[str]:
    """Render a single relation class definition."""
    relation = schema.relations[relation_name]
    cls_name = relation_class_names[relation_name]

    # Determine base class
    if relation.parent and relation.parent in relation_class_names:
        base_class = relation_class_names[relation.parent]
    else:
        base_class = "Relation"

    lines: list[str] = []
    lines.append(f"class {cls_name}({base_class}):")

    # Docstring
    if relation.docstring:
        lines.append(f'    """{relation.docstring}"""')
    else:
        lines.append(f'    """Relation generated from `{relation_name}`."""')

    # TypeFlags
    flag_args = [f'name="{relation_name}"']
    if relation.abstract:
        flag_args.append("abstract=True")
    lines.append(f"    flags = TypeFlags({', '.join(flag_args)})")

    # Attributes - only render those not inherited
    parent_owns = set()
    if relation.parent and relation.parent in schema.relations:
        parent_owns = schema.relations[relation.parent].owns

    own_attrs = [a for a in relation.owns_order if a not in parent_owns]
    for attr in own_attrs:
        if attr not in attr_class_names:
            continue
        py_attr = to_python_name(attr)
        attr_class = attr_class_names[attr]
        lines.append(f"    {py_attr}: attributes.{attr_class}")

    # Roles - only render those not inherited
    parent_roles = set()
    if relation.parent and relation.parent in schema.relations:
        parent_roles = {r.name for r in schema.relations[relation.parent].roles}

    for role in relation.roles:
        if role.name in parent_roles and not role.overrides:
            # Skip inherited roles that aren't being overridden
            continue

        players = minimal_role_players(schema, relation_name, role.name)
        player_classes = [entity_class_names[p] for p in players if p in entity_class_names]

        role_line = _render_role_field(role.name, player_classes)
        if role_line:
            lines.append(role_line)

    lines.append("")
    lines.append("")

    return lines


def _topological_sort_relations(schema: ParsedSchema) -> list[str]:
    """Sort relations so parents come before children."""
    result: list[str] = []
    visited: set[str] = set()

    def visit(name: str) -> None:
        if name in visited or name not in schema.relations:
            return
        visited.add(name)

        relation = schema.relations[name]
        if relation.parent and relation.parent in schema.relations:
            visit(relation.parent)

        result.append(name)

    for name in schema.relations:
        visit(name)

    return result


def render_relations(
    schema: ParsedSchema,
    attr_class_names: dict[str, str],
    entity_class_names: dict[str, str],
    relation_class_names: dict[str, str] | None = None,
) -> str:
    """Render the complete relations module source.

    Args:
        schema: Parsed schema containing relation definitions
        attr_class_names: Mapping from TypeDB attr names to Python class names
        entity_class_names: Mapping from TypeDB entity names to Python class names
        relation_class_names: Mapping from TypeDB relation names to Python class names
            (if None, will be generated from relation names)

    Returns:
        Complete Python source code for relations.py
    """
    if relation_class_names is None:
        relation_class_names = {name: to_class_name(name) for name in schema.relations}

    # Build header
    lines: list[str] = [
        '"""Relation type definitions generated from a TypeDB schema."""',
        "",
        "from type_bridge import Relation, Role, TypeFlags",
        "",
        "from . import attributes, entities",
        "",
        "",
        "def _multi(role: Role) -> Role:",
        '    """Attach allowed_player_types for compatibility with MultiRole."""',
        '    setattr(role, "allowed_player_types", role.player_entity_types)  # noqa: B010',
        "    return role",
        "",
        "",
    ]

    # Render classes in topological order
    rendered_names: list[str] = []
    for relation_name in _topological_sort_relations(schema):
        rendered_names.append(relation_class_names[relation_name])
        lines.extend(
            _render_relation_class(
                relation_name,
                schema,
                attr_class_names,
                entity_class_names,
                relation_class_names,
            )
        )

    # Add helper function
    lines.extend(
        [
            "def get_roles(relation_cls: type[Relation]) -> dict[str, Role]:",
            '    """Expose relation roles for introspection."""',
            "    return relation_cls._roles  # noqa: SLF001",
            "",
            "",
        ]
    )

    # Add __all__ export
    lines.extend(render_all_export(rendered_names, extras=["get_roles"]))

    return "\n".join(lines)

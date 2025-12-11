"""Lark-based TQL schema parser."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from lark import Lark, Transformer

from .models import (
    AttributeSpec,
    Cardinality,
    EntitySpec,
    FunctionSpec,
    ParameterSpec,
    ParsedSchema,
    RelationSpec,
    RoleSpec,
)

logger = logging.getLogger(__name__)

# Load grammar
GRAMMAR_PATH = Path(__file__).parent / "typeql.lark"


class SchemaTransformer(Transformer):
    """Transform Lark parse tree into TypeBridge schema models."""

    def __init__(self) -> None:
        self.schema = ParsedSchema()
        self.pending_annotations: dict[str, Any] = {}

    def start(self, items: list[Any]) -> ParsedSchema:
        """Root rule: returns the populated schema."""
        self.schema.accumulate_inheritance()
        return self.schema

    # --- Attributes ---
    def attribute_def(self, items: list[Any]) -> None:
        name_token = items[0]
        # items[1] is attribute_opts result (list of dicts) if present
        opts_list = items[1] if len(items) > 1 else []

        # Merge all opts dicts
        opts = {}
        for opt in opts_list:
            opts.update(opt)

        attr = AttributeSpec(
            name=str(name_token),
            value_type=opts.get("value_type", ""),
            parent=opts.get("parent"),
            abstract=opts.get("abstract", False),
            regex=opts.get("regex"),
            allowed_values=opts.get("values"),
        )
        self.schema.attributes[attr.name] = attr

    def attribute_opts(self, items: list[Any]) -> list[dict[str, Any]]:
        # Returns list of dicts from children
        return items

    def sub_clause(self, items: list[Any]) -> dict[str, str]:
        return {"parent": str(items[0])}

    def value_type_clause(self, items: list[Any]) -> dict[str, str]:
        return {"value_type": str(items[0])}

    def abstract_annotation(self, items: list[Any]) -> dict[str, bool]:
        return {"abstract": True}

    def regex_annotation(self, items: list[Any]) -> dict[str, str]:
        raw = str(items[0])
        return {"regex": raw[1:-1]}

    def values_annotation(self, items: list[Any]) -> dict[str, tuple[str, ...]]:
        return {"values": tuple(items[0])}

    def string_list(self, items: list[Any]) -> list[str]:
        return [str(item)[1:-1] for item in items]

    def value_type(self, items: list[Any]) -> str:
        return str(items[0])

    # --- Entities ---
    def entity_def(self, items: list[Any]) -> None:
        name = str(items[0])

        # Collect all opts and clauses
        opts = {}
        owns_list = []
        plays_set = set()

        # items[1:] contains entity_clauses (dict, tuple, or str)
        for item in items[1:]:
            if isinstance(item, dict):  # sub_clause or abstract_annotation
                opts.update(item)
            elif isinstance(item, tuple):  # owns_statement result
                owns_list.append(item)
            elif isinstance(item, str):  # plays_statement result
                plays_set.add(item)

        # Process owns
        owns_set = set()
        owns_order = []
        keys = set()
        uniques = set()
        cardinalities = {}

        for attr, card, is_key, is_unique in owns_list:
            owns_set.add(attr)
            owns_order.append(attr)
            if is_key:
                keys.add(attr)
            if is_unique:
                uniques.add(attr)
            if card:
                cardinalities[attr] = card

        entity = EntitySpec(
            name=name,
            parent=opts.get("parent"),
            owns=owns_set,
            owns_order=owns_order,
            plays=plays_set,
            abstract=opts.get("abstract", False),
            keys=keys,
            uniques=uniques,
            cardinalities=cardinalities,
        )
        self.schema.entities[name] = entity

    def entity_clause(self, items: list[Any]) -> Any:
        return items[0]

    def owns_statement(self, items: list[Any]) -> tuple[str, Cardinality | None, bool, bool]:
        name = str(items[0])
        opts = items[1] or {} if len(items) > 1 else {}
        return (
            name,
            opts.get("card"),
            opts.get("key", False),
            opts.get("unique", False),
        )

    def owns_opts(self, items: list[Any]) -> dict[str, Any]:
        opts = {}
        for item in items:
            opts.update(item)
        return opts

    def key_annotation(self, items: list[Any]) -> dict[str, bool]:
        return {"key": True}

    def unique_annotation(self, items: list[Any]) -> dict[str, bool]:
        return {"unique": True}

    def card_annotation(self, items: list[Any]) -> dict[str, Cardinality]:
        # Filter None (from optional grammar groups)
        real_items = [x for x in items if x is not None]

        min_val = int(real_items[0])

        if len(real_items) == 1:
            # @card(x) -> exactly x
            return {"card": Cardinality(min_val, min_val)}

        # Has ".."
        # items could be [min, ".."] or [min, "..", max]
        last = real_items[-1]
        if hasattr(last, "type") and last.type == "INT":
            max_val = int(last)
        else:
            max_val = None  # Unbounded

        return {"card": Cardinality(min_val, max_val)}

    def plays_statement(self, items: list[Any]) -> str:
        # items: [relation_name, optional role_name (Token), optional card_annotation (dict)]
        # We ignore cardinality on plays for now
        relation = str(items[0])
        # Check if there's a role (second item is a Token, not a dict)
        if len(items) > 1 and items[1] is not None and not isinstance(items[1], dict):
            return f"{relation}:{items[1]}"
        return relation

    # --- Relations ---
    def relation_def(self, items: list[Any]) -> None:
        name = str(items[0])

        opts = {}
        roles = []
        owns_list = []
        plays_set = set()

        # items[1:] contains relation_clauses (dict, RoleSpec, tuple, or str)
        for item in items[1:]:
            if isinstance(item, dict):  # sub_clause or abstract_annotation
                opts.update(item)
            elif isinstance(item, RoleSpec):  # relates_statement
                roles.append(item)
            elif isinstance(item, tuple):  # owns_statement
                owns_list.append(item)
            elif isinstance(item, str):  # plays_statement
                plays_set.add(item)

        # Process owns
        owns_set = set()
        owns_order = []
        keys = set()
        uniques = set()
        cardinalities = {}

        for attr, card, is_key, is_unique in owns_list:
            owns_set.add(attr)
            owns_order.append(attr)
            if is_key:
                keys.add(attr)
            if is_unique:
                uniques.add(attr)
            if card:
                cardinalities[attr] = card

        rel = RelationSpec(
            name=name,
            parent=opts.get("parent"),
            roles=roles,
            owns=owns_set,
            owns_order=owns_order,
            abstract=opts.get("abstract", False),
            keys=keys,
            uniques=uniques,
            cardinalities=cardinalities,
        )
        self.schema.relations[name] = rel

    def relation_clause(self, items: list[Any]) -> Any:
        return items[0]

    def relates_statement(self, items: list[Any]) -> RoleSpec:
        # items: [role_name, optional "as" override (Token), optional card_annotation (dict)]
        # We ignore cardinality on relates for now
        name = str(items[0])
        overrides = None
        if len(items) > 1 and items[1] is not None and not isinstance(items[1], dict):
            overrides = str(items[1])
        return RoleSpec(name=name, overrides=overrides)

    # --- Functions ---
    def function_def(self, items: list[Any]) -> None:
        idx = 0
        name = str(items[idx])
        idx += 1

        parameters = []
        if idx < len(items) and isinstance(items[idx], list):
            parameters = items[idx]
            idx += 1

        # Next item is return_type_clause result (string)
        return_type = str(items[idx])

        func = FunctionSpec(name=name, parameters=parameters, return_type=return_type)
        self.schema.functions[name] = func

    def param_list(self, items: list[Any]) -> list[ParameterSpec]:
        return items

    def param(self, items: list[Any]) -> ParameterSpec:
        return ParameterSpec(name=str(items[0]), type=str(items[1]))

    def return_type_clause(self, items: list[Any]) -> str:
        return str(items[0])

    def return_type(self, items: list[Any]) -> str:
        return str(items[0])

    def func_body(self, items: list[Any]) -> Any:
        return None  # Ignore body content

    # --- Comments ---
    # Comments are ignored by grammar (%ignore SH_COMMENT),
    # capturing docstrings requires explicit token handling or a separate pass.
    # For now, we accept losing docstrings in the migration or add them later.


def parse_tql_schema(schema_content: str) -> ParsedSchema:
    """Parse TQL schema using Lark."""
    with open(GRAMMAR_PATH, encoding="utf-8") as f:
        grammar = f.read()

    parser = Lark(grammar, start="start", parser="lalr")
    tree = parser.parse(schema_content)

    transformer = SchemaTransformer()
    return transformer.transform(tree)

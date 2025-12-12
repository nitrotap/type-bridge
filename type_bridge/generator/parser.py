"""Parse TypeDB TQL schema definitions into structured specs.

This parser uses regex-based extraction rather than a full grammar parser.
It handles TypeDB 3.x schema syntax including:
- Entities, relations, and attributes with inheritance (sub)
- Abstract types (@abstract)
- Ownership with constraints (@key, @unique, @card)
- Role definitions with overrides (relates X as Y)
- Value constraints (@regex, @values)
- Functions (ignored, logged as debug)
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from .models import (
    AttributeSpec,
    Cardinality,
    EntitySpec,
    ParsedSchema,
    RelationSpec,
    RoleSpec,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


# =============================================================================
# Regex patterns for TQL parsing
# =============================================================================

# Block-level patterns
RE_DEFINE_BLOCK = re.compile(r"define\s+", re.IGNORECASE)
RE_FUNCTION = re.compile(r"\bfun\s+[\w-]+\s*\([^)]*\)", re.MULTILINE)

# Type declaration patterns (match at start of statement)
RE_ATTRIBUTE = re.compile(r"^\s*attribute\s+([\w-]+)", re.MULTILINE)
RE_ENTITY = re.compile(r"^\s*entity\s+([\w-]+)", re.MULTILINE)
RE_RELATION = re.compile(r"^\s*relation\s+([\w-]+)", re.MULTILINE)

# Inheritance and value type
RE_SUB = re.compile(r"\bsub\s+([\w-]+)")
RE_VALUE_TYPE = re.compile(r"\bvalue\s+([\w-]+)")

# Ownership patterns
RE_OWNS = re.compile(r"\bowns\s+([\w-]+)")
RE_OWNS_KEY = re.compile(r"\bowns\s+([\w-]+)\s+@key")
RE_OWNS_UNIQUE = re.compile(r"\bowns\s+([\w-]+)\s+@unique")
RE_OWNS_CARD = re.compile(r"\bowns\s+([\w-]+)\s+@card\s*\(\s*(\d+)(?:\.\.(\d*))?\s*\)")

# Role patterns
RE_RELATES = re.compile(r"\brelates\s+([\w-]+)(?:\s+as\s+([\w-]+))?")
RE_PLAYS = re.compile(r"\bplays\s+([\w:-]+)")

# Constraint patterns
RE_ABSTRACT = re.compile(r"@abstract\b")
RE_REGEX = re.compile(r'@regex\s*\(\s*"([^"]+)"\s*\)')
RE_VALUES = re.compile(r"@values\s*\(([^)]+)\)")

# Comment annotation patterns (for custom metadata)
RE_ANNOTATION = re.compile(r"#\s*@([\w-]+)(?::\s*(.*))?$")


# =============================================================================
# Parsing helpers
# =============================================================================


def _parse_cardinality(min_str: str, max_str: str | None) -> Cardinality:
    """Parse cardinality from regex match groups."""
    min_val = int(min_str)
    if max_str is None:
        # @card(x) means exactly x
        return Cardinality(min_val, min_val)
    if max_str == "":
        # @card(x..) means unbounded
        return Cardinality(min_val, None)
    # @card(x..y)
    return Cardinality(min_val, int(max_str))


def _parse_cardinalities(block: str) -> dict[str, Cardinality]:
    """Extract all @card annotations from owns clauses."""
    cardinalities: dict[str, Cardinality] = {}
    for match in RE_OWNS_CARD.finditer(block):
        attr_name = match.group(1)
        cardinalities[attr_name] = _parse_cardinality(match.group(2), match.group(3))
    return cardinalities


def _parse_values_annotation(block: str) -> tuple[str, ...] | None:
    """Extract values from @values("v1", "v2", ...) annotation."""
    match = RE_VALUES.search(block)
    if not match:
        return None
    raw_values = match.group(1)
    values = re.findall(r'["\']([^"\']+)["\']', raw_values)
    return tuple(values) if values else None


def _parse_regex_annotation(block: str) -> str | None:
    """Extract regex pattern from @regex annotation."""
    match = RE_REGEX.search(block)
    return match.group(1) if match else None


def _extract_comment_annotations(lines: list[str]) -> dict[str, object]:
    """Extract @key: value annotations from comment lines."""
    import ast

    annotations: dict[str, object] = {}
    for line in lines:
        match = RE_ANNOTATION.match(line.strip())
        if not match:
            continue
        key, raw_value = match.groups()
        value: object = True if raw_value is None else raw_value.strip()
        try:
            value = ast.literal_eval(str(value))
        except (SyntaxError, ValueError):
            value = str(value)
        annotations[key.strip()] = value
    return annotations


def _extract_docstring(text: str) -> str | None:
    """Extract docstring from comment lines preceding a statement."""
    lines = text.strip().splitlines()
    doc_parts: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("#"):
            break
        # Skip annotation comments
        if RE_ANNOTATION.match(stripped):
            continue
        text_content = stripped.lstrip("#").strip()
        if text_content:
            doc_parts.append(text_content)
    return " ".join(doc_parts) if doc_parts else None


def _is_abstract(text: str) -> bool:
    """Check if a type declaration includes @abstract."""
    return bool(RE_ABSTRACT.search(text))


# =============================================================================
# Statement splitting
# =============================================================================


def _split_statements(content: str) -> list[str]:
    """Split schema content into individual type declarations.

    Handles semicolon-separated statements while preserving comments.
    """
    statements: list[str] = []
    current: list[str] = []
    depth = 0  # Track parentheses depth for @regex, @values, etc.

    for line in content.splitlines():
        stripped = line.strip()

        # Skip empty lines and pure comment lines (they'll be captured with next statement)
        if not stripped:
            if current:
                current.append(line)
            continue

        # Track parentheses depth
        depth += stripped.count("(") - stripped.count(")")

        current.append(line)

        # Statement ends with semicolon at depth 0
        if stripped.endswith(";") and depth <= 0:
            statements.append("\n".join(current))
            current = []
            depth = 0

    # Handle any remaining content (statement without trailing semicolon)
    if current:
        statements.append("\n".join(current))

    return statements


# =============================================================================
# Type parsers
# =============================================================================


def _parse_attribute(text: str) -> AttributeSpec | None:
    """Parse an attribute declaration."""
    match = RE_ATTRIBUTE.search(text)
    if not match:
        return None

    name = match.group(1)
    value_match = RE_VALUE_TYPE.search(text)
    sub_match = RE_SUB.search(text)

    return AttributeSpec(
        name=name,
        value_type=value_match.group(1) if value_match else "",
        parent=sub_match.group(1) if sub_match else None,
        abstract=_is_abstract(text),
        regex=_parse_regex_annotation(text),
        allowed_values=_parse_values_annotation(text),
        docstring=_extract_docstring(text),
    )


def _parse_entity(text: str, annotations: dict[str, object]) -> EntitySpec | None:
    """Parse an entity declaration."""
    match = RE_ENTITY.search(text)
    if not match:
        return None

    name = match.group(1)
    sub_match = RE_SUB.search(text)

    # Extract ownership - RE_OWNS matches all owns including those with annotations
    owns_order = [m.group(1) for m in RE_OWNS.finditer(text)]
    keys = {m.group(1) for m in RE_OWNS_KEY.finditer(text)}
    uniques = {m.group(1) for m in RE_OWNS_UNIQUE.finditer(text)}
    plays = {m.group(1) for m in RE_PLAYS.finditer(text)}

    return EntitySpec(
        name=name,
        parent=sub_match.group(1) if sub_match else None,
        owns=set(owns_order),
        owns_order=owns_order,
        plays=plays,
        abstract=_is_abstract(text),
        keys=keys,
        uniques=uniques,
        cardinalities=_parse_cardinalities(text),
        docstring=_extract_docstring(text),
        prefix=str(annotations["prefix"]) if isinstance(annotations.get("prefix"), str) else None,
        internal=bool(annotations.get("internal", False)),
    )


def _parse_relation(text: str) -> RelationSpec | None:
    """Parse a relation declaration."""
    match = RE_RELATION.search(text)
    if not match:
        return None

    name = match.group(1)
    sub_match = RE_SUB.search(text)

    # Parse roles
    roles: list[RoleSpec] = []
    for role_match in RE_RELATES.finditer(text):
        role_name = role_match.group(1)
        overrides = role_match.group(2)
        roles.append(RoleSpec(name=role_name, overrides=overrides))

    # Extract ownership
    owns_order = [m.group(1) for m in RE_OWNS.finditer(text)]
    keys = {m.group(1) for m in RE_OWNS_KEY.finditer(text)}
    uniques = {m.group(1) for m in RE_OWNS_UNIQUE.finditer(text)}

    return RelationSpec(
        name=name,
        parent=sub_match.group(1) if sub_match else None,
        roles=roles,
        owns=set(owns_order),
        owns_order=owns_order,
        abstract=_is_abstract(text),
        keys=keys,
        uniques=uniques,
        cardinalities=_parse_cardinalities(text),
        docstring=_extract_docstring(text),
    )


# =============================================================================
# Function removal
# =============================================================================


def _remove_functions(content: str) -> str:
    """Remove function definitions from schema content.

    TypeDB 3.x functions have the format:
        fun name($param: type) -> { return_type }:
          match
            ...
          return { $var };

    We remove everything from 'fun' to the line containing 'return' followed by semicolon.
    """
    lines = content.split("\n")
    result_lines: list[str] = []
    in_function = False
    brace_depth = 0

    for line in lines:
        stripped = line.strip()

        # Detect function start
        if RE_FUNCTION.search(line) and not in_function:
            in_function = True
            brace_depth = 0
            continue

        if in_function:
            # Track braces to find function end
            brace_depth += stripped.count("{") - stripped.count("}")

            # Function ends when we see "return" and close all braces
            if "return" in stripped and brace_depth <= 0:
                in_function = False
            continue

        result_lines.append(line)

    return "\n".join(result_lines)


# =============================================================================
# Main parser
# =============================================================================


def parse_tql_schema(schema_content: str) -> ParsedSchema:
    """Parse TQL schema content into structured specs.

    Args:
        schema_content: Raw TQL schema text

    Returns:
        ParsedSchema containing all parsed attributes, entities, and relations
    """
    logger.debug("Starting TQL schema parsing")

    # Check for functions
    if RE_FUNCTION.search(schema_content):
        logger.debug("Schema contains function definitions which are not yet supported")

    # Remove function blocks
    clean_content = _remove_functions(schema_content)

    # Remove 'define' keywords - we'll split on statements
    content = RE_DEFINE_BLOCK.sub("", clean_content)

    # Split into individual statements
    statements = _split_statements(content)
    logger.debug(f"Found {len(statements)} statements to parse")

    schema = ParsedSchema()
    pending_annotations: dict[str, object] = {}

    for statement in statements:
        if not statement.strip():
            continue

        # Skip pure comment blocks
        non_comment_lines = [
            line
            for line in statement.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        if not non_comment_lines:
            # Extract annotations for next statement
            comment_lines = [
                line.strip() for line in statement.splitlines() if line.strip().startswith("#")
            ]
            pending_annotations = _extract_comment_annotations(comment_lines)
            continue

        # Try parsing as each type
        if attr := _parse_attribute(statement):
            schema.attributes[attr.name] = attr
            logger.debug(f"Parsed attribute: {attr.name}")
        elif entity := _parse_entity(statement, pending_annotations):
            schema.entities[entity.name] = entity
            logger.debug(f"Parsed entity: {entity.name}")
        elif relation := _parse_relation(statement):
            schema.relations[relation.name] = relation
            logger.debug(f"Parsed relation: {relation.name}")

        pending_annotations = {}

    # Resolve inheritance
    logger.debug("Resolving inheritance")
    schema.accumulate_inheritance()

    logger.info(
        f"Schema parsed: {len(schema.attributes)} attributes, "
        f"{len(schema.entities)} entities, {len(schema.relations)} relations"
    )
    return schema

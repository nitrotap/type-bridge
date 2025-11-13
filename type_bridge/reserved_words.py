"""TypeQL reserved words and keywords.

This module contains all TypeQL reserved words that cannot be used as type names,
attribute names, or role names in TypeDB schemas.

Based on TypeDB 3.x TypeQL reference documentation.
"""

# TypeQL Reserved Words/Keywords
# These words have special meaning in TypeQL and cannot be used as identifiers
TYPEQL_RESERVED_WORDS = frozenset({
    # ============================================================
    # Schema queries
    # ============================================================
    "define",      # Denotes the beginning of a Define query
    "undefine",    # Denotes the beginning of an Undefine query
    "redefine",    # Denotes the beginning of a Redefine query

    # ============================================================
    # Data manipulation stages
    # ============================================================
    "match",       # Match stage - match existing data instances
    "fetch",       # Fetch stage - format output into JSON
    "insert",      # Insert stage - add new data instances
    "delete",      # Delete stage - remove existing data instances
    "update",      # Update stage - modify existing data instances
    "put",         # Put stage - add data if it doesn't exist

    # ============================================================
    # Stream manipulation stages
    # ============================================================
    "select",      # Select operator - keep specified variables
    "require",     # Require stage - filter elements with optional variables
    "sort",        # Sort operator - order elements
    "limit",       # Limit operator - keep specified number of elements
    "offset",      # Offset operator - skip specified number of elements
    "reduce",      # Reduce operator - perform reduction operations

    # ============================================================
    # Special stages
    # ============================================================
    "with",        # Preamble - define functions for ad-hoc use

    # ============================================================
    # Pattern logic
    # ============================================================
    "or",          # Disjunction in query pattern
    "not",         # Negation in query pattern
    "try",         # Optional in query pattern

    # ============================================================
    # Type definition statements
    # ============================================================
    "entity",      # Define a new entity type
    "relation",    # Define a new relation type
    "attribute",   # Define a new attribute type
    "struct",      # Define a new struct type
    "fun",         # Define a new function

    # ============================================================
    # Constraint definition statements
    # ============================================================
    "sub",         # Define supertype of a type (also "sub!")
    "relates",     # Define a new role for a relation type
    "plays",       # Define a new role player for a role
    "value",       # Define the value type of an attribute type
    "owns",        # Define a new owner of an attribute type
    "alias",       # Define an alias label for a type

    # ============================================================
    # Instance statements
    # ============================================================
    "isa",         # Specify the type of a data instance (also "isa!")
    "links",       # Specify the role players in a relation
    "has",         # Specify an attribute of an entity or relation
    "is",          # Specify that two variables represent the same instance
    "let",         # Assign result of expression or stream element to variable
    "contains",    # String comparison - contains substring
    "like",        # String comparison - matches regex pattern

    # ============================================================
    # Identity statements
    # ============================================================
    "label",       # Identify a type by its label
    "iid",         # Identify a data instance by its internal ID

    # ============================================================
    # Annotations (without @ symbol)
    # ============================================================
    # Note: These are reserved as keywords even without @
    "card",        # Cardinality constraint
    "cascade",     # Cascade deletion behavior
    "independent", # Prevent automatic deletion of ownerless attributes
    "abstract",    # Mark type or role as abstract
    "key",         # Key attribute constraint
    "subkey",      # Composite key constraint
    "unique",      # Unique attribute constraint
    "values",      # Set of permitted values
    "range",       # Range of permitted values
    "regex",       # Regex pattern for values
    "distinct",    # Restrict to distinct values

    # ============================================================
    # Reductions
    # ============================================================
    "check",       # Check if stream contains elements
    "first",       # Get first occurrence
    "count",       # Count occurrences
    "max",         # Maximum value
    "min",         # Minimum value
    "mean",        # Arithmetic mean
    "median",      # Median value
    "std",         # Standard deviation
    "sum",         # Sum over variable
    "list",        # List of occurrences

    # ============================================================
    # Value types
    # ============================================================
    "boolean",     # Boolean values
    "integer",     # 64-bit signed integers
    "double",      # 64-bit floating point numbers
    "decimal",     # Fixed-point decimals
    "datetime-tz", # Timestamps with timezones (also "datetime_tz")
    "datetime_tz", # Alternative syntax
    "datetime",    # Timestamps without timezones
    "date",        # ISO dates
    "duration",    # ISO durations
    "string",      # UTF-8 encoded strings

    # ============================================================
    # Built-in functions (without parentheses)
    # ============================================================
    "round",       # Round to nearest integer
    "ceil",        # Round to nearest greater integer
    "floor",       # Round to nearest lesser integer
    "abs",         # Absolute value
    "length",      # Length of list
    # Note: "min" and "max" already included in reductions

    # ============================================================
    # Literals
    # ============================================================
    "true",        # Boolean true literal
    "false",       # Boolean false literal

    # ============================================================
    # Miscellaneous
    # ============================================================
    "asc",         # Ascending order for Sort
    "desc",        # Descending order for Sort
    "return",      # Return signature of function
    "of",          # Remove ownership/players in Delete
    "from",        # Remove interfaces/specialization in Undefine
    "in",          # Access stream or list elements
    "as",          # Specialize a role
})


def get_reserved_words() -> frozenset[str]:
    """Get the complete set of TypeQL reserved words.

    Returns:
        A frozenset of all TypeQL reserved words
    """
    return TYPEQL_RESERVED_WORDS


def is_reserved_word(name: str) -> bool:
    """Check if a name is a TypeQL reserved word.

    Args:
        name: The name to check

    Returns:
        True if the name is a reserved word (case-insensitive)
    """
    return name.lower() in TYPEQL_RESERVED_WORDS
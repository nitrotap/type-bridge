# Unit Tests

This directory contains fast, isolated unit tests that don't require external dependencies.

## Structure

```
unit/
├── core/                        # Core functionality tests
│   ├── test_basic.py            # Basic entity/relation/attribute API
│   ├── test_inheritance.py      # Inheritance and type hierarchies
│   └── test_pydantic.py         # Pydantic integration and validation
├── attributes/                  # Attribute type tests
│   ├── test_boolean.py          # Boolean attribute type
│   ├── test_date.py             # Date attribute type
│   ├── test_datetime_tz.py      # DateTimeTZ attribute type
│   ├── test_decimal.py          # Decimal attribute type
│   ├── test_double.py           # Double attribute type
│   ├── test_duration.py         # Duration attribute type (ISO 8601)
│   ├── test_formatting.py       # Mixed attribute formatting in insert queries
│   ├── test_integer.py          # Integer attribute type
│   └── test_string.py           # String attribute type
├── flags/                       # Flag system tests
│   ├── test_base_flag.py        # Base flag for schema exclusion
│   ├── test_cardinality.py      # Card API for cardinality constraints
│   ├── test_typename_case.py    # Entity/Relation type name formatting
│   └── test_attribute_typename_case.py  # Attribute type name formatting
└── crud/                        # CRUD operation tests
    └── test_update_api.py       # Update API for entities

```

## Test Categories

### Core Tests (33 tests)
- **test_basic.py** (13 tests): Entity/Relation creation, schema generation, insert queries
- **test_inheritance.py** (11 tests): Type hierarchies, base classes, edge cases
- **test_pydantic.py** (9 tests): Validation, serialization, type coercion

### Attribute Tests (115 tests)
- **test_boolean.py** (8 tests): Boolean type creation, formatting, multi-value
- **test_date.py** (17 tests): Date type creation, formatting, validation
- **test_datetime_tz.py** (14 tests): Timezone-aware datetime, conversions
- **test_decimal.py** (16 tests): Fixed-point decimal with 19-digit precision
- **test_double.py** (11 tests): Double type creation, precision, edge cases
- **test_duration.py** (25 tests): ISO 8601 durations, arithmetic operations
- **test_formatting.py** (5 tests): Mixed attribute formatting in TypeQL queries
- **test_integer.py** (8 tests): Integer type creation, edge cases, formatting
- **test_string.py** (11 tests): String type creation, special characters, concatenation

### Flag Tests (43 tests)
- **test_base_flag.py** (12 tests): Base class flag for schema exclusion
- **test_cardinality.py** (8 tests): Card API with min/max constraints
- **test_typename_case.py** (17 tests): Entity/Relation name formatting (snake_case, ClassCase)
- **test_attribute_typename_case.py** (17 tests): Attribute name formatting

### CRUD Tests (6 tests)
- **test_update_api.py** (6 tests): Update single/multi-value attributes

## Running Unit Tests

```bash
# Run all unit tests (default)
uv run pytest

# Run specific category
uv run pytest tests/unit/core/
uv run pytest tests/unit/attributes/
uv run pytest tests/unit/flags/
uv run pytest tests/unit/crud/

# Run specific test file
uv run pytest tests/unit/attributes/test_duration.py -v

# Run specific test
uv run pytest tests/unit/core/test_basic.py::test_entity_creation -v
```

## Test Guidelines

Unit tests should:
- **Run fast**: Complete in milliseconds
- **Be isolated**: No external dependencies (no TypeDB, no network)
- **Be deterministic**: Same input always produces same output
- **Test one thing**: Each test verifies a single behavior
- **Use clear names**: Test names describe what they verify

## Adding New Tests

When adding new tests:
1. Choose the appropriate category directory
2. Follow existing naming conventions (`test_*.py`)
3. Use descriptive test function names (`test_<what>_<when>_<expected>`)
4. Add docstrings for complex tests
5. Run `uv run pytest` to verify all tests pass

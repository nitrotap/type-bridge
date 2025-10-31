# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**type-bridge** is a Python ORM (Object-Relational Mapper) for TypeDB, designed to provide Pythonic abstractions over TypeDB's native TypeQL query language.

TypeDB is a strongly-typed database with a unique type system that includes:
- **Entities**: Independent objects with attributes
- **Relations**: Connections between entities with role players
- **Attributes**: Values owned by entities and relations

## Key TypeDB Concepts

When implementing features, keep these TypeDB-specific concepts in mind:

1. **TypeQL Schema Definition Language**: TypeDB requires schema definitions before data insertion
2. **Role Players**: Relations in TypeDB are first-class citizens with explicit role players (not just foreign keys)
3. **Attribute Ownership**: Attributes can be owned by multiple entity/relation types
4. **Inheritance**: TypeDB supports type hierarchies for entities, relations, and attributes
5. **Rule-based Inference**: TypeDB can derive facts using rules (important for query design)

## Python Version

This project requires **Python 3.13+** (see .python-version)

## Development Commands

### Package Management
```bash
uv sync --extra dev          # Install dependencies including dev tools
uv pip install -e ".[dev]"   # Install in editable mode
```

### Testing
```bash
uv run python -m pytest tests/ -v          # Run tests with verbose output
uv run python -m pytest tests/ -v -k test_name  # Run specific test
```

### Linting
```bash
uv run ruff check .          # Check code style
uv run ruff format .         # Format code
```

### Running Examples
```bash
uv run python examples/basic_usage.py
uv run python examples/advanced_usage.py
```

## Project Structure

```
type_bridge/
├── __init__.py           # Main package exports
├── attribute.py          # Attribute base class, concrete types (String, Integer, etc.),
│                         # Flag system (Key, Unique, Card), and EntityFlags/RelationFlags
├── models.py             # Base Entity and Relation classes using attribute ownership model
├── query.py              # TypeQL query builder
├── session.py            # Database connection and transaction management
├── crud.py               # EntityManager and RelationManager for CRUD ops
└── schema.py             # Schema generation and migration utilities

examples/
├── basic_usage.py        # Complete example showing attributes, entities, relations,
│                         # cardinality, and schema generation
├── pydantic_features.py  # Pydantic integration examples
└── literal_types.py      # Literal type support examples

tests/
├── test_basic.py              # Comprehensive tests for attribute API, entities, relations,
│                              # Flag system, and cardinality
├── test_cardinal_api.py       # Tests for Card API with Flag system
├── test_literal_support.py    # Tests for Literal type support
└── test_pydantic_integration.py # Tests for Pydantic integration features
```

## TypeDB ORM Design Considerations

When implementing ORM features:

1. **Mapping Challenge**: TypeDB's type system is richer than traditional ORMs - relations are not simple foreign keys
2. **TypeQL Generation**: The ORM needs to generate valid TypeQL queries from Python API calls
3. **Transaction Semantics**: TypeDB has strict transaction types (read, write) that must be respected
4. **Schema Evolution**: Consider how Python model changes map to TypeDB schema updates
5. **Role Handling**: Relations require explicit role mapping which is unique to TypeDB

## API Design Principles

TypeBridge follows TypeDB's type system closely:

1. **Attributes are independent types**: Define attributes once, reuse across entities/relations
   ```python
   class Name(String):
       pass

   class Person(Entity):
       name: Name  # Person owns 'name'

   class Company(Entity):
       name: Name  # Company also owns 'name'
   ```

2. **Use EntityFlags/RelationFlags, not dunder attributes**:
   ```python
   class Person(Entity):
       flags = EntityFlags(type_name="person")  # Clean API
       # NOT: __type_name__ = "person"  # Deprecated
   ```

3. **Use Flag system for Key/Unique/Card annotations**:
   ```python
   from type_bridge import Flag, Key, Unique, Card

   name: Name = Flag(Key)                    # @key (implies @card(1..1))
   email: Email = Flag(Unique)               # @unique (default @card(1..1))
   age: Age | None                           # @card(0..1) - PEP 604 syntax
   tags: list[Tag] = Flag(Card(min=2))       # @card(2..)
   jobs: list[Job] = Flag(Card(1, 5))        # @card(1..5)
   languages: list[Lang] = Flag(Card(max=3)) # @card(0..3) (min defaults to 0)
   ```

   **Note**: Use modern PEP 604 syntax (`X | None`) instead of `Optional[X]`.

4. **Python inheritance maps to TypeDB supertypes**:
   ```python
   class Animal(Entity):
       flags = EntityFlags(abstract=True)

   class Dog(Animal):  # Automatically: dog sub animal
       pass
   ```

5. **Cardinality semantics**:
   - `Type` → exactly one @card(1..1) - default
   - `Type | None` → zero or one @card(0..1) - use PEP 604 syntax
   - `list[Type] = Flag(Card(min=N))` → N or more @card(N..)
   - `list[Type] = Flag(Card(max=N))` → zero to N @card(0..N)
   - `list[Type] = Flag(Card(min, max))` → min to max @card(min..max)

## TypeQL Syntax Requirements

When generating TypeQL schema definitions, always use the following correct syntax:

1. **Attribute definitions**:
   ```typeql
   attribute name, value string;
   ```
   ❌ NOT: `name sub attribute, value string;`

2. **Entity definitions**:
   ```typeql
   entity person,
       owns name @key,
       owns age @card(0..1);
   ```
   ❌ NOT: `person sub entity,`

3. **Relation definitions**:
   ```typeql
   relation employment,
       relates employee,
       relates employer,
       owns salary @card(0..1);
   ```
   ❌ NOT: `employment sub relation,`

4. **Cardinality annotations**:
   - Use `..` (double dot) syntax: `@card(1..5)` ✓
   - ❌ NOT comma syntax: `@card(1,5)`
   - Unbounded max: `@card(2..)` ✓

5. **Key and Unique annotations**:
   - `@key` implies `@card(1..1)`, never output both
   - `@unique` with default `@card(1..1)`, omit `@card` annotation
   - Only output explicit `@card` when it differs from the implied cardinality

## Attribute Types

TypeBridge provides built-in attribute types that map to TypeDB's value types:

- `String` → `value string` in TypeDB
- `Integer` → `value integer` in TypeDB (renamed from `Long` to match TypeDB 3.x)
- `Double` → `value double` in TypeDB
- `Boolean` → `value boolean` in TypeDB
- `DateTime` → `value datetime` in TypeDB

Example:
```python
from type_bridge import String, Integer, Double

class Name(String):
    pass

class Age(Integer):  # Note: Integer, not Long
    pass

class Score(Double):
    pass
```

## Deprecated APIs

The following APIs are deprecated and should NOT be used:

- ❌ `Long` - Renamed to `Integer` to match TypeDB 3.x (use `Integer` instead)
- ❌ `Cardinal` - Use `Flag(Card(...))` instead
- ❌ `Min[N, Type]` - Use `list[Type] = Flag(Card(min=N))` instead
- ❌ `Max[N, Type]` - Use `list[Type] = Flag(Card(max=N))` instead
- ❌ `Range[Min, Max, Type]` - Use `list[Type] = Flag(Card(min, max))` instead
- ❌ `Optional[Type]` - Use `Type | None` (PEP 604 syntax) instead
- ❌ `Union[X, Y]` - Use `X | Y` (PEP 604 syntax) instead

These were removed or updated to provide a cleaner, more consistent API following modern Python standards.

## Internal Type System

### ModelAttrInfo Dataclass

The codebase uses `ModelAttrInfo` (defined in `models.py`) as a structured type for attribute metadata:

```python
@dataclass
class ModelAttrInfo:
    typ: type[Attribute]  # The attribute class (e.g., Name, Age)
    flags: AttributeFlags  # Metadata (Key, Unique, Card)
```

**IMPORTANT**: Always use dataclass attribute access, never dictionary-style access:

```python
# ✅ CORRECT
owned_attrs = Entity.get_owned_attributes()
for field_name, attr_info in owned_attrs.items():
    attr_class = attr_info.typ
    flags = attr_info.flags

# ❌ WRONG - Never use dict-style access
attr_class = attr_info["type"]   # Will fail!
flags = attr_info["flags"]       # Will fail!
```

### Modern Python Type Hints

The project follows modern Python typing standards (Python 3.12+):

1. **PEP 604**: Use `X | Y` instead of `Union[X, Y]`
   ```python
   # ✅ Modern
   age: int | str | None

   # ❌ Deprecated
   from typing import Union, Optional
   age: Optional[Union[int, str]]
   ```

2. **PEP 695**: Use type parameter syntax for generics
   ```python
   # ✅ Modern (Python 3.12+)
   class EntityManager[E: Entity]:
       ...

   # ❌ Old style (still works but verbose)
   from typing import Generic, TypeVar
   E = TypeVar("E", bound=Entity)
   class EntityManager(Generic[E]):
       ...
   ```

3. **No linter suppressions**: Code should pass `ruff` and `pyright` without needing `# noqa` or `# type: ignore` comments

## Type Checking and Static Analysis

TypeBridge uses PEP-681 `@dataclass_transform` decorators on Entity and Relation classes to improve type checker support. This provides:

- Type checker recognition of `Flag()` as a valid field default
- Automatic `__init__` signature inference from class annotations
- Better IDE autocomplete and type hints

### Type Checking Limitations

Due to the dynamic nature of Pydantic validation and TypeDB's flexible type system, there are some known type checking limitations:

1. **Constructor arguments**: Type checkers may show warnings when passing literal values to constructors:
   ```python
   # Type checker may warn, but this works at runtime via Pydantic
   person = Person(name="Alice", age=30)  # ⚠️ Type checker warning
   ```

   **Why**: Type checkers see `name: Name` and expect a `Name` instance, but Pydantic's `__get_pydantic_core_schema__` accepts both `str` and `Name` at runtime.

   **Workaround**: Use `# type: ignore[arg-type]` comments if needed, or pass properly typed instances.

2. **Runtime vs. Static Analysis**: The `__init_subclass__` hook rewrites annotations at runtime to support union types (`str | Name`), but type checkers perform static analysis before this happens.

### Minimal `Any` Usage

The project minimizes `Any` usage for type safety:
- `Flag()` accepts `Any` for parameters (to handle type aliases like `Key` and `Unique`)
- `Flag()` returns `AttributeFlags` (used as field default)
- All `__get_pydantic_core_schema__` methods use proper TypeVars (`StrValue`, `IntValue`, etc.)
- No other `Any` types in the core attribute system

## Dependencies

The project requires:
- `typedb-driver==3.5.5`: Official Python driver for TypeDB connectivity
- `pydantic>=2.0`: For validation and type coercion
- Uses Python's built-in type hints and dataclass-like patterns

## TypeDB Driver 3.5.5 API Notes

The driver API for version 3.5.5 differs from earlier versions:

1. **No separate sessions**: Transactions are created directly on the driver
   ```python
   driver.transaction(database_name, TransactionType.READ)
   ```

2. **Single query method**: `transaction.query(query_string)` returns `Promise[QueryAnswer]`
   - Must call `.resolve()` to get results
   - Works for all query types (define, insert, match, fetch, delete)

3. **TransactionType enum**: `READ`, `WRITE`, `SCHEMA`

4. **Authentication**: Requires `Credentials(username, password)` even for local development

## Code Quality Standards

The project maintains high code quality standards with zero tolerance for technical debt:

### Linting and Type Checking

All code must pass these checks without errors or warnings:

```bash
# Ruff - Python linter and formatter (must pass with 0 errors)
uv run ruff check .          # Check for style issues
uv run ruff format .         # Auto-format code

# Pyright - Static type checker (must pass with 0 errors, 0 warnings)
uv run pyright type_bridge/  # Check core library
uv run pyright examples/     # Check examples
uv run pyright tests/        # Check tests (note: intentional validation errors are OK)
```

### Code Quality Requirements

1. **No linter suppressions**: Do not use `# noqa`, `# type: ignore`, or similar comments
   - Exception: Tests intentionally checking validation failures may show type warnings

2. **Modern Python syntax**:
   - Use PEP 604 (`X | Y`) instead of `Union[X, Y]`
   - Use PEP 695 type parameters (`class Foo[T]:`) when possible
   - Use `X | None` instead of `Optional[X]`

3. **Consistent ModelAttrInfo usage**:
   - Always use `attr_info.typ` and `attr_info.flags`
   - Never use dict-style access like `attr_info["type"]`

4. **Import organization**: Imports must be sorted and organized (ruff handles this automatically)

### Testing Requirements

All tests must pass:
```bash
uv run python -m pytest tests/ -v  # All 50 tests must pass
```

When adding new features:
- Add corresponding tests in `tests/`
- Ensure examples in `examples/` demonstrate the feature
- Update CLAUDE.md with usage guidelines
- Run all quality checks before committing

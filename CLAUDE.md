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
├── attribute.py          # Attribute base class, concrete types (String, Long, etc.),
│                         # and flags (Card, Key, Unique, EntityFlags, RelationFlags)
├── models.py             # Base Entity and Relation classes using attribute ownership model
├── query.py              # TypeQL query builder
├── session.py            # Database connection and transaction management
├── crud.py               # EntityManager and RelationManager for CRUD ops
└── schema.py             # Schema generation and migration utilities

examples/
└── basic_usage.py        # Complete example showing attributes, entities, relations,
                          # cardinality, and schema generation

tests/
└── test_basic.py         # Comprehensive tests for attribute API, entities, relations,
                          # Flag system, and Card cardinality
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

3. **Use Flag system for attribute annotations**:
   ```python
   name: Name = Flag(Key, Card(1))  # @key @card(1,1)
   age: Age = Flag(Card(0, 1))      # @card(0,1)
   # NOT: NameKey = Key(Name)  # Deprecated
   ```

4. **Python inheritance maps to TypeDB supertypes**:
   ```python
   class Animal(Entity):
       flags = EntityFlags(abstract=True)

   class Dog(Animal):  # Automatically: dog sub animal
       pass
   ```

5. **Card cardinality semantics**:
   - `Card(1)` → exactly one (1..1)
   - `Card(min=0)` → zero or more (0..∞)
   - `Card(max=5)` → one to five (1..5)
   - `Card(1, 3)` → one to three (1..3)

## Dependencies

The project requires:
- `typedb-driver==3.5.5`: Official Python driver for TypeDB connectivity
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

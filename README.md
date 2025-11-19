# TypeBridge

[![CI](https://github.com/ds1sqe/type_bridge/actions/workflows/ci.yml/badge.svg)](https://github.com/ds1sqe/type_bridge/actions/workflows/ci.yml)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![TypeDB 3.x](https://img.shields.io/badge/TypeDB-3.x-orange.svg)](https://github.com/typedb/typedb)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A modern, Pythonic ORM for [TypeDB](https://github.com/typedb/typedb) with an Attribute-based API that aligns with TypeDB's type system.

## Features

- **True TypeDB Semantics**: Attributes are independent types that entities and relations own
- **Complete Type Support**: All TypeDB value types - String, Integer, Double, Decimal, Boolean, Date, DateTime, DateTimeTZ, Duration
- **Flag System**: Clean API for `@key`, `@unique`, and `@card` annotations
- **Flexible Cardinality**: Express any cardinality constraint with `Card(min, max)`
- **Pydantic Integration**: Built on Pydantic v2 for automatic validation, serialization, and type safety
- **Type-Safe**: Full Python type hints and IDE autocomplete support
- **Declarative Models**: Define entities and relations using Python classes
- **Automatic Schema Generation**: Generate TypeQL schemas from your Python models
- **Schema Conflict Detection**: Automatic detection of breaking schema changes to prevent data loss
- **Data Validation**: Automatic type checking and coercion via Pydantic, including keyword validation
- **JSON Support**: Seamless JSON serialization/deserialization
- **CRUD Operations**: Full CRUD with fetching API (get, filter, all, update) for entities and relations
- **Query Builder**: Pythonic interface for building TypeQL queries

## Installation

```bash
# Clone the repository
git clone https://github.com/ds1sqe/type_bridge.git
cd type_bridge

# Install with uv
uv sync

# Or with pip
pip install -e .

# Or add to project with uv
uv add type-bridge
```

## Quick Start

### 1. Define Attribute Types

TypeBridge supports all TypeDB value types:

```python
from type_bridge import String, Integer, Double, Decimal, Boolean, Date, DateTime, DateTimeTZ, Duration

class Name(String):
    pass

class Age(Integer):
    pass

class Balance(Decimal):  # High-precision fixed-point numbers
    pass

class BirthDate(Date):  # Date-only values
    pass

class UpdatedAt(DateTimeTZ):  # Timezone-aware datetime
    pass
```

### 2. Define Entities

```python
from type_bridge import Entity, TypeFlags, Flag, Key, Card

class Person(Entity):
    flags = TypeFlags(type_name="person")  # Optional, defaults to lowercase class name

    # Use Flag() for key/unique markers and Card for cardinality
    name: Name = Flag(Key)                   # @key (implies @card(1..1))
    age: Age | None                          # @card(0..1) - optional field
    email: Email                             # @card(1..1) - default cardinality
    tags: list[Tag] = Flag(Card(min=2))      # @card(2..) - two or more
```

### 3. Create Instances

```python
# Create entity instances with attribute values
alice = Person(
    name=Name("Alice"),
    age=Age(30),
    email=Email("alice@example.com")
)

# Pydantic handles validation and type coercion automatically
print(alice.name.value)  # "Alice"
```

### 4. Work with Data

```python
from type_bridge import Database, SchemaManager

# Connect to database
db = Database(address="localhost:1729", database="mydb")
db.connect()
db.create_database()

# Define schema
schema_manager = SchemaManager(db)
schema_manager.register(Person, Company, Employment)
schema_manager.sync_schema()

# Insert entities - use typed instances
alice = Person(
    name=Name("Alice"),
    age=Age(30),
    email=Email("alice@example.com")
)
Person.manager(db).insert(alice)

# Insert relations - use typed instances
employment = Employment(
    employee=alice,
    employer=techcorp,
    position=Position("Engineer"),
    salary=Salary(100000)
)
Employment.manager(db).insert(employment)
```

### 5. Cardinality Constraints

```python
from type_bridge import Card, Flag

class Person(Entity):
    flags = TypeFlags(type_name="person")

    # Cardinality options:
    name: Name                              # @card(1..1) - exactly one (default)
    age: Age | None                         # @card(0..1) - zero or one
    tags: list[Tag] = Flag(Card(min=2))     # @card(2..) - two or more (unbounded)
    skills: list[Skill] = Flag(Card(max=5)) # @card(0..5) - zero to five
    jobs: list[Job] = Flag(Card(1, 3))      # @card(1..3) - one to three
```

### 6. Define Relations

```python
from type_bridge import Relation, TypeFlags, Role

class Employment(Relation):
    flags = TypeFlags(type_name="employment")

    # Define roles with type-safe Role[T] syntax
    employee: Role[Person] = Role("employee", Person)
    employer: Role[Company] = Role("employer", Company)

    # Relations can own attributes
    position: Position                   # @card(1..1)
    salary: Salary | None                # @card(0..1)
```

### 7. Using Python Inheritance

```python
class Animal(Entity):
    flags = TypeFlags(abstract=True)  # Abstract entity
    name: Name

class Dog(Animal):  # Automatically: dog sub animal in TypeDB
    breed: Breed
```

## Documentation

- **Complete API Reference**: [docs/ATTRIBUTE_API.md](docs/ATTRIBUTE_API.md)
- **Project Guidance**: [CLAUDE.md](CLAUDE.md) - Development guide and TypeDB concepts

## Pydantic Integration

TypeBridge is built on Pydantic v2, giving you powerful features:

```python
class Person(Entity):
    flags = TypeFlags(type_name="person")
    name: Name = Flag(Key)
    age: Age

# Automatic validation and type coercion
alice = Person(name=Name("Alice"), age=Age(30))

# JSON serialization
json_data = alice.model_dump_json()

# JSON deserialization
bob = Person.model_validate_json('{"name": "Bob", "age": 25}')

# Model copying
alice_copy = alice.model_copy(update={"age": Age(31)})
```

## Running Examples

TypeBridge includes comprehensive examples organized by complexity:

```bash
# Basic CRUD examples (start here!)
uv run python examples/basic/crud_01_define.py  # Schema definition
uv run python examples/basic/crud_02_insert.py  # Data insertion
uv run python examples/basic/crud_03_read.py    # Fetching API
uv run python examples/basic/crud_04_update.py  # Update operations

# Advanced examples
uv run python examples/advanced/schema_01_manager.py     # Schema operations
uv run python examples/advanced/schema_02_comparison.py  # Schema comparison
uv run python examples/advanced/schema_03_conflict.py    # Conflict detection
uv run python examples/advanced/pydantic_features.py     # Pydantic integration
uv run python examples/advanced/type_safety.py           # Literal types
uv run python examples/advanced/reserved_words_validation.py  # Keyword validation
```

## Running Tests

TypeBridge uses a two-tier testing approach with **100% test pass rate**:

```bash
# Unit tests (fast, no external dependencies) - DEFAULT
uv run pytest                              # Run 264 unit tests (0.3s)
uv run pytest tests/unit/attributes/ -v   # Test all 9 attribute types
uv run pytest tests/unit/core/ -v         # Test core functionality
uv run pytest tests/unit/flags/ -v        # Test flag system

# Integration tests (requires running TypeDB server)
# Option 1: Use Docker (recommended)
./test-integration.sh                     # Starts Docker, runs tests, stops Docker

# Option 2: Use existing TypeDB server
USE_DOCKER=false uv run pytest -m integration -v  # Run 102 integration tests (~18s)

# All tests
uv run pytest -m "" -v                    # Run all 366 tests
./test.sh                                 # Run full test suite with detailed output
./check.sh                                # Run linting and type checking
```

## Requirements

- Python 3.13+
- TypeDB 3.x server (fully compatible)
- typedb-driver==3.5.5
- pydantic>=2.0.0
- isodate==0.7.2 (for Duration type support)

## What's New in v0.4.4

### Bug Fixes
- ✅ **Fixed inherited attributes in CRUD operations**: Insert and fetch now properly include inherited attributes from parent Entity/Relation classes
- ✅ Added `get_all_attributes()` method to collect attributes from entire class hierarchy

### API Improvements
- ✅ **Unified TypeFlags API**: Removed deprecated `EntityFlags` and `RelationFlags` aliases - use `TypeFlags` for both
- ✅ All examples updated to use unified TypeFlags API

### Testing & Quality
- ✅ **366 comprehensive tests** (264 unit, 102 integration) - 100% pass rate
- ✅ Docker integration for automated test setup
- ✅ Zero errors from Ruff and Pyright

### Complete Type System
- ✅ All 9 TypeDB value types: String, Integer, Double, Decimal, Boolean, Date, DateTime, DateTimeTZ, Duration
- ✅ Temporal type conversions (DateTime ↔ DateTimeTZ with timezone handling)
- ✅ ISO 8601 Duration support with calendar-aware arithmetic

### Production-Ready Features
- ✅ Type-safe CRUD operations with inheritance support
- ✅ Chainable query builder with limit/offset/sort
- ✅ Schema conflict detection and validation
- ✅ Duplicate attribute type detection

## License

MIT License

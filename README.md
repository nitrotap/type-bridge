# TypeBridge

A modern, Pythonic ORM for TypeDB with an Attribute-based API that aligns with TypeDB's type system.

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
from type_bridge import Entity, EntityFlags, Flag, Key, Card

class Person(Entity):
    flags = EntityFlags(type_name="person")  # Optional, defaults to lowercase class name

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
    flags = EntityFlags(type_name="person")

    # Cardinality options:
    name: Name                              # @card(1..1) - exactly one (default)
    age: Age | None                         # @card(0..1) - zero or one
    tags: list[Tag] = Flag(Card(min=2))     # @card(2..) - two or more (unbounded)
    skills: list[Skill] = Flag(Card(max=5)) # @card(0..5) - zero to five
    jobs: list[Job] = Flag(Card(1, 3))      # @card(1..3) - one to three
```

### 6. Define Relations

```python
from type_bridge import Relation, RelationFlags, Role

class Employment(Relation):
    flags = RelationFlags(type_name="employment")

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
    flags = EntityFlags(abstract=True)  # Abstract entity
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
    flags = EntityFlags(type_name="person")
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

TypeBridge uses a two-tier testing approach:

```bash
# Unit tests (fast, no external dependencies) - DEFAULT
uv run pytest                              # Run 240+ unit tests
uv run pytest tests/unit/attributes/ -v   # Test attribute types
uv run pytest tests/unit/core/ -v         # Test core functionality
uv run pytest tests/unit/flags/ -v        # Test flag system

# Integration tests (requires running TypeDB server)
# First: typedb server
uv run pytest -m integration -v           # Run 27 integration tests

# All tests
uv run pytest -m "" -v                    # Run all 267+ tests
```

## Requirements

- Python 3.13+
- TypeDB 3.x server
- typedb-driver==3.5.5
- pydantic>=2.0.0
- isodate==0.7.2 (for Duration type support)

## What's New in v0.3.0

### Complete Type System
- ✅ All TypeDB value types: String, Integer, Double, Decimal, Boolean, Date, DateTime, DateTimeTZ, Duration
- ✅ Temporal type conversions (DateTime ↔ DateTimeTZ with timezone handling)
- ✅ ISO 8601 Duration support with calendar-aware arithmetic

### Enhanced Validation & Safety
- ✅ Comprehensive keyword validation for reserved TypeDB/TypeQL words
- ✅ Improved schema conflict detection and comparison
- ✅ Type name case formatting options (snake_case, kebab-case, etc.)

### Testing Infrastructure
- ✅ 267+ comprehensive tests (240 unit, 27 integration)
- ✅ Organized test structure by functionality (core, attributes, flags, crud)
- ✅ Integration test suite with TypeDB server

### Improved API
- ✅ Type-safe update API for single and multi-value attributes
- ✅ Better organized examples (basic vs advanced)
- ✅ Enhanced documentation with detailed type guides

## License

MIT License

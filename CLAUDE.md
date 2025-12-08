# Project Overview

**type-bridge** is a Python ORM (Object-Relational Mapper) for TypeDB, designed to provide Pythonic abstractions over TypeDB's native TypeQL query language.

TypeDB is a strongly-typed database with a unique type system that includes:
- **Entities**: Independent objects with attributes
- **Relations**: Connections between entities with role players
- **Attributes**: Values owned by entities and relations

## Python Version

This project requires **Python 3.13+** (see .python-version)

## Quick Start

```bash
# Install dependencies
uv sync --extra dev

# Run tests
uv run pytest                    # Unit tests (fast, no deps)
./test-integration.sh            # Integration tests (with Docker)

Podman users: integration tests work with Podman too—set `CONTAINER_TOOL=podman` (or `podman-compose`) so the fixtures call `podman compose ...` instead of Docker. Either runtime works as long as a compatible *compose* subcommand is available and the TypeDB container can start.

# Run examples
uv run python examples/basic/crud_01_define.py
```

## Project Structure

```
type_bridge/
├── __init__.py           # Main package exports
├── attribute/            # Modular attribute system
│   ├── base.py           # Abstract Attribute base class
│   ├── string.py         # String attribute
│   ├── integer.py        # Integer attribute
│   ├── double.py         # Double attribute
│   ├── boolean.py        # Boolean attribute
│   ├── datetime.py       # DateTime attribute
│   └── flags.py          # Flag system (Key, Unique, Card, TypeFlags)
├── models/               # Base Entity and Relation classes (modularized)
│   ├── __init__.py       # Module exports
│   ├── base.py           # Base model functionality
│   ├── entity.py         # Entity class
│   ├── relation.py       # Relation class
│   ├── role.py           # Role definitions
│   └── utils.py          # Model utilities
├── query.py              # TypeQL query builder
├── session.py            # Database connection and transaction management
├── crud/                 # CRUD operations (modularized)
│   ├── __init__.py       # Module exports (backward compatible)
│   ├── base.py           # Type variables (E, R)
│   ├── utils.py          # Shared utilities (format_value, is_multi_value_attribute)
│   ├── entity/           # Entity CRUD operations
│   │   ├── __init__.py   # Entity module exports
│   │   ├── manager.py    # EntityManager class
│   │   ├── query.py      # EntityQuery chainable queries
│   │   └── group_by.py   # GroupByQuery for aggregations
│   └── relation/         # Relation CRUD operations
│       ├── __init__.py   # Relation module exports
│       ├── manager.py    # RelationManager class
│       ├── query.py      # RelationQuery chainable queries
│       └── group_by.py   # RelationGroupByQuery for aggregations
└── schema/               # Modular schema management
    ├── manager.py        # SchemaManager for schema operations
    ├── info.py           # SchemaInfo container
    ├── diff.py           # SchemaDiff for comparison
    ├── migration.py      # MigrationManager for migrations
    └── exceptions.py     # SchemaConflictError for conflict detection

examples/
├── basic/                # Basic CRUD examples (start here!)
│   ├── crud_01_define.py
│   ├── crud_02_insert.py
│   ├── crud_03_read.py
│   └── crud_04_update.py
└── advanced/             # Advanced features
    ├── schema_01_manager.py
    ├── schema_02_comparison.py
    ├── schema_03_conflict.py
    ├── pydantic_features.py
    ├── type_safety.py
    └── string_representation.py

tests/
├── unit/                 # Unit tests (fast, isolated, no external dependencies)
│   ├── core/             # Core functionality tests
│   ├── attributes/       # Attribute type tests
│   ├── flags/            # Flag system tests
│   ├── expressions/      # Query expression API
│   └── validation/       # Reserved word and keyword validation
└── integration/          # Integration tests (require running TypeDB)
    ├── crud/             # CRUD operations
    ├── queries/          # Query builder tests
    └── schema/           # Schema operations
```

## Dependencies

The project requires:
- `typedb-driver==3.7.0`: Official Python driver for TypeDB connectivity
- `pydantic>=2.0`: For validation and type coercion
- Uses Python's built-in type hints and dataclass-like patterns

## Documentation

### User Documentation
- **[README.md](README.md)** - Quick start guide for users

### Development Guides
- **[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)** - Development setup, commands, code quality standards
- **[docs/TESTING.md](docs/TESTING.md)** - Testing strategy, patterns, and execution

### TypeDB Integration
- **[docs/TYPEDB.md](docs/TYPEDB.md)** - TypeDB concepts, driver API, TypeQL syntax, 3.x changes
- **[docs/ABSTRACT_TYPES.md](docs/ABSTRACT_TYPES.md)** - Abstract types and interface hierarchies in TypeDB

### Architecture & Internals
- **[docs/INTERNALS.md](docs/INTERNALS.md)** - Internal type system, ModelAttrInfo, modern Python standards

### API Reference
- **[docs/api/README.md](docs/api/README.md)** - API overview and quick reference
- **[docs/api/attributes.md](docs/api/attributes.md)** - Attribute types and value types
- **[docs/api/entities.md](docs/api/entities.md)** - Entity definition and ownership
- **[docs/api/relations.md](docs/api/relations.md)** - Relations, roles, and role players
- **[docs/api/abstract_types.md](docs/api/abstract_types.md)** - Abstract types implementation and patterns
- **[docs/api/cardinality.md](docs/api/cardinality.md)** - Card API and Flag system
- **[docs/api/crud.md](docs/api/crud.md)** - CRUD operations and managers
- **[docs/api/queries.md](docs/api/queries.md)** - Query expressions and aggregations
- **[docs/api/schema.md](docs/api/schema.md)** - Schema management and conflict detection
- **[docs/api/validation.md](docs/api/validation.md)** - Pydantic integration and type safety

## Getting Help

- `/help`: Get help with using Claude Code
- Report issues at: https://github.com/anthropics/claude-code/issues

## Quick Reference

### Basic Usage Pattern

```python
from type_bridge import Entity, TypeFlags, AttributeFlags, String, Integer, Flag, Key

# 1. Define attribute types
class Name(String):
    pass

# Override attribute type name (for legacy schemas)
class EmailAddress(String):
    flags = AttributeFlags(name="email")  # TypeDB: attribute email, value string;

class Age(Integer):
    pass

# 2. Define entity with ownership
class Person(Entity):
    flags = TypeFlags(name="person")
    name: Name = Flag(Key)
    email: EmailAddress
    age: Age | None = None  # Optional field

# 3. Create instances (keyword arguments required)
alice = Person(name=Name("Alice"), email=EmailAddress("alice@example.com"), age=Age(30))

# 4. CRUD operations
person_manager = Person.manager(db)
person_manager.insert(alice)
persons = person_manager.all()
```

### Key Concepts

1. **Attributes are independent types** - Define once, reuse across entities/relations
2. **Use TypeFlags for entities/relations** - Clean API with `TypeFlags(name="person")`
3. **Use AttributeFlags for attributes** - Override names with `AttributeFlags(name="person_name")` or use case formatting with `AttributeFlags(case=TypeNameCase.SNAKE_CASE)`
4. **Use Flag system** - `Flag(Key)`, `Flag(Unique)`, `Flag(Card(min=2))`
5. **Python inheritance maps to TypeDB supertypes** - Use `abstract=True` for abstract types
6. **Keyword-only arguments** - All Entity/Relation constructors require keyword arguments

For detailed documentation, see the links above.

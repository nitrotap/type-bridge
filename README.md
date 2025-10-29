# TypeBridge

A modern, Pythonic ORM for TypeDB with an Attribute-based API that aligns with TypeDB's type system.

## Features

- **True TypeDB Semantics**: Attributes are independent types that entities and relations own
- **Type-Safe**: Full Python type hints and IDE autocomplete support
- **Declarative Models**: Define entities and relations using Python classes
- **Automatic Schema Generation**: Generate TypeQL schemas from your Python models
- **CRUD Operations**: Simple managers for entity and relation operations
- **Query Builder**: Pythonic interface for building TypeQL queries
- **Clean API**: No Pydantic conflicts, simple dict-based value storage

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/type_bridge.git
cd type_bridge

# Install with uv
uv sync

# Or with pip
pip install -e .
```

## Quick Start

### 1. Define Attribute Types

```python
from type_bridge import String, Long, Key

class Name(String):
    pass

class Age(Long):
    pass

NameKey = Key(Name)  # Mark as key attribute
```

### 2. Define Entities

```python
from type_bridge import Entity

class Person(Entity):
    __type_name__ = "person"
    
    name: NameKey  # Person owns 'name' as @key
    age: Age       # Person owns 'age'
```

### 3. Work with Data

```python
from type_bridge import Database, SchemaManager, EntityManager

# Setup
db = Database(address="localhost:1729", database="mydb")
schema_manager = SchemaManager(db)
schema_manager.register(Person)
schema_manager.sync_schema(force=True)

# CRUD
person_manager = EntityManager(db, Person)
alice = person_manager.create(name="Alice", age=30)
all_people = person_manager.all()
```

## Documentation

See [ATTRIBUTE_API.md](ATTRIBUTE_API.md) for complete documentation.

## Running Examples

```bash
uv run python examples/basic_usage.py
```

## Running Tests

```bash
uv run pytest tests/ -v
```

## Requirements

- Python 3.13+
- TypeDB 2.x or 3.x
- typedb-driver==3.5.5

## License

MIT License

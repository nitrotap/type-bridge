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
from type_bridge import String, Long

class Name(String):
    pass

class Age(Long):
    pass
```

### 2. Define Entities

```python
from type_bridge import Entity, EntityFlags, Flag, Key, Card

class Person(Entity):
    flags = EntityFlags(type_name="person")  # Optional, defaults to lowercase class name

    name: Name = Flag(Key, Card(1))  # Person owns 'name' as @key @card(1,1)
    age: Age = Flag(Card(0, 1))      # Person owns 'age' as @card(0,1) - optional
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

### 4. Cardinality Constraints

```python
from type_bridge import Card

# Card semantics:
Card(1)          # @card(1,1) - exactly one
Card(min=0)      # @card(0) - zero or more (unbounded)
Card(max=5)      # @card(1,5) - one to five
Card(1, 3)       # @card(1,3) - one to three
Card(0, 5)       # @card(0,5) - zero to five
```

### 5. Using Python Inheritance

```python
class Animal(Entity):
    flags = EntityFlags(abstract=True)  # Abstract entity
    name: Name

class Dog(Animal):  # Automatically: dog sub animal in TypeDB
    breed: Breed
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

# TypeBridge

A modern, Pythonic ORM for TypeDB with an Attribute-based API that aligns with TypeDB's type system.

## Features

- **True TypeDB Semantics**: Attributes are independent types that entities and relations own
- **Flag System**: Clean API for `@key`, `@unique`, and `@card` annotations
- **Flexible Cardinality**: Express any cardinality constraint with `Card(min, max)`
- **Pydantic Integration**: Built on Pydantic v2 for automatic validation, serialization, and type safety
- **Type-Safe**: Full Python type hints and IDE autocomplete support
- **Declarative Models**: Define entities and relations using Python classes
- **Automatic Schema Generation**: Generate TypeQL schemas from your Python models
- **Data Validation**: Automatic type checking and coercion via Pydantic
- **JSON Support**: Seamless JSON serialization/deserialization
- **CRUD Operations**: Simple managers for entity and relation operations
- **Query Builder**: Pythonic interface for building TypeQL queries

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
from type_bridge import String, Integer

class Name(String):
    pass

class Age(Integer):
    pass
```

### 2. Define Entities

```python
from typing import Optional
from type_bridge import Entity, EntityFlags, Flag, Key, Card

class Person(Entity):
    flags = EntityFlags(type_name="person")  # Optional, defaults to lowercase class name

    # Use Flag() for key/unique markers and Card for cardinality
    name: Name = Flag(Key)                   # @key (implies @card(1..1))
    age: Optional[Age]                       # @card(0..1) - optional field
    email: Email                             # @card(1..1) - default cardinality
    tags: list[Tag] = Flag(Card(min=2))      # @card(2..) - two or more
```

### 3. Create Instances

```python
# Two ways to create instances:

# Option 1: Attribute instances (fully type-safe, zero pyright errors)
alice = Person(
    name=Name("Alice"),
    age=Age(30),
    email=Email("alice@example.com")
)

# Option 2: Raw values (convenient, may show pyright warnings)
bob = Person(name="Bob", age=25, email=Email("bob@example.com"))

# Both work identically at runtime!
```

### 4. Work with Data

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
from typing import Optional
from type_bridge import Card, Flag

class Person(Entity):
    flags = EntityFlags(type_name="person")

    # Cardinality options:
    name: Name                              # @card(1..1) - exactly one (default)
    age: Optional[Age]                      # @card(0..1) - zero or one
    tags: list[Tag] = Flag(Card(min=2))     # @card(2..) - two or more (unbounded)
    skills: list[Skill] = Flag(Card(max=5)) # @card(0..5) - zero to five (min defaults to 0)
    jobs: list[Job] = Flag(Card(1, 3))      # @card(1..3) - one to three
```

### 5. Define Relations

```python
from typing import ClassVar
from type_bridge import Relation, RelationFlags, Role

class Employment(Relation):
    flags = RelationFlags(type_name="employment")

    # Define roles with ClassVar
    employee: ClassVar[Role] = Role("employee", Person)
    employer: ClassVar[Role] = Role("employer", Company)

    # Relations can own attributes too
    position: Position                   # @card(1..1)
    salary: Optional[Salary]             # @card(0..1)
```

### 6. Using Python Inheritance

```python
class Animal(Entity):
    flags = EntityFlags(abstract=True)  # Abstract entity
    name: Name

class Dog(Animal):  # Automatically: dog sub animal in TypeDB
    breed: Breed
```

## Documentation

See [ATTRIBUTE_API.md](ATTRIBUTE_API.md) for complete documentation.

## Pydantic Integration

TypeBridge is built on Pydantic v2, giving you powerful features out of the box:

```python
from typing import Optional

class Person(Entity):
    flags = EntityFlags(type_name="person")
    name: Name = Flag(Key)
    age: Age = Age(0)

# Automatic validation
alice = Person(name="Alice", age="30")  # String coerced to int

# JSON serialization
json_data = alice.model_dump_json()

# JSON deserialization
bob = Person.model_validate_json('{"name": "Bob", "age": 25}')

# Model copying
alice_copy = alice.model_copy(update={"age": 31})
```

## Running Examples

```bash
uv run python examples/basic_usage.py
uv run python examples/pydantic_features.py
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

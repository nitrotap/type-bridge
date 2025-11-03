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

# Insert entities
alice = Person.manager(db).insert(
    name="Alice",
    age=30,
    email="alice@example.com"
)

# Insert relations
employment = Employment.manager(db).insert(
    role_players={"employee": alice, "employer": techcorp},
    attributes={"position": "Engineer", "salary": 100000}
)
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

See [ATTRIBUTE_API.md](ATTRIBUTE_API.md) for complete documentation.

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

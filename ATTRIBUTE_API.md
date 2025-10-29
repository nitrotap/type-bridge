# New Attribute-Based API

## Overview

The new Attribute-based API aligns TypeBridge more closely with TypeDB's actual type system, where **attributes are base types** that **entities and relations own**.

## Design Principles

### TypeDB's Model
In TypeDB:
1. **Attributes** are independent value types (e.g., `name`, `email`, `age`)
2. **Entities** and **relations** declare **ownership** of these attributes
3. Multiple types can own the same attribute

### New TypeBridge API
```python
# Step 1: Define attribute types (base types)
from type_bridge import Annotated, String, Long, Entity, EntityFlags, Flag, Key, Card

class Name(String):
    """Name attribute - can be owned by multiple entity types."""
    pass

class Age(Long):
    """Age attribute."""
    pass

# Step 2: Entities OWN attributes via type annotations with Flag
class Person(Entity):
    flags = EntityFlags(type_name="person")  # Optional, defaults to class name

    # Use Flag() as default value to specify attribute annotations
    name: Name = Flag(Key, Card(1))  # @key @card(1,1)
    age: Age = Flag(Card(0, 1))      # @card(0,1)
    email: Email                      # No special flags
```

## Key Components

### 1. Attribute Base Class (`attribute.py`)

```python
class Attribute(ABC):
    """Base class for all TypeDB attributes."""
    value_type: ClassVar[str]  # string, long, double, boolean, datetime

    @classmethod
    def get_attribute_name(cls) -> str:
        """Returns the TypeDB attribute name (lowercase class name)."""

    @classmethod
    def to_schema_definition(cls) -> str:
        """Generates TypeQL schema: 'name sub attribute, value string;'"""
```

### 2. Concrete Attribute Types

```python
class String(Attribute):
    value_type = "string"

class Long(Attribute):
    value_type = "long"

class Double(Attribute):
    value_type = "double"

class Boolean(Attribute):
    value_type = "boolean"

class DateTime(Attribute):
    value_type = "datetime"
```

**Tip**: Combine with `Literal` for type-safe enum-like values:
```python
from typing import Literal

class Status(String):
    pass

# Type checker provides autocomplete for "active", "inactive", "pending"
status: Literal["active", "inactive", "pending"] | Status
```

**Type Checker Support**: TypeBridge automatically rewrites field annotations at runtime to support Pydantic validation:

When you write:
```python
class Name(String):
    pass

class Person(Entity):
    name: Name  # You write this
```

TypeBridge automatically converts it to (at runtime):
```python
name: str | Name  # Runtime annotation after __init_subclass__
```

This happens during class creation in `__init_subclass__`, so:
- `String` subclass fields become `str | FieldType`
- `Long` subclass fields become `int | FieldType`
- `Double` subclass fields become `float | FieldType`
- `Boolean` subclass fields become `bool | FieldType`
- `DateTime` subclass fields become `datetime | FieldType`

### Pyright Support

TypeBridge includes `.pyi` type stub files that tell Pyright the correct signatures for `Entity` and `Relation` `__init__` methods. This means:

✅ **No Pyright warnings** when passing base types:
```python
class Name(String):
    pass

class Person(Entity):
    name: Name

# No warnings - Pyright understands this works!
alice = Person(name="Alice", age=30)
```

The type stubs declare `__init__(**kwargs: Any)`, which tells Pyright that any keyword arguments are accepted. This matches the runtime behavior where TypeBridge automatically rewrites annotations to union types.

**Note**: If you already use a union type (e.g., `Literal["x"] | Status`), TypeBridge won't modify it.

### 3. Entity Ownership Model (`models.py`)

```python
class Entity:
    """Base class for entities."""
    _flags: ClassVar[EntityFlags] = EntityFlags()
    _owned_attrs: ClassVar[dict[str, dict[str, Any]]] = {}

    def __init_subclass__(cls):
        """Automatically collects EntityFlags and owned attributes from type annotations."""

    @classmethod
    def get_type_name(cls) -> str:
        """Returns type name from flags or lowercase class name."""

    @classmethod
    def get_supertype(cls) -> str | None:
        """Returns supertype from Python inheritance."""

    @classmethod
    def get_owned_attributes(cls) -> dict[str, dict[str, Any]]:
        """Returns mapping of field names to attribute info (type + flags)."""

    @classmethod
    def to_schema_definition(cls) -> str:
        """Generates entity schema with ownership declarations and annotations."""
```

## Complete Example

```python
from typing import ClassVar
from type_bridge import (
    Annotated,
    String, Long,
    Entity, EntityFlags,
    Relation, RelationFlags, Role,
    Flag, Key, Card
)

# Define attribute types
class Name(String):
    pass

class Email(String):
    pass

class Age(Long):
    pass

class Salary(Long):
    pass

class Position(String):
    pass

# Define entities with attribute ownership and flags
class Person(Entity):
    flags = EntityFlags(type_name="person")

    name: Name = Flag(Key, Card(1))   # @key @card(1,1)
    age: Age = Flag(Card(0, 1))       # @card(0,1)
    email: Email = Flag(Card(1))      # @card(1,1)

class Company(Entity):
    flags = EntityFlags(type_name="company")

    name: Name = Flag(Key, Card(1))  # @key @card(1,1)

# Define relations with attribute ownership
class Employment(Relation):
    flags = RelationFlags(type_name="employment")

    employee: ClassVar[Role] = Role("employee", Person)
    employer: ClassVar[Role] = Role("employer", Company)

    position: Position = Flag(Card(1))      # @card(1,1)
    salary: Salary = Flag(Card(0, 1))       # @card(0,1)
```

## Generated Schema

The above code generates this TypeQL schema:

```typeql
define

# Attributes (defined once, can be owned by multiple types)
name sub attribute, value string;
email sub attribute, value string;
age sub attribute, value long;
salary sub attribute, value long;
position sub attribute, value string;

# Entities declare ownership with cardinality annotations
person sub entity,
    owns name @key @card(1,1),
    owns age @card(0,1),
    owns email;

company sub entity,
    owns name @key @card(1,1);

# Relations declare ownership with cardinality annotations
employment sub relation,
    relates employee,
    relates employer,
    owns position @card(1,1),
    owns salary @card(0,1);

# Role players
person plays employment:employee;
company plays employment:employer;
```

## Creating Instances

```python
# Create person with attribute values
alice = Person(
    name="Alice Johnson",
    age=30,
    email="alice@example.com"
)

# Generate insert query
print(alice.to_insert_query())
# Output: $e isa person, has name "Alice Johnson", has age 30, has email "alice@example.com"
```

## Benefits

### 1. **True TypeDB Semantics**
- Attributes are independent types
- Entities own attributes (not define them inline)
- Multiple types can own the same attribute

### 2. **Cleaner Schema**
- Attributes defined once at the top
- Clear ownership declarations
- No duplicate attribute definitions

### 3. **Better Type Reuse**
```python
class Name(String):
    pass

# Both Person and Company can own the same Name attribute
class Person(Entity):
    name: Name

class Company(Entity):
    name: Name
```

### 4. **Explicit Key Attributes with Cardinality**
```python
class Person(Entity):
    flags = EntityFlags(type_name="person")
    name: Name = Flag(Key, Card(1))  # Clearly marked as @key @card(1,1)
```

### 5. **No Pydantic Conflicts**
- Entities store values in a simple dict
- No complex Pydantic validation issues
- Cleaner, more predictable behavior

## Card Cardinality Semantics

TypeBridge provides flexible cardinality constraints that map to TypeDB's `@card` annotation:

```python
from type_bridge import Card

# Exact cardinality
Card(1)          # @card(1,1) - exactly one
Card(3)          # @card(3,3) - exactly three

# Range with both min and max
Card(1, 3)       # @card(1,3) - one to three
Card(0, 5)       # @card(0,5) - zero to five

# Unbounded (keyword argument)
Card(min=0)      # @card(0) - zero or more (unbounded)
Card(min=1)      # @card(1) - one or more (unbounded)

# Max only (min defaults to 1)
Card(max=5)      # @card(1,5) - one to five
Card(max=3)      # @card(1,3) - one to three
```

## Using Python Inheritance for Supertypes

TypeBridge automatically uses Python inheritance to determine TypeDB supertypes:

```python
from type_bridge import Entity, EntityFlags

class Animal(Entity):
    flags = EntityFlags(abstract=True)  # Abstract entity
    name: Name

class Dog(Animal):  # Automatically: dog sub animal
    breed: Breed

class Cat(Animal):  # Automatically: cat sub animal
    color: Color
```

Generated schema:
```typeql
animal sub entity, abstract,
    owns name;

dog sub animal,
    owns breed;

cat sub animal,
    owns color;
```

## File Organization

```
type_bridge/
├── attribute.py       # Attribute base class, concrete types, and flags (Card, Key, Unique, EntityFlags, RelationFlags)
├── models.py          # Entity/Relation classes using attribute ownership model
├── crud.py            # EntityManager and RelationManager for CRUD operations
├── schema.py          # SchemaManager and MigrationManager
├── session.py         # Database connection and transaction management
└── query.py           # TypeQL query builder
```

## Running the Example

```bash
uv run python examples/basic_usage.py
```

This will demonstrate:
- Attribute schema generation
- Entity/Relation schema with ownership declarations and cardinality
- Instance creation and insert query generation
- Attribute introspection
- Full TypeDB schema generation

## Literal Types for Type Safety

TypeBridge supports Python's `Literal` types to provide type-checker hints for enum-like values while maintaining runtime flexibility:

```python
from typing import Literal
from type_bridge import Entity, EntityFlags, String, Long

class Status(String):
    pass

class Priority(Long):
    pass

class Task(Entity):
    flags = EntityFlags(type_name="task")
    # Type checkers see Literal and provide autocomplete/warnings
    status: Literal["pending", "active", "completed"] | Status
    priority: Literal[1, 2, 3, 4, 5] | Priority

# Valid literal values work
task1 = Task(status="pending", priority=1)  # IDE autocompletes status values

# Runtime accepts any valid type (type checker would flag these)
task2 = Task(status="custom_status", priority=999)  # Works at runtime
```

**Key Points:**
- **Type-checker safety**: IDEs and type checkers provide autocomplete and warnings for literal values
- **Runtime flexibility**: Pydantic accepts any value matching the Attribute type (any string for String, any int for Long)
- **Best of both worlds**: Get IDE benefits without restricting runtime behavior

This pattern is particularly useful for:
- Enum-like values that may evolve over time
- Status fields with common values but flexibility for custom states
- Priority levels with recommended ranges
- Type-safe API parameters with graceful handling of unexpected values

## Pydantic Integration

TypeBridge v0.1.2+ is built on **Pydantic v2**, providing powerful validation and serialization features:

### Features

1. **Automatic Type Validation**
   - Values are automatically validated and coerced to the correct type
   - Invalid data raises clear validation errors

2. **JSON Serialization/Deserialization**
   - Convert entities to/from JSON with `.model_dump_json()` and `.model_validate_json()`
   - Convert to/from dicts with `.model_dump()` and `Model(**dict)`

3. **Model Copying**
   - Create modified copies with `.model_copy(update={...})`
   - Deep copying supported

4. **Validation on Assignment**
   - Field assignments are automatically validated
   - Type coercion happens on both initialization and assignment

### Example

```python
from type_bridge import Entity, EntityFlags, String, Long

class Name(String):
    pass

class Age(Long):
    pass

class Person(Entity):
    flags = EntityFlags(type_name="person")
    name: Name
    age: Age = 0  # Default value

# Automatic validation and coercion
alice = Person(name="Alice", age="30")  # "30" coerced to int 30
assert isinstance(alice.age, int)

# JSON serialization
json_data = alice.model_dump_json()
# {"name":"Alice","age":30}

# JSON deserialization
bob = Person.model_validate_json('{"name":"Bob","age":25}')

# Model copying
alice_older = alice.model_copy(update={"age": 31})
```

### Configuration

Entity and Relation classes are configured with:
- `arbitrary_types_allowed=True`: Allow Attribute subclass types
- `validate_assignment=True`: Validate field assignments
- `extra='allow'`: Allow extra fields for flexibility
- `ignored_types`: Ignore TypeBridge-specific types (EntityFlags, RelationFlags, Role)

## Implementation Status

1. ✅ Implement core Attribute system
2. ✅ Implement Entity/Relation ownership model with EntityFlags/RelationFlags
3. ✅ Implement Card cardinality constraints
4. ✅ Implement Flag annotation system (Key, Unique, Card)
5. ✅ Support Python inheritance for supertypes
6. ✅ Integrate Pydantic v2 for validation and serialization
7. ✅ Add Literal type support for type-safe enum-like values
8. ✅ Create comprehensive examples
9. ✅ Write comprehensive tests
10. ✅ Update documentation and README

## Conclusion

The new Attribute-based API with Pydantic integration provides a more accurate representation of TypeDB's type system, making it clearer how attributes, entities, and relations work together. The Pydantic integration adds powerful validation, serialization, and type safety features while maintaining full compatibility with TypeDB operations. This design is more maintainable and aligns better with TypeDB's philosophy of treating attributes as first-class types.

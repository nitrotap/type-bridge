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
from typing import Optional
from type_bridge import String, Integer, Entity, EntityFlags, Flag, Key, Card

class Name(String):
    """Name attribute - can be owned by multiple entity types."""
    pass

class Age(Integer):
    """Age attribute."""
    pass

class Tag(String):
    """Tag attribute for multi-value fields."""
    pass

# Step 2: Entities OWN attributes via type annotations
class Person(Entity):
    flags = EntityFlags(type_name="person")  # Optional, defaults to class name

    # Use Flag() for key/unique markers and cardinality
    name: Name = Flag(Key)                  # @key (implies @card(1..1))
    age: Optional[Age]                      # @card(0..1) - optional single value
    phone: Phone | None                     # @card(0..1) - union syntax also works
    email: Email                            # @card(1..1) - default, required
    tags: list[Tag] = Flag(Card(min=2))     # @card(2..) - multi-value with Card
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
        """Generates TypeQL schema: 'attribute name, value string;'"""
```

### 2. Concrete Attribute Types

```python
class String(Attribute):
    value_type = "string"

class Integer(Attribute):
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
- `Integer` subclass fields become `int | FieldType`
- `Double` subclass fields become `float | FieldType`
- `Boolean` subclass fields become `bool | FieldType`
- `DateTime` subclass fields become `datetime | FieldType`

### Type Checker Compatibility

TypeBridge supports **two ways** to create entity instances:

**Option 1: Attribute Instances (fully type-safe, zero pyright errors)**

```python
# Pass attribute instances - zero pyright errors!
alice = Person(
    name=Name("Alice"),
    age=Age(30),
    email=Email("alice@example.com")
)
```

**Pros**:
- ✅ Zero pyright/mypy errors
- ✅ Fully type-safe
- ✅ Explicit about attribute types
- ✅ IDE autocomplete works perfectly

**Cons**:
- Slightly more verbose
- Requires wrapping each value

**Option 2: Raw Values (convenient)**

```python
# Pass raw values - convenient but may show pyright warnings
alice = Person(name="Alice", age=30, email="alice@example.com")
```

**Pros**:
- ✅ Concise and convenient
- ✅ Matches common Python patterns
- ✅ Works perfectly at runtime

**Cons**:
- ⚠️ May show pyright warnings (false positives)

**Both patterns work identically at runtime** thanks to Pydantic's validation. The attribute instances are automatically unwrapped to their primitive values for storage and queries.

**Recommendation**: Use attribute instances when working with strict type checking, use raw values for convenience when type checker warnings are acceptable.

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
from typing import ClassVar, Optional
from type_bridge import (
    String, Integer,
    Entity, EntityFlags,
    Relation, RelationFlags, Role,
    Flag, Key, Card
)

# Define attribute types
class Name(String):
    pass

class Email(String):
    pass

class Age(Integer):
    pass

class Salary(Integer):
    pass

class Position(String):
    pass

class Skill(String):
    pass

# Define entities with attribute ownership and flags
class Person(Entity):
    flags = EntityFlags(type_name="person")

    name: Name = Flag(Key)                  # @key (implies @card(1..1))
    age: Optional[Age]                      # @card(0..1)
    email: Email                            # @card(1..1) - default
    skills: list[Skill] = Flag(Card(min=1)) # @card(1..) - multi-value

class Company(Entity):
    flags = EntityFlags(type_name="company")

    name: Name = Flag(Key)   # @key (implies @card(1..1))

# Define relations with attribute ownership
class Employment(Relation):
    flags = RelationFlags(type_name="employment")

    employee: ClassVar[Role] = Role("employee", Person)
    employer: ClassVar[Role] = Role("employer", Company)

    position: Position        # @card(1..1) - default
    salary: Optional[Salary]  # @card(0..1)
```

## Generated Schema

The above code generates this TypeQL schema:

```typeql
define

# Attributes (defined once, can be owned by multiple types)
attribute name, value string;
attribute email, value string;
attribute age, value long;
attribute salary, value long;
attribute position, value string;
attribute skill, value string;

# Entities declare ownership with cardinality annotations
entity person,
    owns name @key,
    owns age @card(0..1),
    owns email @card(1..1),
    owns skill @card(1..);  # Multi-value: at least 1

entity company,
    owns name @key;

# Relations declare ownership with cardinality annotations
relation employment,
    relates employee,
    relates employer,
    owns position @card(1..1),
    owns salary @card(0..1);

# Role players
person plays employment:employee;
company plays employment:employer;
```

## Cardinality with Card API

The `Card` class provides explicit cardinality specification for multi-value fields:

```python
from type_bridge import Card, Flag

class Tag(String):
    pass

class Person(Entity):
    flags = EntityFlags(type_name="person")

    # Single value patterns
    name: Name                              # @card(1..1) - required, exactly one
    age: Optional[Age]                      # @card(0..1) - optional, at most one
    phone: Phone | None                     # @card(0..1) - union syntax also works

    # Multi-value patterns (MUST use Flag(Card(...)))
    tags: list[Tag] = Flag(Card(min=1))     # @card(1..) - at least one, unbounded
    jobs: list[Job] = Flag(Card(1, 5))      # @card(1..5) - one to five (positional args)
    skills: list[Skill] = Flag(Card(min=2, max=10))  # @card(2..10) - two to ten (keyword args)

    # Combine with Key
    ids: list[ID] = Flag(Key, Card(min=1))  # @key @card(1..) - key with multi-value
```

### Card API Rules

1. **`Flag(Card(...))` ONLY with `list[Type]`**:
   ```python
   # ✅ Correct
   tags: list[Tag] = Flag(Card(min=2))

   # ❌ Wrong - use Optional instead
   age: Age = Flag(Card(min=0, max=1))  # TypeError!
   ```

2. **`list[Type]` MUST have `Flag(Card(...))`**:
   ```python
   # ✅ Correct
   tags: list[Tag] = Flag(Card(min=1))

   # ❌ Wrong - missing Card
   tags: list[Tag]  # TypeError!
   tags: list[Tag] = Flag(Key)  # TypeError - Key alone is not enough!
   ```

3. **For optional single values, use `Optional[Type]` or `Type | None`**:
   ```python
   # ✅ Both work
   age: Optional[Age]
   phone: Phone | None
   ```

## Creating Instances

```python
# Two ways to create instances:

# Option 1: Attribute instances (type-safe, zero pyright errors)
alice = Person(
    name=Name("Alice Johnson"),
    age=Age(30),
    email=Email("alice@example.com"),
    skills=["Python", "TypeDB", "FastAPI"]  # Multi-value field
)

# Option 2: Raw values (convenient, may show pyright warnings)
bob = Person(
    name="Bob Smith",
    age=25,
    email="bob@example.com",
    skills=["JavaScript", "React"]
)

# Both produce the same insert queries
print(alice.to_insert_query())
# Output: $e isa person, has name "Alice Johnson", has age 30, has email "alice@example.com"

print(bob.to_insert_query())
# Output: $e isa person, has name "Bob Smith", has age 25, has email "bob@example.com"
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

### 4. **Explicit Key Attributes**
```python
class Person(Entity):
    flags = EntityFlags(type_name="person")
    name: Name = Flag(Key)  # Clearly marked as @key
```

### 5. **No Pydantic Conflicts**
- Entities store values in a simple dict
- No complex Pydantic validation issues
- Cleaner, more predictable behavior

## Cardinality Semantics

TypeBridge provides cardinality constraints using Python's typing system that map to TypeDB's `@card` annotation:

```python
from typing import Optional
from type_bridge import Min, Max, Range

# Default cardinality
field: Type                  # @card(1..1) - exactly one (default)

# Optional (zero or one)
field: Optional[Type]        # @card(0..1) - zero or one
field: Type | None           # @card(0..1) - equivalent syntax

# Minimum cardinality (unbounded)
field: Min[2, Type]          # @card(2..) - two or more
field: Min[1, Type]          # @card(1..) - one or more

# Maximum cardinality
field: Max[5, Type]          # @card(0..5) - zero to five
field: Max[3, Type]          # @card(0..3) - zero to three

# Range (min and max)
field: Range[1, 3, Type]     # @card(1..3) - one to three
field: Range[2, 5, Type]     # @card(2..5) - two to five
```

**Note**: For multi-cardinality fields (Max, Min, Range), you must pass a list at runtime:
```python
class Company(Entity):
    flags = EntityFlags(type_name="company")
    industries: Range[1, 5, Industry]

# Must pass a list
company = Company(industries=["Tech", "Software", "AI"])
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
entity animal, abstract,
    owns name;

entity dog sub animal,
    owns breed;

entity cat sub animal,
    owns color;
```

## File Organization

```
type_bridge/
├── attribute.py       # Attribute base class, concrete types, and flags (Key, Unique, Min, Max, Range, EntityFlags, RelationFlags)
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
from type_bridge import Entity, EntityFlags, String, Integer

class Status(String):
    pass

class Priority(Integer):
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
- **Runtime flexibility**: Pydantic accepts any value matching the Attribute type (any string for String, any int for Integer)
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
from type_bridge import Entity, EntityFlags, String, Integer

class Name(String):
    pass

class Age(Integer):
    pass

class Person(Entity):
    flags = EntityFlags(type_name="person")
    name: Name
    age: Age = Age(0)  # Default value

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

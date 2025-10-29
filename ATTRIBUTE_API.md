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
from type_bridge.attribute import String, Long, Key

class Name(String):
    """Name attribute - can be owned by multiple entity types."""
    pass

class Age(Long):
    """Age attribute."""
    pass

# Step 2: Mark attributes as keys if needed
NameKey = Key(Name)

# Step 3: Entities OWN attributes via type annotations
class Person(Entity):
    __type_name__ = "person"

    name: NameKey  # Person owns 'name' as a @key
    age: Age       # Person owns 'age'
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

### 3. Entity Ownership Model (`models_v2.py`)

```python
class Entity:
    """Base class for entities."""
    __type_name__: ClassVar[str | None] = None
    __owned_attrs__: ClassVar[dict[str, type[Attribute]]] = {}

    def __init_subclass__(cls):
        """Automatically collects owned attributes from type annotations."""

    @classmethod
    def get_owned_attributes(cls) -> dict[str, type[Attribute]]:
        """Returns mapping of field names to Attribute classes."""

    @classmethod
    def to_schema_definition(cls) -> str:
        """Generates entity schema with ownership declarations."""
```

## Complete Example

```python
from typing import ClassVar
from type_bridge.attribute import String, Long, Key
from type_bridge.models_v2 import Entity, Relation, Role

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

# Create key attributes
NameKey = Key(Name)
EmailKey = Key(Email)

# Define entities with attribute ownership
class Person(Entity):
    __type_name__ = "person"

    name: NameKey   # Person owns 'name' as @key
    age: Age        # Person owns 'age'
    email: Email    # Person owns 'email'

class Company(Entity):
    __type_name__ = "company"

    name: NameKey   # Company also owns 'name' as @key

# Define relations with attribute ownership
class Employment(Relation):
    __type_name__ = "employment"

    employee: ClassVar[Role] = Role("employee", Person)
    employer: ClassVar[Role] = Role("employer", Company)

    position: Position  # Employment owns 'position'
    salary: Salary      # Employment owns 'salary'
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

# Entities declare ownership
person sub entity,
    owns name @key,
    owns age,
    owns email;

company sub entity,
    owns name @key;

# Relations declare ownership
employment sub relation,
    relates employee,
    relates employer,
    owns position,
    owns salary;

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

### 4. **Explicit Key Attributes**
```python
NameKey = Key(Name)

class Person(Entity):
    name: NameKey  # Clearly marked as @key
```

### 5. **No Pydantic Conflicts**
- Entities store values in a simple dict
- No complex Pydantic validation issues
- Cleaner, more predictable behavior

## Migration from Old API

### Old API (Pydantic fields)
```python
from type_bridge import Entity, String, Long

class Person(Entity):
    flags = Flags(type_name="person")
    name: str = String(typedb_key=True)  # Field descriptor
    age: int = Long()
```

### New API (Attribute ownership)
```python
from type_bridge.attribute import String, Long, Key
from type_bridge.models_v2 import Entity

class Name(String):
    pass

class Age(Long):
    pass

NameKey = Key(Name)

class Person(Entity):
    __type_name__ = "person"
    name: NameKey  # Type annotation declares ownership
    age: Age
```

## File Organization

```
type_bridge/
├── attribute.py       # NEW: Attribute base class and concrete types
├── models_v2.py       # NEW: Simplified Entity/Relation using attribute ownership
├── models.py          # OLD: Pydantic-based models (deprecated)
└── fields.py          # OLD: Field descriptors (deprecated)
```

## Running the Example

```bash
uv run python examples/new_attribute_api_example.py
```

This will demonstrate:
- Attribute schema generation
- Entity schema with ownership declarations
- Instance creation and insert query generation
- Attribute introspection

## Next Steps

1. ✅ Implement core Attribute system
2. ✅ Implement Entity/Relation ownership model
3. ✅ Create comprehensive example
4. ⏳ Update SchemaManager to work with new API
5. ⏳ Update CRUD managers for new API
6. ⏳ Write tests for new API
7. ⏳ Update documentation and README

## Conclusion

The new Attribute-based API provides a more accurate representation of TypeDB's type system, making it clearer how attributes, entities, and relations work together. This design is more maintainable and aligns better with TypeDB's philosophy of treating attributes as first-class types.

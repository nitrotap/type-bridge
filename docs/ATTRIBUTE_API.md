# Attribute-Based API

## Overview

TypeBridge provides an Attribute-based API that aligns with TypeDB's type system, where **attributes are base types** that **entities and relations own**.

## Design Principles

### TypeDB's Model
In TypeDB:
1. **Attributes** are independent value types (e.g., `name`, `email`, `age`)
2. **Entities** and **relations** declare **ownership** of these attributes
3. Multiple types can own the same attribute

### TypeBridge API
```python
# Step 1: Define attribute types (base types)
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
    age: Age | None = None                  # @card(0..1) - explicit default - optional single value
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

TypeBridge provides all TypeDB value types:

```python
class String(Attribute):
    value_type = "string"

class Integer(Attribute):
    value_type = "integer"

class Double(Attribute):
    value_type = "double"

class Decimal(Attribute):
    value_type = "decimal"  # High-precision fixed-point (19 decimal digits)

class Boolean(Attribute):
    value_type = "boolean"

class Date(Attribute):
    value_type = "date"  # Date only (no time)

class DateTime(Attribute):
    value_type = "datetime"  # Naive datetime (no timezone)

class DateTimeTZ(Attribute):
    value_type = "datetime-tz"  # Timezone-aware datetime

class Duration(Attribute):
    value_type = "duration"  # ISO 8601 duration (calendar-aware)
```

**Detailed Type Documentation:**

See CLAUDE.md for comprehensive documentation on:
- **Decimal vs Double**: When to use fixed-point vs floating-point
- **Date, DateTime, DateTimeTZ**: Temporal type differences and conversions
- **Duration**: ISO 8601 format, calendar-aware arithmetic

**Tip**: Combine with `Literal` for type-safe enum-like values:
```python
from typing import Literal

class Status(String):
    pass

# Type checker provides autocomplete for "active", "inactive", "pending"
status: Literal["active", "inactive", "pending"] | Status
```

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
    age: Age | None = None                  # @card(0..1) - explicit default
    email: Email                            # @card(1..1) - default
    skills: list[Skill] = Flag(Card(min=1)) # @card(1..) - multi-value

class Company(Entity):
    flags = EntityFlags(type_name="company")

    name: Name = Flag(Key)   # @key (implies @card(1..1))

# Define relations with attribute ownership
class Employment(Relation):
    flags = RelationFlags(type_name="employment")

    employee: Role[Person] = Role("employee", Person)
    employer: Role[Company] = Role("employer", Company)

    position: Position        # @card(1..1) - default
    salary: Salary | None = None          # @card(0..1) - explicit default
```

## Generated Schema

The above code generates this TypeQL schema:

```typeql
define

# Attributes (defined once, can be owned by multiple types)
attribute name, value string;
attribute email, value string;
attribute age, value integer;
attribute salary, value integer;
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
    age: Age | None = None                  # @card(0..1) - explicit default - optional, at most one

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

   # ❌ Wrong - use Type | None instead
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

3. **For optional single values, use `Type | None`**:
   ```python
   # ✅ Correct
   age: Age | None
   ```

## Creating Instances

```python
# Create entity instances with attribute values
alice = Person(
    name=Name("Alice Johnson"),
    age=Age(30),
    email=Email("alice@example.com"),
    skills=[Skill("Python"), Skill("TypeDB"), Skill("FastAPI")]
)

# Generate insert query
print(alice.to_insert_query())
# Output: $e isa person, has name "Alice Johnson", has age 30, has email "alice@example.com", ...
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

### 5. **Pydantic Integration**
- Built on Pydantic v2 for automatic validation
- JSON serialization and deserialization support
- Type coercion and field validation

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
├── attribute/         # Modular attribute package (refactored from attribute.py)
│   ├── base.py        # Attribute abstract base class
│   ├── string.py      # String attribute with concatenation operations
│   ├── integer.py     # Integer attribute with arithmetic operations
│   ├── double.py      # Double attribute
│   ├── boolean.py     # Boolean attribute
│   ├── datetime.py    # DateTime attribute
│   └── flags.py       # Flag system (Key, Unique, Card, EntityFlags, RelationFlags)
├── schema/            # Modular schema package (refactored from schema.py)
│   ├── manager.py     # SchemaManager for schema operations
│   ├── info.py        # SchemaInfo container
│   ├── diff.py        # SchemaDiff, EntityChanges, RelationChanges for comparison
│   ├── migration.py   # MigrationManager for migrations
│   └── exceptions.py  # SchemaConflictError for conflict detection
├── models.py          # Entity/Relation classes using attribute ownership model
├── crud.py            # EntityManager and RelationManager for CRUD operations with fetching API
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

TypeBridge is built on **Pydantic v2**, providing powerful validation and serialization features:

### Features

1. **Automatic Type Validation**
   - Values are automatically validated to the correct type
   - Invalid data raises clear validation errors

2. **JSON Serialization/Deserialization**
   - Convert entities to/from JSON with `.model_dump_json()` and `.model_validate_json()`
   - Convert to/from dicts with `.model_dump()` and `Model(**dict)`

3. **Model Copying**
   - Create modified copies with `.model_copy(update={...})`
   - Deep copying supported

4. **Validation on Assignment**
   - Field assignments are automatically validated

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
    age: Age

# Create instance
alice = Person(name=Name("Alice"), age=Age(30))

# JSON serialization
json_data = alice.model_dump_json()

# JSON deserialization
bob = Person.model_validate_json('{"name":"Bob","age":25}')

# Model copying
alice_older = alice.model_copy(update={"age": Age(31)})
```

### Configuration

Entity and Relation classes are configured with:
- `arbitrary_types_allowed=True`: Allow Attribute subclass types
- `validate_assignment=True`: Validate field assignments
- `extra='allow'`: Allow extra fields for flexibility
- `ignored_types`: Ignore TypeBridge-specific types (EntityFlags, RelationFlags, Role)

## CRUD Operations with Fetching API

TypeBridge provides type-safe CRUD managers with a modern fetching API for querying entities and relations.

### EntityManager Operations

Each Entity class can create a type-safe manager that preserves type information:

```python
from type_bridge import Database, Entity, EntityFlags, String, Integer, Flag, Key

class Name(String):
    pass

class Age(Integer):
    pass

class Person(Entity):
    flags = EntityFlags(type_name="person")
    name: Name = Flag(Key)
    age: Age | None

# Connect to database
db = Database(address="localhost:1729", database="mydb")
db.connect()

# Create manager
person_manager = Person.manager(db)
```

### Insert Operations

**Single insert**:
```python
alice = Person(name=Name("Alice"), age=Age(30))
person_manager.insert(alice)
```

**Bulk insert** (more efficient for multiple entities):
```python
persons = [
    Person(name=Name("Alice"), age=Age(30)),
    Person(name=Name("Bob"), age=Age(25)),
    Person(name=Name("Charlie"), age=Age(35)),
]
person_manager.insert_many(persons)
```

### Fetching Operations

**Get all entities**:
```python
all_persons = person_manager.all()
```

**Get with attribute filters**:
```python
young_persons = person_manager.get(age=25)
alice = person_manager.get(name="Alice")
```

**Chainable queries with EntityQuery**:
```python
# Create a query
query = person_manager.filter(age=30)

# Chain operations
results = query.limit(10).offset(5).execute()

# Get first result or None
first_person = person_manager.filter(name="Alice").first()

# Count matching entities
count = person_manager.filter(age=30).count()
```

### Delete Operations

```python
# Delete entities matching filters
deleted_count = person_manager.delete(name="Alice")
```

### Update Operations

The update API follows the typical ORM pattern: fetch, modify, update.

```python
# Step 1: Fetch entity
alice = person_manager.get(name="Alice")[0]

# Step 2: Modify attributes directly on the entity instance
alice.age = Age(31)
alice.status = Status("active")
alice.tags = [Tag("python"), Tag("typedb"), Tag("ai")]

# Step 3: Persist changes to database
person_manager.update(alice)
```

**Complete workflow examples**:

```python
# Update single-value attribute
alice = person_manager.get(name="Alice")[0]
alice.age = Age(31)
person_manager.update(alice)

# Update multi-value attribute
alice = person_manager.get(name="Alice")[0]
alice.tags = [Tag("python"), Tag("typedb"), Tag("machine-learning")]
person_manager.update(alice)

# Update multiple attributes at once
bob = person_manager.get(name="Bob")[0]
bob.age = Age(26)
bob.status = Status("active")
bob.tags = [Tag("java"), Tag("python")]
person_manager.update(bob)

# Clear multi-value attribute by setting to empty list
alice = person_manager.get(name="Alice")[0]
alice.tags = []
person_manager.update(alice)
```

**TypeQL update semantics**:
- **Single-value attributes** (`@card(0..1)` or `@card(1..1)`): Uses TypeQL `update` clause for efficient in-place updates
- **Multi-value attributes** (e.g., `@card(0..5)`, `@card(2..)`): Deletes all old values first, then inserts new ones

The update method reads the entity's current state and generates the appropriate TypeQL:

```typeql
match
$e isa person, has name "Alice";
delete
has $tags of $e;
insert
$e has tags "python";
$e has tags "typedb";
update
$e has age 31;
```

The update method automatically determines whether each attribute is single or multi-value based on its cardinality annotations, ensuring correct TypeQL generation.

### RelationManager Operations

Relations support similar operations with additional role player filtering:

```python
from type_bridge import Relation, RelationFlags, Role

class Position(String):
    pass

class Employment(Relation):
    flags = RelationFlags(type_name="employment")
    employee: Role[Person] = Role("employee", Person)
    employer: Role[Company] = Role("employer", Company)
    position: Position

# Create manager
employment_manager = Employment.manager(db)

# Insert relation - use typed instances
employment = Employment(
    employee=alice,
    employer=techcorp,
    position=Position("Engineer")
)
employment_manager.insert(employment)

# Bulk insert relations
employments = [
    Employment(employee=alice, employer=techcorp, position=Position("Engineer")),
    Employment(employee=bob, employer=startup, position=Position("Designer")),
]
employment_manager.insert_many(employments)

# Get relations by attribute filter
engineers = employment_manager.get(position="Engineer")

# Get relations by role player filter
alice_jobs = employment_manager.get(employee=alice)
techcorp_employees = employment_manager.get(employer=techcorp)
```

### Type Safety

EntityManager and RelationManager use Python's generic type syntax to preserve type information:

```python
class EntityManager[E: Entity]:
    def insert(self, entity: E) -> E:
        ...
    def insert_many(self, entities: list[E]) -> list[E]:
        ...
    def get(self, **filters) -> list[E]:
        ...
    def filter(self, **filters) -> EntityQuery[E]:
        ...
    def all(self) -> list[E]:
        ...

# Type checkers understand the returned types
alice = Person(name=Name("Alice"), age=Age(30))
person_manager.insert(alice)  # ✓ Type-safe
persons: list[Person] = person_manager.all()  # ✓ Type-safe
```

## Schema Management with Conflict Detection

TypeBridge provides comprehensive schema management with automatic conflict detection to prevent accidental data loss.

### Basic Schema Operations

```python
from type_bridge import SchemaManager, Database

db = Database(address="localhost:1729", database="mydb")
db.connect()

# Create schema manager
schema_manager = SchemaManager(db)

# Register models
schema_manager.register(Person, Company, Employment)

# Generate TypeQL schema
typeql_schema = schema_manager.generate_schema()
print(typeql_schema)

# Sync schema to database
schema_manager.sync_schema()
```

### Automatic Conflict Detection

SchemaManager automatically detects breaking changes and prevents data loss:

```python
from type_bridge.schema import SchemaConflictError

# Initial schema creation
schema_manager.sync_schema()  # ✓ Success

# Modify your models (e.g., remove an attribute)
class Person(Entity):
    flags = EntityFlags(type_name="person")
    name: Name = Flag(Key)
    # age attribute removed - BREAKING CHANGE!

# Attempt to sync
try:
    schema_manager.sync_schema()  # ✗ Raises SchemaConflictError
except SchemaConflictError as e:
    print(e.diff.summary())
    # Output:
    # Schema Differences:
    # Modified Entities:
    #   person:
    #     - Removed attributes: age

# Force recreate (⚠️ DATA LOSS - drops and recreates database)
schema_manager.sync_schema(force=True)
```

### Schema Comparison and Diff

Compare schemas to understand changes before applying them:

```python
from type_bridge.schema import SchemaInfo

# Collect current schema
old_schema = schema_manager.collect_schema_info()

# Modify your models
class Person(Entity):
    flags = EntityFlags(type_name="person")
    name: Name = Flag(Key)
    age: Age | None
    email: Email = Flag(Unique)  # New attribute!

# Collect new schema
new_schema = schema_manager.collect_schema_info()

# Compare and view differences
diff = old_schema.compare(new_schema)

if diff.has_changes():
    print(diff.summary())
    # Output:
    # Schema Differences:
    # Modified Entities:
    #   person:
    #     + Added attributes: email (unique)
```

### Schema Diff Details

The SchemaDiff class provides granular change tracking:

```python
# Check for specific changes
print(f"Added entities: {diff.added_entities}")
print(f"Removed entities: {diff.removed_entities}")
print(f"Added relations: {diff.added_relations}")
print(f"Removed relations: {diff.removed_relations}")
print(f"Added attributes: {diff.added_attributes}")
print(f"Removed attributes: {diff.removed_attributes}")

# Check entity modifications
for entity_type, changes in diff.modified_entities.items():
    print(f"\n{entity_type} changes:")
    print(f"  Added attributes: {changes.added_attributes}")
    print(f"  Removed attributes: {changes.removed_attributes}")

    # Check attribute flag changes (cardinality, key, unique)
    for attr_name, flag_change in changes.modified_attributes.items():
        print(f"  Modified {attr_name}:")
        print(f"    Old: {flag_change.old_flags}")
        print(f"    New: {flag_change.new_flags}")

# Check relation modifications
for relation_type, changes in diff.modified_relations.items():
    print(f"\n{relation_type} changes:")
    print(f"  Added roles: {changes.added_roles}")
    print(f"  Removed roles: {changes.removed_roles}")
    print(f"  Added attributes: {changes.added_attributes}")
    print(f"  Removed attributes: {changes.removed_attributes}")
```

### Migration Manager

For complex schema migrations, use MigrationManager:

```python
from type_bridge.schema import MigrationManager

migration_manager = MigrationManager(db)

# Add migrations
migration_manager.add_migration(
    name="add_email_to_person",
    schema="define person owns email;"
)

migration_manager.add_migration(
    name="add_company_entity",
    schema="""
    define
    entity company,
        owns name @key;
    """
)

# Apply all migrations in order
migration_manager.apply_migrations()
```

## Implementation Status

### Core Features
1. ✅ Core Attribute system with all TypeDB value types
2. ✅ Entity/Relation ownership model with EntityFlags/RelationFlags
3. ✅ Card cardinality constraints with flexible API
4. ✅ Flag annotation system (Key, Unique, Card)
5. ✅ Python inheritance for TypeDB supertypes
6. ✅ Pydantic v2 integration for validation and serialization

### Attribute Types (Complete)
7. ✅ Basic types: String, Integer, Double, Boolean
8. ✅ Temporal types: Date, DateTime, DateTimeTZ with conversions
9. ✅ Numeric precision: Decimal for fixed-point arithmetic
10. ✅ Duration type with ISO 8601 format support

### Advanced Features
11. ✅ Literal type support for type-safe enum-like values
12. ✅ Fetching API (get, filter, all, first, count) with EntityQuery
13. ✅ Update API for single and multi-value attributes
14. ✅ Bulk operations (insert_many for entities and relations)
15. ✅ Schema conflict detection with SchemaDiff
16. ✅ Keyword validation for reserved TypeDB/TypeQL words
17. ✅ Type name case formatting options (snake_case, kebab-case, etc.)

### Testing & Documentation
18. ✅ 267+ comprehensive tests (240 unit, 27 integration)
19. ✅ Organized examples (basic vs advanced)
20. ✅ Complete documentation and README

## Conclusion

The Attribute-based API with Pydantic integration provides an accurate representation of TypeDB's type system, making it clear how attributes, entities, and relations work together. The Pydantic integration adds powerful validation, serialization, and type safety features while maintaining full compatibility with TypeDB operations. This design aligns with TypeDB's philosophy of treating attributes as first-class types.

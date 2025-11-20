# CRUD Operations

Complete reference for Create, Read, Update, Delete operations in TypeBridge.

## Overview

TypeBridge provides type-safe CRUD managers for entities and relations with a modern fetching API. All operations preserve type information and generate optimized TypeQL queries.

## EntityManager

Type-safe manager for entity CRUD operations.

### Creating a Manager

```python
from type_bridge import Database, Entity, TypeFlags

class Person(Entity):
    flags = TypeFlags(type_name="person")
    name: Name = Flag(Key)
    age: Age | None = None

# Connect to database
db = Database(address="localhost:1729", database="mydb")
db.connect()

# Create manager
person_manager = Person.manager(db)
```

### EntityManager Methods

```python
class EntityManager[E: Entity]:
    def insert(self, entity: E) -> E:
        """Insert a single entity."""

    def insert_many(self, entities: list[E]) -> list[E]:
        """Insert multiple entities (bulk operation)."""

    def get(self, **filters) -> list[E]:
        """Get entities matching attribute filters."""

    def filter(self, **filters) -> EntityQuery[E]:
        """Create chainable query with filters."""

    def all(self) -> list[E]:
        """Get all entities of this type."""

    def delete(self, **filters) -> int:
        """Delete entities matching filters. Returns count."""

    def update(self, entity: E) -> E:
        """Update entity in database."""
```

## Insert Operations

### Single Insert

Insert one entity at a time:

```python
# Create entity instance
alice = Person(
    name=Name("Alice Johnson"),
    age=Age(30),
    email=Email("alice@example.com")
)

# Insert into database
person_manager.insert(alice)
```

### Bulk Insert

Insert multiple entities efficiently in a single transaction:

```python
# Create multiple entities
persons = [
    Person(name=Name("Alice"), age=Age(30)),
    Person(name=Name("Bob"), age=Age(25)),
    Person(name=Name("Charlie"), age=Age(35)),
    Person(name=Name("Diana"), age=Age(28)),
]

# Bulk insert (more efficient than multiple insert() calls)
person_manager.insert_many(persons)
```

**Performance tip**: Use `insert_many()` for multiple entities - it's significantly faster than calling `insert()` multiple times.

## Read Operations

### Get All Entities

```python
# Fetch all persons
all_persons = person_manager.all()

for person in all_persons:
    print(f"{person.name}: {person.age}")
```

### Get with Filters

Filter by attribute values:

```python
# Get persons with specific age
young_persons = person_manager.get(age=25)

# Get person by name (key attribute)
alice = person_manager.get(name="Alice")

# Multiple filters (AND logic)
results = person_manager.get(age=30, status="active")
```

### Chainable Queries

Create complex queries with method chaining:

```python
# Basic query
query = person_manager.filter(age=30)
results = query.execute()

# Chained query with pagination
results = person_manager.filter(age=30).limit(10).offset(5).execute()

# Get first matching entity (returns Person | None)
first_person = person_manager.filter(name="Alice").first()

if first_person:
    print(f"Found: {first_person.name}")
else:
    print("Not found")

# Count matching entities
count = person_manager.filter(age=30).count()
print(f"Found {count} persons aged 30")
```

### EntityQuery Methods

```python
class EntityQuery[E: Entity]:
    def filter(self, **filters) -> EntityQuery[E]:
        """Add additional filters."""

    def limit(self, n: int) -> EntityQuery[E]:
        """Limit number of results."""

    def offset(self, n: int) -> EntityQuery[E]:
        """Skip first n results."""

    def execute(self) -> list[E]:
        """Execute query and return results."""

    def first(self) -> E | None:
        """Get first result or None."""

    def count(self) -> int:
        """Count matching entities."""
```

## Update Operations

The update API follows the typical ORM pattern: **fetch → modify → update**.

### Basic Update

```python
# Step 1: Fetch entity
alice = person_manager.get(name="Alice")[0]

# Step 2: Modify attributes
alice.age = Age(31)
alice.status = Status("active")

# Step 3: Persist changes
person_manager.update(alice)
```

### Update Single-Value Attributes

```python
# Fetch entity
bob = person_manager.get(name="Bob")[0]

# Modify single-value attributes
bob.age = Age(26)
bob.email = Email("bob.new@example.com")
bob.is_active = IsActive(True)

# Persist changes
person_manager.update(bob)
```

### Update Multi-Value Attributes

```python
# Fetch entity
alice = person_manager.get(name="Alice")[0]

# Replace all values (deletes old, inserts new)
alice.tags = [Tag("python"), Tag("typedb"), Tag("machine-learning")]

# Persist changes
person_manager.update(alice)

# Clear multi-value attribute
alice.tags = []
person_manager.update(alice)
```

### Update Multiple Attributes

```python
# Fetch entity
charlie = person_manager.get(name="Charlie")[0]

# Modify multiple attributes at once
charlie.age = Age(36)
charlie.status = Status("active")
charlie.tags = [Tag("java"), Tag("python"), Tag("kubernetes")]
charlie.is_verified = IsVerified(True)

# Single update call persists all changes
person_manager.update(charlie)
```

### TypeQL Update Semantics

The update method generates different TypeQL based on cardinality:

**Single-value attributes** (`@card(0..1)` or `@card(1..1)`):
- Uses TypeQL `update` clause for efficient in-place updates

**Multi-value attributes** (e.g., `@card(1..)`, `@card(2..5)`):
- Deletes all old values
- Inserts new values

**Example TypeQL generated**:

```typeql
match
$e isa person, has name "Alice";
delete
has $tags of $e;
insert
$e has tags "python";
$e has tags "typedb";
$e has tags "machine-learning";
update
$e has age 31;
$e has status "active";
```

## Delete Operations

Delete entities matching filter criteria:

```python
# Delete by key attribute
deleted_count = person_manager.delete(name="Alice")
print(f"Deleted {deleted_count} entities")

# Delete by other attributes
deleted_count = person_manager.delete(age=25)

# Delete with multiple filters (AND logic)
deleted_count = person_manager.delete(age=30, status="inactive")
```

**Warning**: Delete operations are permanent and cannot be undone!

## RelationManager

Type-safe manager for relation CRUD operations.

### Creating a Manager

```python
from type_bridge import Relation, TypeFlags, Role

class Employment(Relation):
    flags = TypeFlags(type_name="employment")
    employee: Role[Person] = Role("employee", Person)
    employer: Role[Company] = Role("employer", Company)
    position: Position

# Create manager
employment_manager = Employment.manager(db)
```

### Insert Relations

```python
# Single insert
employment = Employment(
    employee=alice,
    employer=techcorp,
    position=Position("Senior Engineer")
)
employment_manager.insert(employment)

# Bulk insert
employments = [
    Employment(employee=alice, employer=techcorp, position=Position("Engineer")),
    Employment(employee=bob, employer=startup, position=Position("Designer")),
    Employment(employee=charlie, employer=techcorp, position=Position("Manager")),
]
employment_manager.insert_many(employments)
```

### Fetch Relations

```python
# Get all relations
all_employments = employment_manager.all()

# Filter by attribute
engineers = employment_manager.get(position="Engineer")

# Filter by role player
alice_jobs = employment_manager.get(employee=alice)
techcorp_employees = employment_manager.get(employer=techcorp)

# Multiple filters (AND logic)
results = employment_manager.get(
    employee=alice,
    position="Senior Engineer"
)
```

### Update Relations

```python
# Fetch relation
employment = employment_manager.get(employee=alice)[0]

# Modify attributes
employment.position = Position("Staff Engineer")
employment.salary = Salary(150000)

# Persist changes
employment_manager.update(employment)
```

### Delete Relations

```python
# Delete by attribute
deleted_count = employment_manager.delete(position="Engineer")

# Delete by role player
deleted_count = employment_manager.delete(employee=alice)

# Delete with multiple filters
deleted_count = employment_manager.delete(
    employee=alice,
    employer=techcorp
)
```

## Type Safety

Managers use Python's generic type syntax to preserve type information:

```python
class EntityManager[E: Entity]:
    def insert(self, entity: E) -> E: ...
    def get(self, **filters) -> list[E]: ...
    def all(self) -> list[E]: ...
```

Type checkers understand the returned types:

```python
# ✅ Type-safe: alice is inferred as Person
alice = Person(name=Name("Alice"), age=Age(30))
person_manager.insert(alice)

# ✅ Type-safe: persons is inferred as list[Person]
persons: list[Person] = person_manager.all()

# ✅ Type-safe: first_person is inferred as Person | None
first_person = person_manager.filter(age=30).first()

# ❌ Type error: Cannot insert Company into Person manager
company = Company(name=Name("TechCorp"))
person_manager.insert(company)  # Type checker catches this!
```

## Complete CRUD Workflow

```python
from type_bridge import (
    Database, Entity, TypeFlags,
    String, Integer, Boolean,
    Flag, Key, Unique, Card
)

# 1. Define schema
class UserID(String):
    pass

class Username(String):
    pass

class Email(String):
    pass

class Age(Integer):
    pass

class IsActive(Boolean):
    pass

class Tag(String):
    pass

class User(Entity):
    flags = TypeFlags(type_name="user")
    user_id: UserID = Flag(Key)
    username: Username
    email: Email = Flag(Unique)
    age: Age | None = None
    is_active: IsActive | None = None
    tags: list[Tag] = Flag(Card(min=0))

# 2. Connect to database
db = Database(address="localhost:1729", database="mydb")
db.connect()

# 3. Create manager
user_manager = User.manager(db)

# 4. CREATE: Insert users
users = [
    User(
        user_id=UserID("u1"),
        username=Username("alice"),
        email=Email("alice@example.com"),
        age=Age(30),
        is_active=IsActive(True),
        tags=[Tag("python"), Tag("typedb")]
    ),
    User(
        user_id=UserID("u2"),
        username=Username("bob"),
        email=Email("bob@example.com"),
        age=Age(25),
        is_active=IsActive(True),
        tags=[Tag("javascript"), Tag("react")]
    ),
]
user_manager.insert_many(users)

# 5. READ: Fetch users
all_users = user_manager.all()
alice = user_manager.get(username="alice")[0]
active_users = user_manager.filter(is_active=True).execute()

# 6. UPDATE: Modify user
alice = user_manager.get(username="alice")[0]
alice.age = Age(31)
alice.tags = [Tag("python"), Tag("typedb"), Tag("fastapi")]
user_manager.update(alice)

# 7. DELETE: Remove user
deleted_count = user_manager.delete(username="bob")
print(f"Deleted {deleted_count} users")
```

## Best Practices

### 1. Use Bulk Insert for Multiple Entities

```python
# ✅ GOOD: Bulk insert (single transaction)
user_manager.insert_many(users)

# ❌ POOR: Multiple inserts (multiple transactions)
for user in users:
    user_manager.insert(user)
```

### 2. Use `first()` for Single Results

```python
# ✅ GOOD: Use first() for single result
user = user_manager.filter(username="alice").first()
if user:
    print(user.email)

# ❌ POOR: Use get() and index
users = user_manager.get(username="alice")
if users:
    print(users[0].email)
```

### 3. Fetch Before Update

Always fetch the current entity before updating:

```python
# ✅ GOOD: Fetch → Modify → Update
alice = user_manager.get(username="alice")[0]
alice.age = Age(31)
user_manager.update(alice)

# ❌ WRONG: Cannot update without fetching first
alice = User(username=Username("alice"), age=Age(31))
user_manager.update(alice)  # Error: entity not from database
```

### 4. Use Specific Filters

Use key or unique attributes for efficient queries:

```python
# ✅ GOOD: Filter by key or unique attribute
alice = user_manager.get(user_id="u1")[0]
alice = user_manager.get(email="alice@example.com")[0]

# ⚠️ SLOWER: Filter by non-indexed attribute
alice = user_manager.get(age=30)[0]  # May return multiple results
```

### 5. Check Delete Results

Always verify delete operations:

```python
# ✅ GOOD: Check delete count
deleted_count = user_manager.delete(username="alice")
if deleted_count > 0:
    print(f"Successfully deleted {deleted_count} users")
else:
    print("No users deleted")

# ⚠️ POOR: Assume delete succeeded
user_manager.delete(username="alice")
```

## See Also

- [Entities](entities.md) - Entity definition
- [Relations](relations.md) - Relation definition
- [Queries](queries.md) - Advanced query expressions
- [Schema Management](schema.md) - Schema operations

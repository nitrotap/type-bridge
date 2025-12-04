# CRUD Operations

Complete reference for Create, Read, Update, Delete operations in TypeBridge.

## Overview

TypeBridge provides type-safe CRUD managers for entities and relations with a modern fetching API. All operations preserve type information and generate optimized TypeQL queries.

> **Note**: The CRUD module has been refactored into a modular structure for better maintainability, but all imports remain backward compatible. You can continue using `from type_bridge import EntityManager, RelationManager` as before.

## EntityManager

Type-safe manager for entity CRUD operations.

### Creating a Manager

```python
from type_bridge import Database, Entity, TypeFlags

class Person(Entity):
    flags = TypeFlags(name="person")
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

    def put(self, entity: E) -> E:
        """Put a single entity (idempotent insert)."""

    def put_many(self, entities: list[E]) -> list[E]:
        """Put multiple entities (idempotent bulk operation)."""

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

**Note on special characters**: TypeBridge automatically escapes special characters in string attributes (quotes, backslashes) when generating TypeQL queries. You don't need to manually escape values - just pass them as normal Python strings.

## PUT Operations (Idempotent Insert)

PUT operations are idempotent - they insert only if the pattern doesn't exist, making them safe to run multiple times.

| Operation | Behavior |
|-----------|----------|
| **INSERT** | Always creates new instances |
| **PUT** | Idempotent - inserts only if doesn't exist |

```python
# Single PUT
alice = Person(name=Name("Alice"), age=Age(30))
person_manager.put(alice)
person_manager.put(alice)  # No duplicate created

# Bulk PUT
persons = [Person(name=Name("Bob"), age=Age(25)), ...]
person_manager.put_many(persons)
person_manager.put_many(persons)  # No duplicates
```

**Use cases**: Data import scripts, ensuring reference data exists, synchronization with external systems.

**All-or-nothing semantics**: PUT matches the entire pattern - if ANY part doesn't match, ALL is inserted. Use `put_many()` when entities either all exist or all don't exist together.

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

    def delete(self) -> int:
        """Delete all matching entities. Returns count deleted."""

    def update_with(self, func: Callable[[E], None]) -> list[E]:
        """Update entities by applying function. Returns updated entities."""
```

## Update Operations

The update API supports two patterns:
1. **Instance-based**: fetch → modify → update (traditional ORM pattern)
2. **Bulk functional**: filter → update_with function (efficient bulk updates)

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

### Bulk Update with Function

**New in v0.6.0**: Update multiple entities efficiently using `update_with()`:

```python
# Increment age for all persons over 30
updated = person_manager.filter(Age.gt(Age(30))).update_with(
    lambda person: setattr(person, 'age', Age(person.age.value + 1))
)
print(f"Updated {len(updated)} persons")

# Complex updates with function
def promote_to_senior(person):
    """Promote eligible persons to senior status."""
    person.status = Status("senior")
    if person.salary:
        # 10% raise
        person.salary = Salary(int(person.salary.value * 1.1))

# Apply to filtered entities
promoted = person_manager.filter(
    Age.gte(Age(35)),
    Status.eq(Status("regular"))
).update_with(promote_to_senior)

# All updates happen in single transaction
print(f"Promoted {len(promoted)} persons")
```

**How `update_with()` works**:
1. Fetches all entities matching the filter
2. Applies the function to each entity in-place
3. Updates all entities in a single atomic transaction
4. Returns list of updated entities

**Error handling**: If the function raises an error on any entity, the operation stops immediately and raises the error. No partial updates occur (atomic transaction).

**Empty results**: Returns empty list if no entities match the filter.

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

TypeBridge supports two delete patterns:
1. **Direct delete**: `manager.delete(**filters)` - delete with keyword filters
2. **Chainable delete**: `manager.filter(...).delete()` - delete after complex filtering

### Direct Delete

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

### Chainable Delete

**New in v0.6.0**: Delete after complex filtering with expressions:

```python
# Delete all persons over 65
count = person_manager.filter(Age.gt(Age(65))).delete()
print(f"Deleted {count} seniors")

# Delete with multiple expression filters
count = person_manager.filter(
    Age.lt(Age(18)),
    Status.eq(Status("inactive"))
).delete()
print(f"Deleted {count} inactive minors")

# Delete with range filter
count = person_manager.filter(
    Age.gte(Age(18)),
    Age.lt(Age(21))
).delete()

# Returns 0 if no matches
count = person_manager.filter(Age.gt(Age(150))).delete()
assert count == 0
```

**How chainable delete works**:
- Builds TypeQL delete query from all filters (dict-based and expression-based)
- Executes in single atomic transaction
- Returns count of deleted entities (0 if no matches)

**Warning**: Delete operations are permanent and cannot be undone!

## RelationManager

Type-safe manager for relation CRUD operations.

### Creating a Manager

```python
from type_bridge import Relation, TypeFlags, Role

class Employment(Relation):
    flags = TypeFlags(name="employment")
    employee: Role[Person] = Role("employee", Person)
    employer: Role[Company] = Role("employer", Company)
    position: Position
    salary: Salary

# Create manager
employment_manager = Employment.manager(db)
```

### RelationManager Methods

```python
class RelationManager[R: Relation]:
    def insert(self, relation: R) -> R:
        """Insert a single relation."""

    def insert_many(self, relations: list[R]) -> list[R]:
        """Insert multiple relations (bulk operation)."""

    def put(self, relation: R) -> R:
        """Put a single relation (idempotent insert)."""

    def put_many(self, relations: list[R]) -> list[R]:
        """Put multiple relations (idempotent bulk operation)."""

    def get(self, **filters) -> list[R]:
        """Get relations matching attribute/role player filters."""

    def filter(self, **filters) -> RelationQuery[R]:
        """Create chainable query with filters."""

    def group_by(self, *fields) -> RelationGroupByQuery[R]:
        """Create group-by query for aggregations."""

    def all(self) -> list[R]:
        """Get all relations of this type."""

    def delete(self, **filters) -> int:
        """Delete relations matching filters. Returns count."""

    def update(self, relation: R) -> R:
        """Update relation in database."""
```

### Insert Relations

```python
# Single insert
employment = Employment(
    employee=alice,
    employer=techcorp,
    position=Position("Senior Engineer"),
    salary=Salary(120000)
)
employment_manager.insert(employment)

# Bulk insert
employments = [
    Employment(employee=alice, employer=techcorp, position=Position("Engineer"), salary=Salary(100000)),
    Employment(employee=bob, employer=startup, position=Position("Designer"), salary=Salary(90000)),
    Employment(employee=charlie, employer=techcorp, position=Position("Manager"), salary=Salary(130000)),
]
employment_manager.insert_many(employments)
```

### PUT Relations (Idempotent Insert)

PUT operations for relations work the same as entities - idempotent and safe to run multiple times:

```python
# Single PUT
employment = Employment(employee=alice, employer=techcorp, position=Position("Engineer"))
employment_manager.put(employment)
employment_manager.put(employment)  # No duplicate

# Bulk PUT
employments = [Employment(employee=alice, employer=techcorp, ...), ...]
employment_manager.put_many(employments)
employment_manager.put_many(employments)  # No duplicates
```

### Fetch Relations

#### Get All Relations

```python
# Fetch all employments
all_employments = employment_manager.all()

for employment in all_employments:
    print(f"{employment.employee.name}: {employment.position}")
```

#### Get with Filters

Filter by both attributes and role players:

```python
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

# Filter by both role players
specific_employment = employment_manager.get(
    employee=alice,
    employer=techcorp
)
```

#### Chainable Queries

**New in v0.6.0**: RelationManager now supports the same chainable query API as EntityManager:

```python
# Basic query
query = employment_manager.filter(position="Engineer")
results = query.execute()

# Chained query with pagination
results = employment_manager.filter(position="Engineer").limit(10).offset(5).execute()

# Get first matching relation (returns Relation | None)
first_employment = employment_manager.filter(employee=alice).first()

if first_employment:
    print(f"Found: {first_employment.position}")
else:
    print("Not found")

# Count matching relations
count = employment_manager.filter(position="Engineer").count()
print(f"Found {count} engineers")
```

#### RelationQuery Methods

**New in v0.6.0**: Complete API parity with EntityQuery:

```python
class RelationQuery[R: Relation]:
    def filter(self, **filters) -> RelationQuery[R]:
        """Add additional filters (attributes and role players)."""

    def limit(self, n: int) -> RelationQuery[R]:
        """Limit number of results."""

    def offset(self, n: int) -> RelationQuery[R]:
        """Skip first n results."""

    def execute(self) -> list[R]:
        """Execute query and return results."""

    def first(self) -> R | None:
        """Get first result or None."""

    def count(self) -> int:
        """Count matching relations."""

    def delete(self) -> int:
        """Delete all matching relations. Returns count deleted."""

    def update_with(self, func: Callable[[R], None]) -> list[R]:
        """Update relations by applying function. Returns updated relations."""

    def aggregate(self, *aggregates) -> dict[str, Any]:
        """Execute aggregation queries."""

    def group_by(self, *fields) -> RelationGroupByQuery[R]:
        """Group relations by field values."""
```

### Update Relations

The update API supports two patterns (same as EntityManager):
1. **Instance-based**: fetch → modify → update (traditional ORM pattern)
2. **Bulk functional**: filter → update_with function (efficient bulk updates)

#### Basic Update

```python
# Step 1: Fetch relation
employment = employment_manager.get(employee=alice, employer=techcorp)[0]

# Step 2: Modify attributes
employment.position = Position("Staff Engineer")
employment.salary = Salary(150000)

# Step 3: Persist changes
employment_manager.update(employment)
```

#### Update Single-Value Attributes

```python
# Fetch relation
employment = employment_manager.get(employee=alice)[0]

# Modify attributes
employment.position = Position("Principal Engineer")
employment.salary = Salary(180000)
employment.start_date = StartDate("2024-01-01")

# Persist changes
employment_manager.update(employment)
```

#### Update Multi-Value Attributes

```python
# Fetch relation
employment = employment_manager.get(employee=alice)[0]

# Replace all values (deletes old, inserts new)
employment.responsibilities = [
    Responsibility("Team lead"),
    Responsibility("Architecture"),
    Responsibility("Mentoring")
]

# Persist changes
employment_manager.update(employment)

# Clear multi-value attribute
employment.responsibilities = []
employment_manager.update(employment)
```

#### Bulk Update with Function

**New in v0.6.0**: Update multiple relations efficiently using `update_with()`:

```python
# Give all engineers a 10% raise
updated = employment_manager.filter(position="Engineer").update_with(
    lambda emp: setattr(emp, 'salary', Salary(int(emp.salary.value * 1.1)))
)
print(f"Updated {len(updated)} engineers")

# Complex updates with function
def promote_to_senior(employment):
    """Promote engineers to senior level."""
    # Add "Senior" prefix
    employment.position = Position(f"Senior {employment.position.value}")
    # 20% raise
    if employment.salary:
        employment.salary = Salary(int(employment.salary.value * 1.2))

# Apply to filtered relations
promoted = employment_manager.filter(
    position="Engineer",
    employee=alice  # Only Alice's employments
).update_with(promote_to_senior)

# All updates happen in single transaction
print(f"Promoted {len(promoted)} employments")
```

**How `update_with()` works for relations**:
1. Fetches all relations matching the filter
2. Stores original attribute values (needed to uniquely identify relations)
3. Applies the function to each relation in-place
4. Updates all relations in a single atomic transaction using original values for matching
5. Returns list of updated relations

**Why original values matter**: In TypeDB, multiple relations can have the same role players (e.g., Alice can have multiple employments at TechCorp). The update query matches each relation by both its role players AND its original attribute values to ensure the correct relation is updated.

**Error handling**: If the function raises an error on any relation, the operation stops immediately and raises the error. No partial updates occur (atomic transaction).

**Empty results**: Returns empty list if no relations match the filter.

### Delete Relations

TypeBridge supports two delete patterns for relations (same as entities):
1. **Direct delete**: `manager.delete(**filters)` - delete with keyword filters
2. **Chainable delete**: `manager.filter(...).delete()` - delete after complex filtering

#### Direct Delete

Delete relations matching filter criteria:

```python
# Delete by attribute
deleted_count = employment_manager.delete(position="Intern")
print(f"Deleted {deleted_count} intern positions")

# Delete by role player
deleted_count = employment_manager.delete(employee=alice)
print(f"Deleted {deleted_count} of Alice's employments")

# Delete with multiple filters (AND logic)
deleted_count = employment_manager.delete(
    employee=alice,
    employer=techcorp
)
print(f"Deleted {deleted_count} employments")

# Delete by both role players
deleted_count = employment_manager.delete(
    employee=bob,
    employer=startup
)
```

#### Chainable Delete

**New in v0.6.0**: Delete after complex filtering with expressions:

```python
# Delete high-salary employments
count = employment_manager.filter(Salary.gt(Salary(150000))).delete()
print(f"Deleted {count} high-salary employments")

# Delete with multiple expression filters
count = employment_manager.filter(
    Salary.lt(Salary(50000)),
    Position.eq(Position("Intern"))
).delete()
print(f"Deleted {count} low-paid interns")

# Delete by role player using filter
count = employment_manager.filter(employee=alice).delete()
print(f"Deleted all of Alice's employments: {count}")

# Returns 0 if no matches
count = employment_manager.filter(Salary.gt(Salary(1000000))).delete()
assert count == 0
```

**How chainable delete works for relations**:
- Builds TypeQL delete query from all filters (dict-based, expression-based, and role player filters)
- Executes in single atomic transaction
- Returns count of deleted relations (0 if no matches)

**Warning**: Delete operations are permanent and cannot be undone!

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
    flags = TypeFlags(name="user")
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

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**type-bridge** is a Python ORM (Object-Relational Mapper) for TypeDB, designed to provide Pythonic abstractions over TypeDB's native TypeQL query language.

TypeDB is a strongly-typed database with a unique type system that includes:
- **Entities**: Independent objects with attributes
- **Relations**: Connections between entities with role players
- **Attributes**: Values owned by entities and relations

## Key TypeDB Concepts

When implementing features, keep these TypeDB-specific concepts in mind:

1. **TypeQL Schema Definition Language**: TypeDB requires schema definitions before data insertion
2. **Role Players**: Relations in TypeDB are first-class citizens with explicit role players (not just foreign keys)
3. **Attribute Ownership**: Attributes can be owned by multiple entity/relation types
4. **Inheritance**: TypeDB supports type hierarchies for entities, relations, and attributes
5. **Rule-based Inference**: TypeDB can derive facts using rules (important for query design)

## Python Version

This project requires **Python 3.13+** (see .python-version)

## Development Commands

### Package Management
```bash
uv sync --extra dev          # Install dependencies including dev tools
uv pip install -e ".[dev]"   # Install in editable mode
```

### Docker Setup for Integration Tests

Integration tests require a TypeDB 3.5.5 server. The project includes Docker configuration for automated setup:

**Requirements:**
- Docker and Docker Compose installed
- Ports: 1729 (TypeDB server)

**Docker is managed automatically** by the test fixtures. Simply run:
```bash
./test-integration.sh          # Starts Docker, runs tests, stops Docker
```

**Manual Docker control:**
```bash
docker compose up -d           # Start TypeDB container
docker compose down            # Stop TypeDB container
docker compose logs typedb     # View TypeDB logs
```

**Skip Docker (use existing server):**
```bash
USE_DOCKER=false uv run pytest -m integration
```

### Testing
```bash
# Unit tests (fast, no external dependencies)
uv run pytest                              # Run unit tests only (default)
uv run pytest -v                           # Run unit tests with verbose output
uv run pytest -k test_name                 # Run specific unit test

# Integration tests (require running TypeDB)
# Option 1: Use Docker (recommended - automatic management)
./test-integration.sh                     # Run integration tests with Docker
./test-integration.sh -v                  # Run integration tests with Docker (verbose)

# Option 2: Use existing TypeDB server (set USE_DOCKER=false)
# First, start TypeDB 3.x server: typedb server
USE_DOCKER=false uv run pytest -m integration    # Run integration tests (no Docker)
USE_DOCKER=false uv run pytest -m integration -v # Run integration tests (verbose)

# Run all tests (unit + integration)
uv run pytest -m ""                       # Run all tests (Docker managed automatically)
```

### Linting
```bash
uv run ruff check .          # Check code style
uv run ruff format .         # Format code
```

### Running Examples
```bash
# Basic CRUD examples (start here!)
uv run python examples/basic/crud_01_define.py  # Schema definition and basic usage
uv run python examples/basic/crud_02_insert.py  # Bulk insertion
uv run python examples/basic/crud_03_read.py    # Fetching API: get(), filter(), all()
uv run python examples/basic/crud_04_update.py  # Update API for single and multi-value attrs

# Advanced examples
uv run python examples/advanced/schema_01_manager.py     # Schema operations
uv run python examples/advanced/schema_02_comparison.py  # Schema diff and comparison
uv run python examples/advanced/schema_03_conflict.py    # Conflict detection
uv run python examples/advanced/pydantic_features.py     # Pydantic integration
uv run python examples/advanced/type_safety.py           # Literal types for type safety
uv run python examples/advanced/string_representation.py # Custom __str__ and __repr__
```

## Project Structure

```
type_bridge/
├── __init__.py           # Main package exports
├── attribute/            # Modular attribute system (refactored from attribute.py)
│   ├── __init__.py       # Attribute package exports
│   ├── base.py           # Abstract Attribute base class
│   ├── string.py         # String attribute with concatenation operations
│   ├── integer.py        # Integer attribute with arithmetic operations
│   ├── double.py         # Double attribute
│   ├── boolean.py        # Boolean attribute
│   ├── datetime.py       # DateTime attribute
│   └── flags.py          # Flag system (Key, Unique, Card, TypeFlags)
├── models.py             # Base Entity and Relation classes using attribute ownership model
├── query.py              # TypeQL query builder
├── session.py            # Database connection and transaction management
├── crud.py               # EntityManager and RelationManager for CRUD ops with fetching API
└── schema/               # Modular schema management (refactored from schema.py)
    ├── __init__.py       # Schema package exports
    ├── manager.py        # SchemaManager for schema operations
    ├── info.py           # SchemaInfo container
    ├── diff.py           # SchemaDiff, EntityChanges, RelationChanges for comparison
    ├── migration.py      # MigrationManager for migrations
    └── exceptions.py     # SchemaConflictError for conflict detection

examples/
├── basic/                        # Basic CRUD examples (start here!)
│   ├── crud_01_define.py         # Schema definition and basic usage
│   ├── crud_02_insert.py         # Bulk insertion
│   ├── crud_03_read.py           # Fetching API: get(), filter(), all()
│   └── crud_04_update.py         # Update API for single and multi-value attrs
└── advanced/                     # Advanced features
    ├── schema_01_manager.py      # Schema operations
    ├── schema_02_comparison.py   # Schema diff and comparison
    ├── schema_03_conflict.py     # Conflict detection and resolution
    ├── pydantic_features.py      # Pydantic integration
    ├── type_safety.py            # Literal type support
    └── string_representation.py  # Custom __str__ and __repr__

tests/
├── conftest.py                   # Pytest configuration
├── unit/                         # Unit tests (fast, isolated, no external dependencies)
│   ├── core/                     # Core functionality tests
│   │   ├── test_basic.py         # Basic entity/relation/attribute API
│   │   ├── test_inheritance.py   # Inheritance and type hierarchies
│   │   └── test_pydantic.py      # Pydantic integration and validation
│   ├── attributes/               # Attribute type tests
│   │   ├── test_boolean.py       # Boolean attribute type
│   │   ├── test_date.py          # Date attribute type
│   │   ├── test_datetime_tz.py   # DateTimeTZ attribute type
│   │   ├── test_decimal.py       # Decimal attribute type
│   │   ├── test_double.py        # Double attribute type
│   │   ├── test_duration.py      # Duration attribute type (ISO 8601)
│   │   ├── test_formatting.py    # Mixed attribute formatting
│   │   ├── test_integer.py       # Integer attribute type
│   │   └── test_string.py        # String attribute type
│   ├── flags/                    # Flag system tests
│   │   ├── test_base_flag.py     # Base flag for schema exclusion
│   │   ├── test_cardinality.py   # Card API for cardinality constraints
│   │   ├── test_typename_case.py # Entity/Relation type name formatting
│   │   └── test_attribute_typename_case.py # Attribute name formatting
│   └── crud/                     # CRUD operation tests
│       └── test_update_api.py    # Update API for entities
└── integration/                  # Integration tests (require running TypeDB)
    ├── conftest.py               # Integration test fixtures (DB connection, cleanup)
    ├── test_schema_operations.py # Schema creation, migration, conflict detection
    ├── test_crud_workflows.py    # End-to-end CRUD operations
    └── test_query_building.py    # Complex queries with real data
```

## Testing Strategy

TypeBridge uses a two-tier testing approach with **100% test pass rate (417/417 tests)**:

### Unit Tests (Default)

Located in `tests/unit/` with organized subdirectories:
- `core/`: Basic entity/relation/attribute API, inheritance
- `attributes/`: All 9 attribute types with dedicated test files
- `flags/`: Flag system (base flags, cardinality, type name formatting)
- `expressions/`: Query expression API (field references, comparisons, aggregations)
- `validation/`: Reserved word and keyword validation
- `type-check-except/`: Validation tests intentionally excluded from type checking

Characteristics:
- **Fast**: Run in ~0.3 seconds without external dependencies
- **Isolated**: Test individual components in isolation
- **No TypeDB required**: Use mocks and in-memory validation
- **Run by default**: `pytest` runs unit tests only
- **284 tests total**: Organized by functionality

Coverage:
- Core API: Entity/Relation creation, schema generation, inheritance
- Attribute types: All 9 types with dedicated test files
  - Boolean, Date, DateTime, DateTimeTZ, Decimal, Double, Duration, Integer, String
  - Mixed formatting tests for query generation
- Flag system: Base flags, cardinality, type name cases
- Expression API: Field references, comparisons, string operations, aggregations
- Validation: Pydantic integration, keyword validation, type checking, schema validation
  - Duplicate attribute type detection

### Integration Tests

Located in `tests/integration/` with organized subdirectories:
- `crud/`: CRUD operations organized by type
  - `entities/`: Entity insert, fetch, update, delete operations
  - `relations/`: Relation operations including abstract role types
  - `attributes/`: All 9 attribute types (insert, fetch, update, delete)
  - `interop/`: Cross-type operations and mixed queries
- `queries/`: Query builder and expression tests
- `schema/`: Schema operations, conflict detection, migration

Characteristics:
- **Sequential**: Use `@pytest.mark.order()` for predictable execution order
- **Real database**: Require running TypeDB 3.x server
- **End-to-end**: Test complete workflows from schema to queries
- **Explicit execution**: Must use `pytest -m integration`
- **133 tests total**: Full CRUD, schema, and query coverage

Coverage:
- Schema creation, conflict detection, inheritance
- CRUD operations for all 9 attribute types (insert, fetch, update, delete)
- Multi-value attribute operations
- Complex queries with real data (pagination, filtering, role players)
- Query expressions (comparisons, string operations, boolean logic, aggregations)
- Relations with abstract entity types in role definitions
- TypeDB 3.x specific features (proper `isa` syntax, offset before limit)
- Transaction management and database lifecycle

**Setup for integration tests:**
```bash
# Option 1: Use Docker (recommended - automatic)
./test-integration.sh -v

# Option 2: Use existing TypeDB server
# 1. Start TypeDB 3.x server
typedb server

# 2. Run integration tests (skip Docker)
USE_DOCKER=false uv run pytest -m integration -v
```

**Test execution patterns:**
```bash
# Unit tests only (default, fast)
uv run pytest                              # All 284 unit tests

# Run specific unit test category
uv run pytest tests/unit/core/             # Core tests
uv run pytest tests/unit/attributes/       # Attribute tests
uv run pytest tests/unit/flags/            # Flag tests
uv run pytest tests/unit/expressions/      # Expression tests
uv run pytest tests/unit/validation/       # Validation tests

# Run specific attribute type test
uv run pytest tests/unit/attributes/test_integer.py -v
uv run pytest tests/unit/attributes/test_string.py -v
uv run pytest tests/unit/attributes/test_boolean.py -v

# Integration tests only (requires TypeDB)
uv run pytest -m integration              # All 133 integration tests

# Run specific integration test category
uv run pytest tests/integration/crud/entities/ -v      # Entity CRUD tests
uv run pytest tests/integration/crud/relations/ -v    # Relation CRUD tests
uv run pytest tests/integration/queries/ -v           # Query expression tests
uv run pytest tests/integration/schema/ -v            # Schema operation tests

# All tests (unit + integration)
uv run pytest -m ""                       # All 417 tests
./test.sh                                 # Full test suite with detailed output
./check.sh                                # Linting and type checking

# Specific integration test files
uv run pytest tests/integration/schema/test_conflict.py -v
uv run pytest tests/integration/queries/test_pagination.py -v
uv run pytest tests/integration/queries/test_expressions.py -v
uv run pytest tests/integration/crud/relations/test_abstract_roles.py -v
```

## TypeDB ORM Design Considerations

When implementing ORM features:

1. **Mapping Challenge**: TypeDB's type system is richer than traditional ORMs - relations are not simple foreign keys
2. **TypeQL Generation**: The ORM needs to generate valid TypeQL queries from Python API calls
3. **Transaction Semantics**: TypeDB has strict transaction types (read, write) that must be respected
4. **Schema Evolution**: Consider how Python model changes map to TypeDB schema updates
5. **Role Handling**: Relations require explicit role mapping which is unique to TypeDB

## API Design Principles

TypeBridge follows TypeDB's type system closely:

1. **Attributes are independent types**: Define attributes once, reuse across entities/relations
   ```python
   class Name(String):
       pass

   class Person(Entity):
       name: Name  # Person owns 'name'

   class Company(Entity):
       name: Name  # Company also owns 'name'
   ```

2. **Use TypeFlags, not dunder attributes**:
   ```python
   class Person(Entity):
       flags = TypeFlags(type_name="person")  # Clean API
       # NOT: __type_name__ = "person"  # Deprecated
   ```

3. **Use Flag system for Key/Unique/Card annotations**:
   ```python
   from type_bridge import Flag, Key, Unique, Card

   name: Name = Flag(Key)                    # @key (implies @card(1..1))
   email: Email = Flag(Unique)               # @unique (default @card(1..1))
   age: Age | None = None                    # @card(0..1) - PEP 604 syntax, explicit default
   tags: list[Tag] = Flag(Card(min=2))       # @card(2..)
   jobs: list[Job] = Flag(Card(1, 5))        # @card(1..5)
   languages: list[Lang] = Flag(Card(max=3)) # @card(0..3) (min defaults to 0)
   ```

   **Note**: Use modern PEP 604 syntax (`X | None`) instead of `Optional[X]`.

4. **Python inheritance maps to TypeDB supertypes**:
   ```python
   class Animal(Entity):
       flags = TypeFlags(abstract=True)

   class Dog(Animal):  # Generates: entity dog, sub animal
       pass
   ```

   Multi-level inheritance example:
   ```python
   class Content(Entity):
       flags = TypeFlags(type_name="content", abstract=True)
       # Generates: entity content @abstract,

   class Page(Content):
       flags = TypeFlags(type_name="page", abstract=True)
       # Generates: entity page @abstract, sub content,

   class Person(Page):
       flags = TypeFlags(type_name="person")
       # Generates: entity person, sub page,
   ```

5. **Cardinality semantics**:
   - `Type` → exactly one @card(1..1) - default
   - `Type | None` → zero or one @card(0..1) - use PEP 604 syntax
   - `list[Type] = Flag(Card(min=N))` → N or more @card(N..)
   - `list[Type] = Flag(Card(max=N))` → zero to N @card(0..N)
   - `list[Type] = Flag(Card(min, max))` → min to max @card(min..max)

## Schema Validation Rules

TypeBridge enforces TypeDB best practices through automatic validation during schema generation.

### Duplicate Attribute Type Detection

**Rule**: Each semantic field in an entity or relation MUST use a distinct attribute type.

**Why this matters**: TypeDB does not store Python field names - it only stores attribute types and their values. When you use the same attribute type for multiple fields (e.g., `created: TimeStamp` and `modified: TimeStamp`), TypeDB sees a single ownership relationship: `Issue owns TimeStamp`, not separate `created` and `modified` fields. This causes cardinality constraint violations.

**Validation**: The schema manager will raise `SchemaValidationError` if duplicate attribute types are detected.

**Example - Incorrect (will raise error)**:
```python
from type_bridge import Entity, SchemaManager
from type_bridge.attribute.datetime import DateTime
from type_bridge.attribute.string import String
from type_bridge.attribute.flags import Flag, Key

class TimeStamp(DateTime):
    pass

class IssueKey(String):
    pass

class Issue(Entity):
    key: IssueKey = Flag(Key)
    created: TimeStamp   # ❌ Error: duplicate attribute type
    modified: TimeStamp  # ❌ Error: duplicate attribute type

# Raises SchemaValidationError:
# "TimeStamp used in fields: 'created', 'modified'"
schema_manager = SchemaManager(db)
schema_manager.register(Issue)
schema_manager.generate_schema()  # ❌ Raises error
```

**Example - Correct (distinct attribute types)**:
```python
class CreatedStamp(DateTime):
    """Timestamp for when entity was created"""
    pass

class ModifiedStamp(DateTime):
    """Timestamp for when entity was last modified"""
    pass

class IssueKey(String):
    pass

class Issue(Entity):
    key: IssueKey = Flag(Key)
    created: CreatedStamp   # ✓ Distinct type
    modified: ModifiedStamp # ✓ Distinct type

# Generates correct TypeQL:
# entity Issue,
#     owns IssueKey @key,
#     owns CreatedStamp @card(1..1),
#     owns ModifiedStamp @card(1..1);
#
# Note: Each attribute type gets its own ownership line with cardinality annotation.
# This is TypeDB's semantic model - ownership is per attribute type, not per field name.
schema_manager = SchemaManager(db)
schema_manager.register(Issue)
schema_manager.generate_schema()  # ✓ Success
```

**Best practice**: Use distinct attribute types for each semantic field, even when they share the same underlying value type (string, datetime, etc.). This makes schemas more expressive and avoids ownership conflicts.

**Benefits**:
- Prevents cardinality constraint violations at runtime
- Makes schema more self-documenting (attribute names reflect their purpose)
- Allows different constraints per field in the future (e.g., unique created but not modified)
- Catches design errors early during schema generation instead of during data insertion

**Discussion**: Is this validation approach correct? Should TypeBridge enforce this rule, or provide it as an optional warning? Feedback welcome on the design decision to fail fast vs. allow users to handle edge cases manually.

## TypeQL Syntax Requirements

When generating TypeQL schema definitions, always use the following correct syntax:

1. **Attribute definitions**:
   ```typeql
   attribute name, value string;
   ```
   ❌ NOT: `name sub attribute, value string;`

2. **Entity definitions**:
   ```typeql
   entity person,
       owns name @key,
       owns age @card(0..1);
   ```
   ❌ NOT: `person sub entity,`

3. **Entity inheritance with abstract**:
   ```typeql
   # Abstract entity without parent
   entity content @abstract,
       owns id @key;

   # Abstract entity with inheritance
   entity page @abstract, sub content,
       owns page-id,
       owns bio;

   # Concrete entity with inheritance
   entity person sub profile,
       owns email;
   ```
   Note: `@abstract` comes before `sub`, separated by comma.

4. **Relation definitions**:
   ```typeql
   relation employment,
       relates employee,
       relates employer,
       owns salary @card(0..1);
   ```
   ❌ NOT: `employment sub relation,`

5. **Relation inheritance with abstract**:
   ```typeql
   # Abstract relation
   relation social-relation @abstract,
       relates related @card(2);

   # Concrete relation with inheritance
   relation friendship sub social-relation,
       relates friend as related @card(2);
   ```

6. **Cardinality annotations**:
   - Use `..` (double dot) syntax: `@card(1..5)` ✓
   - ❌ NOT comma syntax: `@card(1,5)`
   - Unbounded max: `@card(2..)` ✓

7. **Key and Unique annotations**:
   - `@key` implies `@card(1..1)`, never output both
   - `@unique` with default `@card(1..1)`, omit `@card` annotation
   - Only output explicit `@card` when it differs from the implied cardinality

## Attribute Types

TypeBridge provides built-in attribute types that map to TypeDB's value types:

- `String` → `value string` in TypeDB
- `Integer` → `value integer` in TypeDB (renamed from `Long` to match TypeDB 3.x)
- `Double` → `value double` in TypeDB (floating-point)
- `Decimal` → `value decimal` in TypeDB (fixed-point, 19 decimal digits precision)
- `Boolean` → `value boolean` in TypeDB
- `Date` → `value date` in TypeDB (date only, no time)
- `DateTime` → `value datetime` in TypeDB (naive datetime, no timezone)
- `DateTimeTZ` → `value datetime-tz` in TypeDB (timezone-aware datetime)
- `Duration` → `value duration` in TypeDB (ISO 8601 duration, calendar-aware)

Example:
```python
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal as DecimalType
from type_bridge import String, Integer, Double, Decimal, Date, DateTime, DateTimeTZ, Duration

class Name(String):
    pass

class Age(Integer):  # Note: Integer, not Long
    pass

class Score(Double):  # Floating-point number
    pass

class Price(Decimal):  # Fixed-point decimal with high precision
    pass

class BirthDate(Date):  # Date only (no time)
    pass

class CreatedAt(DateTime):  # Naive datetime (no timezone)
    pass

class UpdatedAt(DateTimeTZ):  # Timezone-aware datetime
    pass

class SessionDuration(Duration):  # ISO 8601 duration
    pass
```

### Double vs Decimal

TypeDB provides two numeric types for non-integer values:

1. **Double** (`value double`): Floating-point number (standard IEEE 754)
   - Use for: Scientific calculations, measurements, approximate values
   - Example: `Score(95.5)`, `Temperature(37.2)`

2. **Decimal** (`value decimal`): Fixed-point number with exact precision
   - 64 bits for integer part, 19 decimal digits of precision after decimal point
   - Range: −2^63 to 2^63 − 10^−19
   - Use for: Financial calculations, monetary values, exact decimal representation
   - TypeQL syntax: Values use `dec` suffix (e.g., `0.02dec`)
   - Example:
     ```python
     from decimal import Decimal as DecimalType

     class AccountBalance(Decimal):
         pass

     # Use string for exact precision (recommended)
     balance = AccountBalance("1234.567890123456789")

     # In TypeQL insert query: has AccountBalance 1234.567890123456789dec
     ```

**When to use Decimal:**
- Financial applications (account balances, prices, tax calculations)
- When exact decimal representation is required
- When you need to avoid floating-point rounding errors

**When to use Double:**
- Scientific measurements
- Statistical calculations
- When approximate values are acceptable

### Date, DateTime, and DateTimeTZ

TypeDB provides three temporal types with distinct use cases:

#### 1. Date (`value date`)
Date-only values without time information.

- **Use for**: Birth dates, publish dates, deadlines, anniversaries
- **Format**: ISO 8601 date (YYYY-MM-DD)
- **Range**: January 1, 262144 BCE to December 31, 262142 CE
- **Example**:
  ```python
  from datetime import date

  class PublishDate(Date):
      pass

  # Usage
  book = Book(publish_date=PublishDate(date(2024, 3, 30)))
  # In TypeQL: has PublishDate 2024-03-30
  ```

#### 2. DateTime (`value datetime`)
Naive datetime without timezone information.

- **Use for**: Timestamps where timezone context is implicit or unnecessary
- **Format**: ISO 8601 datetime (YYYY-MM-DDTHH:MM:SS)
- **Example**:
  ```python
  from datetime import datetime

  class CreatedAt(DateTime):
      pass

  # Usage
  event = Event(created_at=CreatedAt(datetime(2024, 3, 30, 10, 30, 45)))
  # In TypeQL: has CreatedAt 2024-03-30T10:30:45
  ```

#### 3. DateTimeTZ (`value datetime-tz`)
Timezone-aware datetime with explicit timezone information.

- **Use for**: Distributed systems, events across timezones, UTC timestamps
- **Format**: ISO 8601 with timezone (YYYY-MM-DDTHH:MM:SS±HH:MM or with IANA TZ identifier)
- **Example**:
  ```python
  from datetime import datetime, timezone

  class UpdatedAt(DateTimeTZ):
      pass

  # Usage
  record = Record(updated_at=UpdatedAt(datetime(2024, 3, 30, 10, 30, 45, tzinfo=timezone.utc)))
  # In TypeQL: has UpdatedAt 2024-03-30T10:30:45+00:00
  ```

**When to use each type:**
- **Date**: When you only care about the calendar date (birthdays, publish dates, deadlines)
- **DateTime**: When you need date + time but timezone is implicit (local events, single-timezone systems)
- **DateTimeTZ**: When timezone matters (global events, distributed systems, UTC timestamps)

### DateTime and DateTimeTZ Conversions

TypeBridge provides conversion methods between DateTime and DateTimeTZ:

**Add timezone to DateTime:**
```python
# Implicit: add system timezone
naive_dt = DateTime(datetime(2024, 1, 15, 10, 30, 45))
aware_dt = naive_dt.add_timezone()  # Uses system timezone

# Explicit: add specific timezone
from datetime import timezone, timedelta
jst = timezone(timedelta(hours=9))
aware_jst = naive_dt.add_timezone(jst)  # Add JST timezone
aware_utc = naive_dt.add_timezone(timezone.utc)  # Add UTC timezone
```

**Strip timezone from DateTimeTZ:**
```python
# Implicit: just strip timezone
aware_dt = DateTimeTZ(datetime(2024, 1, 15, 10, 30, 45, tzinfo=timezone.utc))
naive_dt = aware_dt.strip_timezone()  # Strips timezone as-is

# Explicit: convert to timezone first, then strip
jst = timezone(timedelta(hours=9))
naive_jst = aware_dt.strip_timezone(jst)  # Convert to JST, then strip
```

**Conversion semantics:**
- `DateTime.add_timezone(tz=None)`: If tz is None, adds system timezone; otherwise adds specified timezone
- `DateTimeTZ.strip_timezone(tz=None)`: If tz is None, strips timezone as-is; otherwise converts to tz first, then strips

### Duration Type

TypeDB's `duration` type represents calendar-aware time spans using ISO 8601 duration format.

**Key characteristics:**
- Storage: 32-bit months, 32-bit days, 64-bit nanoseconds
- Format: ISO 8601 duration (e.g., `P1Y2M3DT4H5M6.789S`)
- **Partially ordered**: `P1M` and `P30D` cannot be compared directly
- **Calendar-aware**: `P1D` ≠ `PT24H`, `P1M` varies by month

**ISO 8601 Duration Syntax:**
```
P[years]Y[months]M[days]DT[hours]H[minutes]M[seconds]S
```

Date components (before T):
- `Y` = years
- `M` = months
- `W` = weeks (cannot combine with other units)
- `D` = days

Time components (after T):
- `H` = hours
- `M` = minutes
- `S` = seconds (can have up to 9 decimal digits for nanoseconds)

**Examples:**
```python
from datetime import timedelta
from type_bridge import Duration, DateTime, Entity, TypeFlags

class EventCadence(Duration):
    pass

# Simple durations
hourly = EventCadence("PT1H")                      # 1 hour
daily = EventCadence("P1D")                        # 1 day
weekly = EventCadence("P7D")                       # 7 days (weeks converted to days)
monthly = EventCadence("P1M")                      # 1 month

# Complex duration
complex = EventCadence("P1Y2M3DT4H5M6.789S")      # 1 year, 2 months, 3 days, 4:05:06.789

# From Python timedelta (converted to Duration internally)
from_td = EventCadence(timedelta(hours=2, minutes=30))  # PT2H30M

# Ambiguous M disambiguation:
one_month = EventCadence("P1M")   # 1 month (no T)
one_minute = EventCadence("PT1M")  # 1 minute (with T)
```

**Arithmetic operations with DateTime/DateTimeTZ:**
```python
from datetime import datetime, timezone

# Add duration to datetime
start = DateTime(datetime(2024, 1, 31, 14, 0, 0))
one_month = Duration("P1M")
result = start + one_month  # Feb 29, 2024 (leap year, last day of month)

# Add duration to timezone-aware datetime
start_utc = DateTimeTZ(datetime(2024, 1, 31, 14, 0, 0, tzinfo=timezone.utc))
result_utc = start_utc + one_month  # Respects timezone

# Duration arithmetic
d1 = Duration("P1M")
d2 = Duration("P15D")
total = d1 + d2  # P1M15D
```

**Important notes:**
- Addition order matters: `P1M + P1D` ≠ `P1D + P1M` (calendar arithmetic)
- Month addition respects calendar:
  - Jan 31 + 1 month = Feb 29 (uses last day of month if invalid)
- Duration with DateTimeTZ respects DST and timezone changes
- Durations are partially ordered (can't compare `P1M` vs `P30D`)

**When to use Duration:**
- Recurring events (monthly meetings, weekly tasks)
- Calendar-relative time spans (add 1 month, 3 days)
- Time intervals that respect calendar boundaries
- When months/years are needed (not just days/hours)

**When NOT to use Duration:**
- Simple time intervals → use `Integer` (seconds) or `Double` (hours)
- Fixed-length periods → use `Integer` for seconds
- When ordering/comparison is required → use fixed units

## Deprecated APIs

The following APIs are deprecated and should NOT be used:

- ❌ `Long` - Renamed to `Integer` to match TypeDB 3.x (use `Integer` instead)
- ❌ `Cardinal` - Use `Flag(Card(...))` instead
- ❌ `Min[N, Type]` - Use `list[Type] = Flag(Card(min=N))` instead
- ❌ `Max[N, Type]` - Use `list[Type] = Flag(Card(max=N))` instead
- ❌ `Range[Min, Max, Type]` - Use `list[Type] = Flag(Card(min, max))` instead
- ❌ `Optional[Type]` - Use `Type | None` (PEP 604 syntax) instead
- ❌ `Union[X, Y]` - Use `X | Y` (PEP 604 syntax) instead

These were removed or updated to provide a cleaner, more consistent API following modern Python standards.

## Internal Type System

### ModelAttrInfo Dataclass

The codebase uses `ModelAttrInfo` (defined in `models.py`) as a structured type for attribute metadata:

```python
@dataclass
class ModelAttrInfo:
    typ: type[Attribute]  # The attribute class (e.g., Name, Age)
    flags: AttributeFlags  # Metadata (Key, Unique, Card)
```

**IMPORTANT**: Always use dataclass attribute access, never dictionary-style access:

```python
# ✅ CORRECT
owned_attrs = Entity.get_owned_attributes()
for field_name, attr_info in owned_attrs.items():
    attr_class = attr_info.typ
    flags = attr_info.flags

# ❌ WRONG - Never use dict-style access
attr_class = attr_info["type"]   # Will fail!
flags = attr_info["flags"]       # Will fail!
```

### Modern Python Type Hints

The project follows modern Python typing standards (Python 3.12+):

1. **PEP 604**: Use `X | Y` instead of `Union[X, Y]`
   ```python
   # ✅ Modern
   age: int | str | None

   # ❌ Deprecated
   from typing import Union, Optional
   age: Optional[Union[int, str]]
   ```

2. **PEP 695**: Use type parameter syntax for generics
   ```python
   # ✅ Modern (Python 3.12+)
   class EntityManager[E: Entity]:
       ...

   # ❌ Old style (still works but verbose)
   from typing import Generic, TypeVar
   E = TypeVar("E", bound=Entity)
   class EntityManager(Generic[E]):
       ...
   ```

3. **No linter suppressions**: Code should pass `ruff` and `pyright` without needing `# noqa` or `# type: ignore` comments

## Type Checking and Static Analysis

TypeBridge uses PEP-681 `@dataclass_transform` decorators on Entity and Relation classes to improve type checker support. This provides:

- Type checker recognition of `Flag()` as a valid field default
- Automatic `__init__` signature inference from class annotations
- Better IDE autocomplete and type hints
- Keyword-only arguments enforced (improved code clarity and safety)

## Keyword-Only Arguments

TypeBridge enforces keyword-only arguments for Entity and Relation constructors using `@dataclass_transform(kw_only_default=True)`. This improves code clarity and prevents positional argument errors.

### Why Keyword-Only?

1. **Clarity**: Explicit field names make code self-documenting
2. **Safety**: Type checkers catch argument order mistakes
3. **Maintainability**: Adding fields doesn't break existing code
4. **Prevention**: Eliminates entire class of positional argument bugs

### Usage Pattern

```python
from type_bridge import Entity, TypeFlags, String, Integer, Flag, Key

class Name(String):
    pass

class Age(Integer):
    pass

class Person(Entity):
    flags = TypeFlags(type_name="person")
    name: Name = Flag(Key)
    age: Age | None = None  # Optional field requires explicit = None

# ✅ CORRECT: Keyword arguments required
person = Person(name=Name("Alice"), age=Age(30))
person2 = Person(name=Name("Bob"))  # age is optional

# ❌ WRONG: Positional arguments not allowed
person = Person(Name("Alice"), Age(30))  # Type error!
```

### Optional Fields Require Explicit Defaults

Optional fields (marked with `| None`) **must** have an explicit `= None` default:

```python
# ✅ CORRECT: Explicit defaults for optional fields
class Person(Entity):
    name: Name = Flag(Key)          # Required field
    age: Age | None = None           # Optional with explicit = None
    email: Email | None = None       # Optional with explicit = None

# ❌ WRONG: Missing defaults on optional fields
class Person(Entity):
    name: Name = Flag(Key)
    age: Age | None                  # Type error: missing default!
    email: Email | None              # Type error: missing default!
```

**Why explicit `= None`?**

1. **Type checking**: Pyright needs explicit defaults to distinguish optional from required fields
2. **IDE support**: Autocomplete works better with explicit optionality
3. **Code clarity**: Makes intent obvious at a glance
4. **Runtime behavior**: Matches static type annotations exactly

### Type Checking Limitations

TypeBridge achieves 0 type errors with Pyright, but there are some edge cases to be aware of:

1. **Optional fields in queries**: When using field references with optional fields, Pyright may incorrectly infer the type:
   ```python
   class Person(Entity):
       score: PersonScore | None = None  # Optional field

   # Pyright may warn about optional field access
   high_scorers = manager.filter(Person.score.gt(PersonScore(90)))  # May show warning
   ```

   **Solution**: Use attribute class methods instead of field references for optional fields:
   ```python
   # ✅ RECOMMENDED: Attribute class method (no warnings)
   high_scorers = manager.filter(PersonScore.gt(PersonScore(90)))

   # Also works, but may trigger type checker warnings
   high_scorers = manager.filter(Person.score.gt(PersonScore(90)))
   ```

2. **Validation tests**: Tests that intentionally check Pydantic validation behavior use raw values and are excluded from type checking via `pyrightconfig.json`. These are located in `tests/unit/type-check-except/`.

### Minimal `Any` Usage

The project minimizes `Any` usage for type safety:
- `Flag()` accepts `Any` for parameters (to handle type aliases like `Key` and `Unique`)
- `Flag()` returns `AttributeFlags` (used as field default)
- All `__get_pydantic_core_schema__` methods use proper TypeVars (`StrValue`, `IntValue`, etc.)
- No other `Any` types in the core attribute system

## CRUD Operations and Fetching API

TypeBridge provides type-safe CRUD managers with a modern fetching API for entities and relations.

### EntityManager

Each Entity class can create a type-safe manager:

```python
from type_bridge import Database, Entity, TypeFlags, String, Integer, Flag, Key

class Name(String):
    pass

class Age(Integer):
    pass

class Person(Entity):
    flags = TypeFlags(type_name="person")
    name: Name = Flag(Key)
    age: Age | None

# Connect to database
db = Database(address="localhost:1729", database="mydb")
db.connect()

# Create manager
person_manager = Person.manager(db)
```

### Fetching Methods

**Insert single entity**:
```python
alice = Person(name=Name("Alice"), age=Age(30))
person_manager.insert(alice)
```

**Bulk insert (more efficient)**:
```python
persons = [
    Person(name=Name("Alice"), age=Age(30)),
    Person(name=Name("Bob"), age=Age(25)),
    Person(name=Name("Charlie"), age=Age(35)),
]
person_manager.insert_many(persons)
```

**Get entities with filters**:
```python
# Get all entities
all_persons = person_manager.all()

# Get with attribute filters
young_persons = person_manager.get(age=25)
```

**Chainable queries with EntityQuery**:
```python
# Create chainable query
query = person_manager.filter(age=30)

# Chain methods
results = query.limit(10).offset(5).execute()

# Get first result
first_person = person_manager.filter(name="Alice").first()  # Returns Person | None

# Count results
count = person_manager.filter(age=30).count()
```

**Delete entities**:
```python
deleted_count = person_manager.delete(name="Alice")
```

**Update entities**:
```python
# Fetch entity
alice = person_manager.get(name="Alice")[0]

# Modify attributes directly
alice.age = Age(31)
alice.tags = [Tag("python"), Tag("typedb"), Tag("ai")]

# Persist changes to database
person_manager.update(alice)

# Typical workflow: Fetch → Modify → Update
bob = person_manager.get(name="Bob")[0]
bob.age = Age(26)
bob.status = Status("active")
bob.tags = [Tag("java"), Tag("python")]
person_manager.update(bob)
```

**TypeQL update semantics**:
- **Single-value attributes** (`@card(0..1)` or `@card(1..1)`): Uses TypeQL `update` clause
- **Multi-value attributes** (e.g., `@card(0..5)`, `@card(2..)`): Deletes all old values, then inserts new ones

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

### RelationManager

Relations support similar operations with role player filtering:

```python
from type_bridge import Relation, TypeFlags, Role

class Position(String):
    pass

class Employment(Relation):
    flags = TypeFlags(type_name="employment")
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

# Get relations by attribute filter
engineers = employment_manager.get(position="Engineer")

# Get relations by role player filter
alice_jobs = employment_manager.get(employee=alice)
```

### Type Safety

EntityManager and RelationManager are generic classes that preserve type information:

```python
class EntityManager[E: Entity]:
    def insert(self, entity: E) -> E:
        ...
    def get(self, **filters) -> list[E]:
        ...
    def filter(self, **filters) -> EntityQuery[E]:
        ...

# Type checkers understand the returned type
alice = Person(name=Name("Alice"), age=Age(30))
person_manager.insert(alice)  # ✓ Type-safe
persons: list[Person] = person_manager.all()  # ✓ Type-safe
```

## Advanced Query API with Expressions

TypeBridge provides a fully type-safe expression-based query API for advanced filtering, aggregations, and boolean logic. All expressions are validated at compile-time and execute efficiently on the database.

### Field References

Access entity fields at the class level to get type-safe field references:

```python
# Class-level access returns FieldRef for query building
Person.age      # Returns NumericFieldRef[Age]
Person.name     # Returns StringFieldRef[Name]
Person.email    # Returns StringFieldRef[Email]

# Instance-level access still returns attribute values
person.age      # Returns Age instance
person.name     # Returns Name instance
```

### Value Comparisons

Filter entities using type-safe comparison operators:

```python
# Greater than
older = manager.filter(Person.age.gt(Age(30)))

# Less than or equal
young = manager.filter(Person.age.lte(Age(25)))

# Range queries (AND multiple comparisons)
adults = manager.filter(
    Person.age.gte(Age(18)),
    Person.age.lt(Age(65))
)

# Equality and inequality
exact = manager.filter(Person.age.eq(Age(35)))
not_thirty = manager.filter(Person.age.neq(Age(30)))

# All methods: .gt(), .lt(), .gte(), .lte(), .eq(), .neq()
```

### String Operations

Perform text searches with type-safe string methods:

```python
# Contains substring
gmail = manager.filter(Person.email.contains(Email("@gmail.com")))

# Regex pattern matching
a_names = manager.filter(Person.name.like(Name("^A.*")))

# Regex (alias for like)
pattern = manager.filter(Person.city.regex(City("New.*")))

# All methods: .contains(), .like(), .regex()
```

### Boolean Logic

Compose complex queries with AND, OR, NOT:

```python
# OR: young OR senior
young_or_old = manager.filter(
    Person.age.lt(Age(25)).or_(Person.age.gt(Age(60)))
)

# AND: explicit composition
senior_engineers = manager.filter(
    Person.department.eq(Department("Engineering")).and_(
        Person.job_title.contains(JobTitle("Senior"))
    )
)

# NOT: negation
non_sales = manager.filter(
    Person.department.eq(Department("Sales")).not_()
)

# Complex: (age > 40 AND salary > 100k) OR performance > 90
top_talent = manager.filter(
    Person.age.gt(Age(40)).and_(
        Person.salary.gt(Salary(100000.0))
    ).or_(
        Person.performance.gt(Performance(90.0))
    )
)

# Multiple filters are implicitly AND'ed
result = manager.filter(
    Person.age.gt(Age(18)),      # AND
    Person.age.lt(Age(65)),      # AND
    Person.status.eq(Status("active"))
).execute()
```

### Database-Side Aggregations

Execute efficient aggregations on the database (not in Python):

```python
# Single aggregation
result = manager.filter().aggregate(Person.age.avg())
avg_age = result['avg_age']

# Multiple aggregations
stats = manager.filter(
    Person.department.eq(Department("Engineering"))
).aggregate(
    Person.age.avg(),
    Person.salary.avg(),
    Person.salary.sum(),
    Person.salary.max(),
    Person.salary.min()
)

avg_age = stats['avg_age']
avg_salary = stats['avg_salary']
total_payroll = stats['sum_salary']
max_salary = stats['max_salary']
min_salary = stats['min_salary']

# Available aggregation methods:
# - .avg()    - Average value
# - .sum()    - Sum of values
# - .max()    - Maximum value
# - .min()    - Minimum value
# - .median() - Median value
# - .std()    - Standard deviation
```

### Group-By Queries

Group entities by field values and compute per-group aggregations:

```python
# Group by single field
dept_stats = manager.group_by(Person.department).aggregate(
    Person.age.avg(),
    Person.salary.avg()
)

# Results: dict mapping group values to stats
for dept, stats in dept_stats.items():
    print(f"{dept}: avg age={stats['avg_age']}, avg salary={stats['avg_salary']}")

# Example output:
# Engineering: avg age=32.5, avg salary=95000.0
# Sales: avg age=29.3, avg salary=75000.0
# Marketing: avg age=28.1, avg salary=68000.0

# Group by multiple fields
title_dept_stats = manager.group_by(
    Person.job_title,
    Person.department
).aggregate(Person.salary.avg())

# Results: dict with tuple keys
for (title, dept), stats in title_dept_stats.items():
    print(f"{title} in {dept}: avg salary={stats['avg_salary']}")
```

### Combining Filters and Aggregations

Chain expression filters with aggregations:

```python
# Filter then aggregate
eng_stats = manager.filter(
    Person.department.eq(Department("Engineering")),
    Person.age.gt(Age(30))
).aggregate(
    Person.salary.avg(),
    Person.performance.avg()
)

# Filter, group, then aggregate
senior_stats_by_dept = manager.filter(
    Person.job_title.contains(JobTitle("Senior"))
).group_by(Person.department).aggregate(
    Person.salary.avg(),
    Person.age.avg()
)
```

### Backward Compatibility

The expression API coexists with the dictionary filter API:

```python
# Old style (exact match only) - still works
persons = manager.filter(age=30, status="active").execute()

# New style (advanced filtering)
persons = manager.filter(
    Person.age.gt(Age(30)),
    Person.status.eq(Status("active"))
).execute()

# Mixed style (both together)
persons = manager.filter(
    Person.age.gt(Age(25)),  # Expression
    status="active"           # Dict filter
).execute()
```

### Query Chaining and Pagination

All query methods support chaining:

```python
# Build query step by step
query = manager.filter(Person.age.gt(Age(25)))
query = query.filter(Person.department.eq(Department("Engineering")))
results = query.limit(10).offset(20).execute()

# Or chain in one expression
results = manager.filter(
    Person.age.gt(Age(25)),
    Person.department.eq(Department("Engineering"))
).limit(10).offset(20).execute()

# Get first matching entity
first = manager.filter(Person.age.gt(Age(30))).first()  # Returns Person | None

# Count without fetching all
count = manager.filter(Person.department.eq(Department("Sales"))).count()
```

### Type Safety Guarantees

All expression operations are fully type-safe:

```python
# ✓ Type-safe: Age field has numeric methods
Person.age.gt(Age(30))
Person.age.avg()

# ✓ Type-safe: Name field has string methods
Person.name.contains(Name("Alice"))
Person.name.like(Name("A.*"))

# ✗ Type error: String field doesn't have numeric methods
Person.name.avg()  # Caught by type checker!

# ✗ Type error: Numeric field doesn't have string methods
Person.age.contains(Age(30))  # Caught by type checker!

# ✓ Type-safe: Expression returns correct type
expr: ComparisonExpr[Age] = Person.age.gt(Age(30))
str_expr: StringExpr[Name] = Person.name.contains(Name("Alice"))
agg_expr: AggregateExpr[Age] = Person.age.avg()
```

### Complete Example

```python
from type_bridge import Database, Entity, TypeFlags
from type_bridge.attribute import String, Integer, Double
from type_bridge.attribute.flags import Flag, Key

class Email(String):
    pass

class Age(Integer):
    pass

class Salary(Double):
    pass

class Department(String):
    pass

class Employee(Entity):
    flags = TypeFlags(type_name="employee")
    email: Email = Flag(Key)
    age: Age
    salary: Salary
    department: Department

# Connect
db = Database(address="localhost:1729", database="company")
db.connect()
manager = Employee.manager(db)

# Complex query: senior engineers with high salary
senior_engineers = manager.filter(
    Employee.department.eq(Department("Engineering")),
    Employee.age.gt(Age(35)),
    Employee.salary.gte(Salary(120000.0))
).execute()

# Aggregation: average salary by department
dept_salaries = manager.group_by(Employee.department).aggregate(
    Employee.salary.avg(),
    Employee.age.avg()
)

for dept, stats in dept_salaries.items():
    print(f"{dept}: ${stats['avg_salary']:,.2f}, {stats['avg_age']:.1f} years")

# Boolean logic: young high performers OR experienced employees
talent = manager.filter(
    Employee.age.lt(Age(30)).and_(
        Employee.salary.gt(Salary(80000.0))
    ).or_(
        Employee.age.gte(Age(45))
    )
).execute()
```

See `examples/advanced/query_expressions.py` for comprehensive real-world examples.

## Schema Management and Conflict Detection

TypeBridge provides comprehensive schema management with automatic conflict detection.

### SchemaManager

The SchemaManager handles schema registration, generation, and synchronization:

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

### Conflict Detection

SchemaManager automatically detects schema conflicts and prevents data loss:

```python
from type_bridge.schema import SchemaConflictError

# First time - creates schema
schema_manager.sync_schema()  # ✓ Success

# Modify your models (e.g., remove an attribute, change cardinality)
class Person(Entity):
    flags = TypeFlags(type_name="person")
    name: Name = Flag(Key)
    # age attribute removed!

# Try to sync again
try:
    schema_manager.sync_schema()  # ✗ Raises SchemaConflictError
except SchemaConflictError as e:
    print(e.diff.summary())  # Shows what changed
    # Output:
    # Schema Differences:
    # Modified Entities:
    #   person:
    #     - Removed attributes: age

# Force recreate (⚠️ DATA LOSS)
schema_manager.sync_schema(force=True)
```

### Schema Comparison

Compare schemas to understand changes:

```python
from type_bridge.schema import SchemaInfo

# Collect current schema
old_schema = schema_manager.collect_schema_info()

# Make changes to your models
class Person(Entity):
    flags = TypeFlags(type_name="person")
    name: Name = Flag(Key)
    age: Age | None
    email: Email = Flag(Unique)  # New attribute!

# Collect new schema
new_schema = schema_manager.collect_schema_info()

# Compare
diff = old_schema.compare(new_schema)
print(diff.summary())
# Output:
# Schema Differences:
# Modified Entities:
#   person:
#     + Added attributes: email (unique)
```

### Schema Diff Details

The SchemaDiff class tracks granular changes:

- **Entity changes**: Added, removed, modified entities
- **Relation changes**: Added, removed, modified relations
- **Attribute changes**: Added, removed attributes
- **Ownership changes**: Attributes added/removed from entities
- **Flag changes**: Cardinality, key, unique annotation changes
- **Role changes**: Roles added/removed from relations

Example usage:

```python
if diff.has_changes():
    print(f"Added entities: {diff.added_entities}")
    print(f"Removed attributes: {diff.removed_attributes}")

    for entity_type, changes in diff.modified_entities.items():
        print(f"{entity_type}:")
        print(f"  Added attributes: {changes.added_attributes}")
        print(f"  Removed attributes: {changes.removed_attributes}")
        for attr, flag_change in changes.modified_attributes.items():
            print(f"  Modified: {attr} - {flag_change}")
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

# Apply all migrations
migration_manager.apply_migrations()
```

## Dependencies

The project requires:
- `typedb-driver==3.5.5`: Official Python driver for TypeDB connectivity
- `pydantic>=2.0`: For validation and type coercion
- Uses Python's built-in type hints and dataclass-like patterns

## TypeDB Driver 3.5.5 API Notes

The driver API for version 3.5.5 differs from earlier versions:

1. **No separate sessions**: Transactions are created directly on the driver
   ```python
   driver.transaction(database_name, TransactionType.READ)
   ```

2. **Single query method**: `transaction.query(query_string)` returns `Promise[QueryAnswer]`
   - Must call `.resolve()` to get results
   - Works for all query types (define, insert, match, fetch, delete)

3. **TransactionType enum**: `READ`, `WRITE`, `SCHEMA`

4. **Authentication**: Requires `Credentials(username, password)` even for local development

## TypeDB 3.x Syntax and Behavior Changes

TypeDB 3.x introduced important syntax and behavior changes that affect query generation:

### Query Syntax Changes

1. **Type queries use `isa` instead of `sub`**:
   ```typeql
   # ✅ TypeDB 3.x (correct)
   match $x isa person;

   # ❌ TypeDB 2.x (deprecated)
   match $x sub person;
   ```

2. **Cannot query root types directly**:
   - Cannot match on `entity`, `relation`, or `attribute` root types
   - Must query specific subtypes (e.g., `person`, `employment`)
   ```typeql
   # ❌ This will fail in TypeDB 3.x
   match $x isa entity;

   # ✅ Query specific entity types
   match $x isa person;
   ```

3. **Pagination requires explicit sorting**:
   - `offset` relies on consistent sort order
   - Always include `sort` clause when using `offset`
   ```typeql
   # ✅ Correct pagination
   match $p isa person;
   sort $p asc;
   offset 10;
   limit 5;

   # ⚠️ Unpredictable results without sort
   match $p isa person;
   offset 10;
   limit 5;
   ```

4. **Clause ordering matters**:
   - `offset` must come before `limit`
   ```typeql
   # ✅ Correct order
   match $p isa person;
   offset 10;
   limit 5;

   # ❌ Wrong order (syntax error)
   match $p isa person;
   limit 5;
   offset 10;
   ```

### Implementation Considerations

When generating TypeQL queries:
- Use `isa` for type matching in all queries
- Avoid querying root types (`entity`, `relation`, `attribute`)
- Always include explicit `sort` clause when using `offset` for pagination
- Ensure clause order: `match` → `sort` → `offset` → `limit`

## Code Quality Standards

The project maintains high code quality standards with zero tolerance for technical debt:

### Linting and Type Checking

All code must pass these checks without errors or warnings:

```bash
# Ruff - Python linter and formatter (must pass with 0 errors)
uv run ruff check .          # Check for style issues
uv run ruff format .         # Auto-format code

# Pyright - Static type checker (must pass with 0 errors, 0 warnings)
uv run pyright type_bridge/  # Check core library
uv run pyright examples/     # Check examples
uv run pyright tests/        # Check tests (note: intentional validation errors are OK)
```

### Code Quality Requirements

1. **No linter suppressions**: Do not use `# noqa`, `# type: ignore`, or similar comments
   - Exception: Tests intentionally checking validation failures may show type warnings

2. **Modern Python syntax**:
   - Use PEP 604 (`X | Y`) instead of `Union[X, Y]`
   - Use PEP 695 type parameters (`class Foo[T]:`) when possible
   - Use `X | None` instead of `Optional[X]`

3. **Consistent ModelAttrInfo usage**:
   - Always use `attr_info.typ` and `attr_info.flags`
   - Never use dict-style access like `attr_info["type"]`

4. **Import organization**: Imports must be sorted and organized (ruff handles this automatically)

5. **Temporary files and reports**: When creating temporary test scripts, reports, or analysis files during development/debugging:
   - Create them in the `tmp/` directory (already in .gitignore)
   - Do NOT create temporary files in the project root
   - Examples: test scripts, debug reports, analysis documents, verification files
   - Exception: Permanent documentation that should be committed belongs in the root or docs/

### Testing Requirements

All tests must pass:
```bash
uv run python -m pytest tests/ -v  # All 38 tests must pass
```

When adding new features:
- Add corresponding tests in `tests/`
- Ensure examples in `examples/` demonstrate the feature
- Update CLAUDE.md with usage guidelines
- Run all quality checks before committing

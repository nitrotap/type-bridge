# Testing Guide

TypeBridge uses a comprehensive two-tier testing approach with **100% test pass rate (417/417 tests)**.

## Table of Contents

- [Testing Strategy](#testing-strategy)
- [Unit Tests](#unit-tests)
- [Integration Tests](#integration-tests)
- [Test Execution Patterns](#test-execution-patterns)
- [Writing Tests](#writing-tests)

## Testing Strategy

TypeBridge employs a two-tier testing approach that balances speed, isolation, and real-world validation:

### Unit Tests (Default)
- **Fast**: Run in ~0.3 seconds without external dependencies
- **Isolated**: Test individual components in isolation
- **No TypeDB required**: Use mocks and in-memory validation
- **Run by default**: `pytest` runs unit tests only
- **284 tests total**: Organized by functionality

### Integration Tests
- **Sequential**: Use `@pytest.mark.order()` for predictable execution order
- **Real database**: Require running TypeDB 3.x server
- **End-to-end**: Test complete workflows from schema to queries
- **Explicit execution**: Must use `pytest -m integration`
- **133 tests total**: Full CRUD, schema, and query coverage

## Unit Tests

### Overview

Unit tests are located in `tests/unit/` with organized subdirectories:

```
tests/unit/
├── core/                     # Core functionality tests
│   ├── test_basic.py         # Basic entity/relation/attribute API
│   ├── test_inheritance.py   # Inheritance and type hierarchies
│   └── test_pydantic.py      # Pydantic integration and validation
├── attributes/               # Attribute type tests
│   ├── test_boolean.py       # Boolean attribute type
│   ├── test_date.py          # Date attribute type
│   ├── test_datetime_tz.py   # DateTimeTZ attribute type
│   ├── test_decimal.py       # Decimal attribute type
│   ├── test_double.py        # Double attribute type
│   ├── test_duration.py      # Duration attribute type (ISO 8601)
│   ├── test_formatting.py    # Mixed attribute formatting
│   ├── test_integer.py       # Integer attribute type
│   └── test_string.py        # String attribute type
├── flags/                    # Flag system tests
│   ├── test_base_flag.py     # Base flag for schema exclusion
│   ├── test_cardinality.py   # Card API for cardinality constraints
│   ├── test_typename_case.py # Entity/Relation type name formatting
│   └── test_attribute_typename_case.py # Attribute name formatting
├── expressions/              # Query expression API tests
│   ├── test_field_refs.py    # Field reference creation
│   ├── test_comparisons.py   # Comparison operators
│   ├── test_string_ops.py    # String operations
│   └── test_aggregations.py  # Aggregation functions
├── validation/               # Validation tests
│   ├── test_keywords.py      # Reserved word validation
│   └── test_schema_validation.py # Duplicate attribute detection
└── type-check-except/        # Intentionally excluded from type checking
    └── test_validation_errors.py # Tests for validation failures
```

### Running Unit Tests

```bash
# Run all unit tests (default)
uv run pytest                              # All 284 unit tests (~0.3s)
uv run pytest -v                           # With verbose output

# Run specific test category
uv run pytest tests/unit/core/             # Core tests
uv run pytest tests/unit/attributes/       # Attribute tests
uv run pytest tests/unit/flags/            # Flag tests
uv run pytest tests/unit/expressions/      # Expression tests
uv run pytest tests/unit/validation/       # Validation tests

# Run specific test file
uv run pytest tests/unit/attributes/test_integer.py -v
uv run pytest tests/unit/attributes/test_string.py -v

# Run specific test function
uv run pytest tests/unit/core/test_basic.py::test_entity_creation -v

# With coverage report
uv run pytest --cov=type_bridge --cov-report=html
```

### Unit Test Coverage

**Core API:**
- Entity/Relation creation
- Schema generation
- Inheritance and type hierarchies

**Attribute types (all 9 types):**
- Boolean, Date, DateTime, DateTimeTZ, Decimal, Double, Duration, Integer, String
- Value validation and type coercion
- Mixed formatting tests for query generation

**Flag system:**
- Base flags for schema exclusion
- Cardinality constraints (Card API)
- Type name formatting (snake_case, kebab-case, etc.)

**Expression API:**
- Field references and access
- Comparison operators (gt, lt, eq, etc.)
- String operations (contains, like, regex)
- Aggregation functions (avg, sum, min, max)

**Validation:**
- Pydantic integration
- Keyword and reserved word validation
- Type checking
- Schema validation (duplicate attribute type detection)

## Integration Tests

### Overview

Integration tests are located in `tests/integration/` with organized subdirectories:

```
tests/integration/
├── crud/                     # CRUD operations organized by type
│   ├── entities/             # Entity CRUD operations
│   │   ├── test_insert.py    # Entity insertion
│   │   ├── test_fetch.py     # Entity fetching
│   │   ├── test_update.py    # Entity updates
│   │   └── test_delete.py    # Entity deletion
│   ├── relations/            # Relation CRUD operations
│   │   ├── test_insert.py    # Relation insertion
│   │   ├── test_fetch.py     # Relation fetching
│   │   ├── test_abstract_roles.py # Abstract entity types in roles
│   │   └── test_delete.py    # Relation deletion
│   ├── attributes/           # Attribute type operations
│   │   ├── test_all_types.py # All 9 attribute types
│   │   ├── test_multi_value.py # Multi-value attributes
│   │   └── test_conversions.py # DateTime/DateTimeTZ conversions
│   └── interop/              # Cross-type operations
│       ├── test_mixed_queries.py # Complex mixed queries
│       └── test_role_players.py  # Role player operations
├── queries/                  # Query builder and expression tests
│   ├── test_expressions.py   # Query expressions
│   ├── test_aggregations.py  # Database-side aggregations
│   ├── test_pagination.py    # Limit, offset, sort
│   └── test_filtering.py     # Filter operations
└── schema/                   # Schema operations
    ├── test_creation.py      # Schema creation
    ├── test_conflict.py      # Conflict detection
    ├── test_migration.py     # Schema migrations
    └── test_inheritance.py   # Inheritance hierarchies
```

### Running Integration Tests

Integration tests require a running TypeDB 3.x server.

**Option 1: Use Docker (Recommended - Automatic)**

```bash
# Run integration tests with Docker (automatic setup)
./test-integration.sh                     # All 133 integration tests
./test-integration.sh -v                  # With verbose output

# Docker is automatically:
# - Started before tests
# - Stopped after tests (even on failure)
```

**Option 2: Use Existing TypeDB Server**

```bash
# 1. Start TypeDB 3.x server manually
typedb server

# 2. Run integration tests (skip Docker)
USE_DOCKER=false uv run pytest -m integration
USE_DOCKER=false uv run pytest -m integration -v  # Verbose
```

**Run specific integration test categories:**

```bash
# Entity CRUD tests
uv run pytest tests/integration/crud/entities/ -v

# Relation CRUD tests
uv run pytest tests/integration/crud/relations/ -v

# Query expression tests
uv run pytest tests/integration/queries/ -v

# Schema operation tests
uv run pytest tests/integration/schema/ -v

# Specific test file
uv run pytest tests/integration/schema/test_conflict.py -v
uv run pytest tests/integration/queries/test_pagination.py -v
uv run pytest tests/integration/queries/test_expressions.py -v
uv run pytest tests/integration/crud/relations/test_abstract_roles.py -v
```

### Integration Test Coverage

**Schema operations:**
- Schema creation and synchronization
- Conflict detection
- Inheritance hierarchies
- Schema migrations

**CRUD operations for all 9 attribute types:**
- Insert (single and bulk)
- Fetch (get, filter, all, first)
- Update (single-value and multi-value attributes)
- Delete

**Complex queries:**
- Query expressions (comparisons, string operations)
- Boolean logic (AND, OR, NOT)
- Aggregations (avg, sum, min, max, median, std)
- Group-by queries
- Pagination (limit, offset, sort)
- Filtering with role players

**Relations:**
- Abstract entity types in role definitions
- Role player queries
- Relation inheritance

**TypeDB 3.x specific features:**
- Proper `isa` syntax (not `sub`)
- Offset before limit clause ordering
- Explicit sorting for pagination

**Transaction management:**
- READ, WRITE, SCHEMA transaction types
- Proper transaction lifecycle
- Database creation and cleanup

### Docker Setup for Integration Tests

**Requirements:**
- Docker and Docker Compose installed
- Port 1729 available (TypeDB server)

**Configuration:**

The project includes `docker-compose.yml` for TypeDB 3.5.5:

```yaml
services:
  typedb:
    image: vaticle/typedb:3.5.5
    ports:
      - "1729:1729"
    volumes:
      - typedb-data:/opt/typedb/server/data

volumes:
  typedb-data:
```

**Manual Docker control:**

```bash
# Start TypeDB container
docker compose up -d

# View TypeDB logs
docker compose logs typedb

# Stop TypeDB container
docker compose down

# Remove volumes (clean slate)
docker compose down -v
```

## Test Execution Patterns

### Running All Tests

```bash
# Unit tests only (default, fast)
uv run pytest                              # All 284 unit tests

# Integration tests only (requires TypeDB)
./test-integration.sh                     # All 133 integration tests with Docker

# All tests (unit + integration)
uv run pytest -m ""                       # All 417 tests
./test.sh                                 # Full test suite with detailed output
```

### Selective Test Execution

```bash
# By marker
uv run pytest -m unit           # Only unit tests
uv run pytest -m integration    # Only integration tests

# By keyword
uv run pytest -k "test_entity"  # All tests matching "test_entity"
uv run pytest -k "crud"         # All CRUD-related tests

# By path
uv run pytest tests/unit/                    # All unit tests
uv run pytest tests/integration/crud/        # All CRUD integration tests

# Specific test
uv run pytest tests/unit/core/test_basic.py::test_entity_creation
```

### Test Output Options

```bash
# Verbose output
uv run pytest -v

# Show print statements
uv run pytest -s

# Show captured logs
uv run pytest --log-cli-level=DEBUG

# Stop on first failure
uv run pytest -x

# Run last failed tests
uv run pytest --lf

# Run failed tests first
uv run pytest --ff
```

### Parallel Execution

```bash
# Install pytest-xdist
uv pip install pytest-xdist

# Run tests in parallel (unit tests only)
uv run pytest -n auto  # Auto-detect CPU count
uv run pytest -n 4     # Use 4 workers

# Note: Integration tests use @pytest.mark.order() and should run sequentially
```

## Writing Tests

### Unit Test Template

```python
"""Unit tests for [feature name]."""

import pytest
from type_bridge import Entity, TypeFlags, String, Flag, Key


class Name(String):
    pass


class TestFeature:
    """Test [feature description]."""

    def test_basic_functionality(self):
        """Test basic functionality."""
        # Arrange
        class Person(Entity):
            flags = TypeFlags(type_name="person")
            name: Name = Flag(Key)

        # Act
        person = Person(name=Name("Alice"))

        # Assert
        assert person.name.value == "Alice"
        assert Person.get_type_name() == "person"

    def test_edge_case(self):
        """Test edge case behavior."""
        # Test implementation
        pass

    def test_error_handling(self):
        """Test error handling."""
        with pytest.raises(ValueError, match="Expected error message"):
            # Code that should raise ValueError
            pass
```

### Integration Test Template

```python
"""Integration tests for [feature name]."""

import pytest
from type_bridge import Database, Entity, TypeFlags, String, Flag, Key, SchemaManager


class Name(String):
    pass


class Person(Entity):
    flags = TypeFlags(type_name="person")
    name: Name = Flag(Key)


@pytest.mark.integration
@pytest.mark.order(1)
class TestFeatureIntegration:
    """Integration tests for [feature description]."""

    @pytest.fixture(autouse=True)
    def setup(self, db: Database):
        """Setup schema for tests."""
        schema_manager = SchemaManager(db)
        schema_manager.register(Person)
        schema_manager.sync_schema()

    def test_end_to_end_workflow(self, db: Database):
        """Test complete workflow with database."""
        # Create manager
        manager = Person.manager(db)

        # Insert
        alice = Person(name=Name("Alice"))
        manager.insert(alice)

        # Fetch
        persons = manager.all()
        assert len(persons) == 1
        assert persons[0].name.value == "Alice"

        # Update
        persons[0].name = Name("Alice Smith")
        manager.update(persons[0])

        # Verify
        updated = manager.get(name="Alice Smith")
        assert len(updated) == 1
```

### Test Best Practices

1. **Use descriptive test names**:
   ```python
   # ✅ Good
   def test_entity_with_optional_field_allows_none():
       pass

   # ❌ Bad
   def test_entity():
       pass
   ```

2. **Follow Arrange-Act-Assert pattern**:
   ```python
   def test_something():
       # Arrange: Set up test data
       person = Person(name=Name("Alice"))

       # Act: Perform the operation
       result = person.to_schema_definition()

       # Assert: Verify the result
       assert "person" in result
   ```

3. **One assertion per test** (when possible):
   ```python
   # ✅ Good
   def test_entity_type_name():
       assert Person.get_type_name() == "person"

   def test_entity_has_attributes():
       assert len(Person.get_owned_attributes()) > 0

   # ❌ Less ideal
   def test_entity():
       assert Person.get_type_name() == "person"
       assert len(Person.get_owned_attributes()) > 0
   ```

4. **Use fixtures for common setup**:
   ```python
   @pytest.fixture
   def person():
       return Person(name=Name("Alice"))

   def test_with_fixture(person):
       assert person.name.value == "Alice"
   ```

5. **Test edge cases and error conditions**:
   ```python
   def test_empty_string():
       pass

   def test_none_value():
       pass

   def test_invalid_type_raises_error():
       with pytest.raises(TypeError):
           # Invalid operation
           pass
   ```

### Test Organization

- **One test file per module**: `test_<module_name>.py`
- **Group related tests in classes**: Use `TestClassName` for grouping
- **Use markers**: `@pytest.mark.unit`, `@pytest.mark.integration`
- **Order integration tests**: Use `@pytest.mark.order(N)` for sequential tests

### Running Tests During Development

Quick test commands while developing:

```bash
# Test current file
uv run pytest tests/unit/core/test_basic.py -v

# Test with auto-rerun on file changes (requires pytest-watch)
uv run ptw tests/unit/

# Test with coverage
uv run pytest --cov=type_bridge tests/unit/

# Generate coverage HTML report
uv run pytest --cov=type_bridge --cov-report=html tests/unit/
open htmlcov/index.html  # View coverage report
```

---

For development setup, see [DEVELOPMENT.md](DEVELOPMENT.md).

For TypeDB-specific testing considerations, see [TYPEDB.md](TYPEDB.md).

# Integration Tests

This directory contains integration tests that require a running TypeDB instance. These tests verify end-to-end functionality with a real database.

## Structure

```
integration/
├── schema/                  # Schema management tests (7 tests)
│   ├── test_creation.py     # Schema creation and safe updates
│   ├── test_relations.py    # Schema with relations and roles
│   ├── test_conflict.py     # Conflict detection
│   ├── test_cardinality.py  # Cardinality constraints
│   ├── test_attributes.py   # Unique and key attributes
│   ├── test_inheritance.py  # Entity inheritance
│   └── test_types.py        # All 9 attribute types in schema
├── crud/                    # CRUD operation tests
│   ├── entities/           # Entity CRUD tests (12 tests)
│   │   ├── test_insert.py  # Insert operations
│   │   ├── test_fetch.py   # Fetch operations
│   │   ├── test_update.py  # Update operations
│   │   └── test_delete.py  # Delete operations
│   ├── relations/          # Relation CRUD tests (6 tests)
│   │   ├── test_insert.py  # Relation insert
│   │   └── test_fetch.py   # Relation fetch by role/attribute
│   ├── attributes/         # Attribute type CRUD tests (54 tests)
│   │   ├── test_boolean.py    # Boolean CRUD (4 tests)
│   │   ├── test_integer.py    # Integer CRUD (4 tests)
│   │   ├── test_string.py     # String CRUD (4 tests)
│   │   ├── test_double.py     # Double CRUD (4 tests)
│   │   ├── test_date.py       # Date CRUD (4 tests)
│   │   ├── test_datetime.py   # DateTime CRUD (4 tests)
│   │   ├── test_datetimetz.py # DateTimeTZ CRUD (4 tests)
│   │   ├── test_decimal.py    # Decimal CRUD (4 tests)
│   │   ├── test_duration.py   # Duration CRUD (4 tests)
│   │   ├── test_multi_value.py # Multi-value attributes (9 tests)
│   │   └── test_multivalue_escaping.py # String escaping edge cases (9 tests)
│   └── interop/            # Type interoperability tests (23 tests)
│       ├── test_mixed_entity.py  # Mixed type entities (6 tests)
│       ├── test_mixed_queries.py # Mixed type queries (8 tests)
│       └── test_type_combinations.py # Real-world combos (9 tests)
└── queries/                # Query building tests (8 tests)
    ├── test_match.py       # Simple match queries
    ├── test_filters.py     # Filtering with multiple types
    ├── test_pagination.py  # Limit, offset, first, count
    └── test_role_players.py # Relation role player queries
```

## Test Count Summary

| Category | Files | Tests | Description |
|----------|-------|-------|-------------|
| **Schema** | 7 | 16 | Schema operations, conflicts, inheritance, all types |
| **Entity CRUD** | 4 | 12 | Insert, fetch, update, delete operations |
| **Relation CRUD** | 2 | 6 | Relation insert and fetch operations |
| **Attribute CRUD** | 11 | 54 | CRUD for all 9 types + multi-value + escaping |
| **Interoperability** | 3 | 23 | Mixed types, queries, real-world combinations |
| **Queries** | 4 | 8 | Match, filters, pagination, role players |
| **Total** | **31** | **119** | Complete integration test coverage |

## Running Integration Tests

**Prerequisites:**
- TypeDB server running on `localhost:1729`
- Test database will be created/destroyed automatically

```bash
# Run all integration tests (requires TypeDB)
uv run pytest -m integration -v

# Run specific category
uv run pytest tests/integration/schema/ -v
uv run pytest tests/integration/crud/entities/ -v
uv run pytest tests/integration/crud/attributes/ -v
uv run pytest tests/integration/crud/interop/ -v
uv run pytest tests/integration/queries/ -v

# Run specific test file
uv run pytest tests/integration/schema/test_creation.py -v
uv run pytest tests/integration/crud/attributes/test_boolean.py -v

# Run tests in order (uses pytest-order)
uv run pytest -m integration -v --order-scope=session
```

## Test Execution Order

Tests are executed sequentially using `@pytest.mark.order()` to ensure:
1. **Schema tests** run first (orders 1-8)
2. **Entity CRUD** tests follow (orders 10-19)
3. **Relation CRUD** tests (orders 20-22)
4. **Attribute CRUD** tests (orders 23-67)
5. **Interoperability** tests (orders 68-90)
6. **Query** tests run last (orders 91-98)

This ordering ensures schema is created before CRUD operations and data exists before queries.

## Test Coverage by Type

### Complete Type Coverage

All 9 TypeDB attribute types are tested across multiple dimensions:

| Type | Schema | Insert | Fetch | Update | Delete | Multi-value | Interop |
|------|--------|--------|-------|--------|--------|-------------|---------|
| **Boolean** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Integer** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **String** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Double** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Date** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **DateTime** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **DateTimeTZ** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Decimal** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Duration** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

**Coverage: 100%** (63/63 type operations)

### Real-World Type Combinations

The interoperability tests verify common real-world entity patterns:

1. **Person** - String + Integer + Date (user profile)
2. **Product** - String + Decimal + Integer + Boolean (e-commerce)
3. **Event** - String + DateTime + Duration (scheduling)
4. **Measurement** - String + Double + DateTimeTZ (IoT sensors)
5. **Account** - String + Boolean + DateTime (user accounts)
6. **Order** - Integer + Decimal + Date + String (orders)
7. **Session** - String + DateTime + DateTimeTZ + Duration (sessions)
8. **Score** - String + Integer + Double + Boolean (gaming/scoring)
9. **Audit** - All 9 types (comprehensive audit log)

## Fixtures

Integration tests use the following fixtures (defined in `conftest.py`):

- **`clean_db`**: Fresh database for each test (isolated)
- **`db_with_schema`**: Database with Person/Company/Employment schema pre-loaded

## Test Guidelines

Integration tests should:
- **Use real TypeDB**: Connect to actual TypeDB instance
- **Be isolated**: Each test gets a clean database via fixtures
- **Run sequentially**: Use `@pytest.mark.order()` for dependencies
- **Test end-to-end**: Full workflow from schema → insert → fetch → update → delete
- **Verify all types**: Ensure all 9 attribute types work correctly
- **Test interoperability**: Verify types work together in real scenarios

## Adding New Integration Tests

When adding new integration tests:

1. **Choose the right directory**:
   - Schema changes → `schema/`
   - CRUD operations → `crud/entities/` or `crud/relations/`
   - New attribute type → `crud/attributes/`
   - Type combinations → `crud/interop/`
   - Query features → `queries/`

2. **Follow naming conventions**:
   - Files: `test_*.py`
   - Functions: `test_<what>_<when>_<expected>`
   - Use descriptive test names

3. **Use appropriate fixtures**:
   - `clean_db` for isolated tests
   - `db_with_schema` for tests needing existing schema

4. **Add execution order**:
   - Use `@pytest.mark.order(N)` where N is the next available number
   - Group related tests with consecutive numbers

5. **Test all CRUD operations**:
   - For new types: insert, fetch, update, delete
   - For new features: happy path + edge cases

6. **Run tests to verify**:
   ```bash
   uv run pytest tests/integration/ -v
   ```

## TypeDB Configuration

Tests expect TypeDB running at:
- **Address**: `localhost:1729`
- **Database**: Auto-created (e.g., `test_db_<timestamp>`)
- **Credentials**: Default credentials for local development
- **Cleanup**: Databases are deleted after tests complete

## Debugging Failed Tests

If integration tests fail:

1. **Check TypeDB is running**:
   ```bash
   typedb server status
   ```

2. **Check connection**:
   ```bash
   typedb console --server=localhost:1729
   ```

3. **Run single test with verbose output**:
   ```bash
   uv run pytest tests/integration/schema/test_creation.py::test_schema_creation_and_sync -vv
   ```

4. **Check test execution order**:
   ```bash
   uv run pytest -m integration -v --collect-only
   ```

5. **Inspect database after failure**:
   - Comment out database cleanup in `conftest.py`
   - Connect with TypeDB Console to inspect schema/data

## Performance

Integration tests are slower than unit tests due to:
- Real database connections
- Schema creation/deletion
- Network I/O
- Transaction commits

**Typical execution time**: 30-60 seconds for all 119 tests

Use unit tests for fast iteration, integration tests for comprehensive validation.

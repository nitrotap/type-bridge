# Integration Tests

This directory contains integration tests that verify end-to-end workflows with a real TypeDB instance.

## Requirements

- **TypeDB Server**: You must have TypeDB 3.x running before executing integration tests
- **Connection**: Tests connect to `localhost:1729` by default
- **Database**: Tests use a temporary database (`type_bridge_test`) that is created and cleaned up

## Running Integration Tests

### Install dependencies (including pytest-order)
```bash
uv sync --extra dev
```

### Start TypeDB Server
```bash
# Download and start TypeDB 3.x
typedb server
```

### Run integration tests only
```bash
# Run all integration tests
uv run pytest -m integration

# Run with verbose output
uv run pytest -m integration -v

# Run specific integration test file
uv run pytest tests/integration/test_schema_operations.py -v
```

### Run all tests (unit + integration)
```bash
uv run pytest -m ""
```

### Run unit tests only (default)
```bash
uv run pytest
```

## Test Organization

Integration tests are organized by feature area:

- `test_schema_operations.py`: Schema creation, migration, conflict detection
- `test_crud_workflows.py`: Insert, fetch, update, delete end-to-end workflows
- `test_query_building.py`: Complex queries with real data

## Test Execution Order

Integration tests use `@pytest.mark.order()` to ensure proper sequential execution:

1. Schema setup tests run first
2. Data insertion tests run second
3. Query and retrieval tests run third
4. Update and deletion tests run last

This ensures tests have a predictable database state.

## Database Cleanup

The `conftest.py` fixture handles:
- Database creation before tests
- Database cleanup after tests
- Transaction management
- Connection lifecycle

Tests should use the `db` and `db_manager` fixtures provided by `conftest.py`.

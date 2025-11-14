# Changelog

All notable changes to TypeBridge will be documented in this file.

## [0.4.0] - 2025-11-15

### 🚀 New Features

#### Docker Integration for Testing
- **Automated Docker management for integration tests**
  - Added `docker-compose.yml` with TypeDB 3.5.5 server configuration
  - Created `test-integration.sh` script for automated Docker lifecycle management
  - Docker containers start/stop automatically with test fixtures
  - Location: `docker-compose.yml`, `test-integration.sh`, `tests/integration/conftest.py`
- **Optional Docker usage**: Set `USE_DOCKER=false` to use existing TypeDB server
- **Port configuration**: TypeDB server on port 1729

#### Schema Validation
- **Duplicate attribute type detection**
  - Prevents using the same attribute type for multiple fields in an entity/relation
  - Validates during schema generation to catch design errors early
  - Raises `SchemaValidationError` with detailed field information
  - Location: `type_bridge/schema/info.py`, `type_bridge/schema/exceptions.py`
- **Why it matters**: TypeDB stores ownership by attribute type, not by field name
  - Using `created: TimeStamp` and `modified: TimeStamp` creates a single ownership
  - This causes cardinality constraint violations at runtime
  - Solution: Use distinct types like `CreatedStamp` and `ModifiedStamp`

### 🧪 Testing

#### Test Infrastructure
- **Improved test organization**: 347 total tests (249 unit + 98 integration)
- **Docker-based integration tests**: Automatic container lifecycle management
- **Added duplicate attribute validation tests**: 6 new tests for schema validation
  - Location: `tests/unit/validation/test_duplicate_attributes.py`

### 📚 Documentation

- **Updated CLAUDE.md**:
  - Added Docker setup instructions for integration tests
  - Documented duplicate attribute type validation rules
  - Added schema validation best practices
  - Included examples of correct vs incorrect attribute usage
- **Updated test execution patterns**: Docker vs manual TypeDB server options

### 🔧 CI/CD

- **Updated GitHub Actions workflow**:
  - Integrated Docker Compose for automated integration testing
  - Added TypeDB 3.5.5 service container configuration
  - Location: `.github/workflows/` (multiple CI updates)

### 📦 Dependencies

- Added `docker-compose` support for development workflow
- No changes to runtime dependencies

### 🐛 Bug Fixes

- **Fixed test fixture ordering**: Improved integration test reliability with Docker
- **Enhanced error messages**: Schema validation errors now include field names

## [0.3.X] - 2025-01-14

### ✅ Full TypeDB 3.x Compatibility

**Major Achievement: 100% Test Pass Rate (341/341 tests)**

### Fixed

#### Query Pagination
- **Fixed TypeQL clause ordering**: offset must come BEFORE limit in TypeDB 3.x
  - Changed `limit X; offset Y;` → `offset Y; limit X;`
  - Location: `type_bridge/query.py:151-154`
- **Added automatic sorting for pagination**: TypeDB 3.x requires sorting for reliable offset results
  - Automatically finds and sorts by key attributes when using limit/offset
  - Falls back to required attributes if no key exists
  - Location: `type_bridge/crud.py:447-468`

#### Schema Conflict Detection
- **Updated to TypeDB 3.x syntax**: Changed from `sub` to `isa` for type queries
  - TypeDB 3.x uses `$e isa person` instead of `$e sub entity`
  - Fixed `has_existing_schema()` to properly detect existing types
  - Fixed `_type_exists()` to use correct TypeQL syntax
  - Location: `type_bridge/schema/manager.py:65-284`
- **Improved conflict detection**: Now properly raises SchemaConflictError when types exist

#### Type Safety
- **Fixed AttributeFlags attribute access**: Changed `cardinality_min` to `card_min`
  - Resolved pyright type checking error
  - Location: `type_bridge/crud.py:460`

### Testing

#### Test Results
- **Unit tests**: 243/243 passing (100%) - ~0.3s runtime
- **Integration tests**: 98/98 passing (100%) - ~18s runtime
- **Total**: 341/341 passing (100%)

#### Test Coverage
- All 9 TypeDB attribute types fully tested (Boolean, Date, DateTime, DateTimeTZ, Decimal, Double, Duration, Integer, String)
- Full CRUD operations for each type (insert, fetch, update, delete)
- Multi-value attribute operations
- Query pagination with limit/offset/sort
- Schema conflict detection and inheritance
- Reserved word validation

#### Code Quality
- ✅ Ruff linting: 0 errors, 0 warnings
- ✅ Ruff formatting: All 112 files properly formatted
- ✅ Pyright type checking: 0 errors, 0 warnings, 0 informations

### Documentation

- Updated README.md with current test counts and features
- Updated CLAUDE.md testing strategy section
- Added TypeDB 3.x compatibility notes
- Documented pagination requirements and automatic sorting

#### Key Files Modified
- `type_bridge/query.py` - Fixed clause ordering in build()
- `type_bridge/crud.py` - Added automatic sorting for pagination, fixed attribute access
- `type_bridge/schema/manager.py` - Updated to TypeDB 3.x `isa` syntax

## [0.2.0] - Previous Release

See git history for earlier changes.

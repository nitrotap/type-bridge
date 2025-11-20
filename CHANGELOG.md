# Changelog

All notable changes to TypeBridge will be documented in this file.

## [0.5.0] - 2025-11-20

### 🚀 New Features

#### Concise Attribute Type-Based Expression API
- **New streamlined query API using attribute class methods**
  - Old: `Person.age.gt(Age(30))` → New: `Age.gt(Age(30))` ✨
  - Shorter, more readable syntax with better type checking support
  - Type checkers now correctly validate all expression methods
  - Location: `type_bridge/attribute/base.py`, `type_bridge/attribute/string.py`

#### Class Methods Added to Attribute Base Class
- **Comparison methods**: `gt()`, `lt()`, `gte()`, `lte()`, `eq()`, `neq()`
  - Example: `Age.gt(Age(30))`, `Salary.gte(Salary(80000))`
- **Aggregation methods**: `sum()`, `avg()`, `max()`, `min()`, `median()`, `std()`
  - Example: `Salary.avg()`, `Age.sum()`
- **String-specific methods** (on `String` class): `contains()`, `like()`, `regex()`
  - Example: `Email.contains(Email("@company.com"))`, `Name.like(Name("^A.*"))`

#### Runtime Validation
- **Automatic attribute ownership validation in filter() methods**
  - Validates that entity owns the attribute type being queried
  - Raises `ValueError` with helpful message if validation fails
  - Example: `person_manager.filter(Salary.gt(Salary(50000)))` validates Person owns Salary
  - Location: `type_bridge/crud.py`, `type_bridge/expressions/base.py`

### 🔄 API Changes

#### Expression Classes Refactored
- **Changed from field-based to attribute type-based**
  - `ComparisonExpr`, `StringExpr`, `AggregateExpr` now use `attr_type` instead of `field`
  - Simpler internal structure with 1-to-1 mapping (attribute type uniquely identifies field)
  - Location: `type_bridge/expressions/comparison.py`, `type_bridge/expressions/string.py`, `type_bridge/expressions/aggregate.py`

#### Backwards Compatibility
- **Old field-based API still works**
  - `Person.age.gt(Age(30))` continues to work alongside new API
  - FieldRef classes now delegate to attribute class methods internally
  - Gradual migration path for existing code
  - Location: `type_bridge/fields.py`

### 🔧 Type Safety Improvements

#### Keyword-Only Arguments Enforced
- **Changed `@dataclass_transform(kw_only_default=False)` → `True`**
  - All Entity/Relation constructors now require keyword arguments for clarity and safety
  - Improves code readability and prevents positional argument order errors
  - Example: `Person(name=Name("Alice"), age=Age(30))` ✅
  - Positional args now rejected by type checkers: `Person(Name("Alice"), Age(30))` ❌
  - Location: `type_bridge/models/base.py:20`, `type_bridge/models/entity.py:81`, `type_bridge/models/relation.py:30`

#### Optional Field Defaults Required
- **Added explicit `= None` defaults for all optional fields**
  - Pattern: `age: Age | None = None` (previously `age: Age | None`)
  - Makes field optionality explicit in code for better clarity
  - Improves IDE autocomplete and type checking accuracy
  - Required by `kw_only_default=True` to distinguish optional from required fields
  - Applied throughout codebase: examples, tests, integration tests

#### Pyright Type Checking Configuration
- **Added `pyrightconfig.json`** for project-wide type checking
  - Excludes validation tests from type checking (`tests/unit/type-check-except/`)
  - Tests intentionally checking Pydantic validation failures now properly excluded
  - Core library achieves **0 errors, 0 warnings, 0 informations** ✨
  - Proper separation of type-safe code vs runtime validation tests
  - Location: `pyrightconfig.json` (new file)

#### Validation Tests Reorganized
- **Moved intentional validation tests to `tests/unit/type-check-except/`**
  - Tests using raw values to verify Pydantic validation now excluded from type checking
  - Original tests fixed to use properly wrapped attribute types
  - Clean separation: type-safe tests vs validation behavior tests
  - Moved files: `test_pydantic.py`, `test_basic.py`, `test_update_api.py`, `test_cardinality.py`, `test_list_default.py`

#### Benefits
1. **Clearer code**: Keyword arguments make field names explicit at call sites
2. **Better IDE support**: Explicit `= None` improves autocomplete for optional fields
3. **100% type safety**: Pyright validates correctly with zero false positives
4. **Maintainability**: Adding new fields doesn't break existing constructor calls
5. **Error prevention**: Type checker catches argument order mistakes at development time

### 📚 Documentation

#### Automatic Conversions Documented
- **`avg()` → `mean` in TypeQL**
  - TypeDB 3.x uses `mean` instead of `avg`
  - User calls `Age.avg()`, generates `mean($age)` in TypeQL
  - Result key converted back to `avg_age` for consistency
  - Clearly documented in docstrings and implementation comments
- **`regex()` → `like` in TypeQL**
  - TypeQL uses `like` for regex pattern matching
  - `regex()` provided as user-friendly alias
  - Both methods generate identical TypeQL output
  - Documented in method docstrings and code comments

#### TypeQL Compliance Verification
- **All expressions verified against TypeDB 3.x specification**
  - Comparison operators: `>`, `<`, `>=`, `<=`, `==`, `!=` ✓
  - String operations: `contains`, `like` ✓
  - Aggregations: `sum`, `mean`, `max`, `min`, `median`, `std`, `count` ✓
  - Boolean logic: `;` (AND), `or`, `not` ✓
  - Created `tmp/typeql_verification.md` and `tmp/automatic_conversions.md`

#### Examples Updated
- **Updated query_expressions.py to use new API**
  - All field-based expressions converted to attribute type-based
  - Added notes about API improvements and type safety
  - Location: `examples/advanced/query_expressions.py`

### 🧪 Testing

#### Test Results
- **417/417 tests passing** (100% pass rate) ✅
- **Unit tests**: 284/284 passing (0.3s)
- **Integration tests**: 133/133 passing
- **Type checking**: 0 errors, 0 warnings, 0 informations ✅
- All type errors eliminated (250 errors → 0 errors)

#### Tests Updated
- **Updated field reference tests for new API**
  - Tests now check `attr_type` instead of `field` attributes
  - All expression creation and TypeQL generation tests passing
  - Location: `tests/unit/expressions/test_field_refs.py`

#### Test Organization
- **Integration tests reorganized into subdirectories**
  - `tests/integration/queries/test_expressions.py` - Query expression integration tests
  - `tests/integration/crud/relations/test_abstract_roles.py` - Abstract role type tests
  - Better organization: crud/, queries/, schema/ subdirectories
  - Improved test discoverability and maintenance

### 🔧 Type Safety

#### Type Checking Improvements
- **Eliminated all expression-related type errors**
  - Before: 26 errors (`.gt()`, `.avg()` "not a known attribute" errors)
  - After: 0 errors ✅
  - Type checkers now fully understand class method API
  - Pyright passes with 0 errors, 0 warnings, 0 informations

#### Benefits
1. **Type-safe**: Full type checker support with zero errors
2. **Concise**: Shorter syntax (`Age.gt()` vs `Person.age.gt()`)
3. **Validated**: Runtime checks prevent invalid queries
4. **Compatible**: Old API still works for gradual migration
5. **Documented**: All automatic conversions clearly explained

### 📦 Key Files Modified

- `type_bridge/attribute/base.py` - Added class methods for comparisons and aggregations
- `type_bridge/attribute/string.py` - Added string-specific class methods
- `type_bridge/expressions/comparison.py` - Changed to `attr_type`-based
- `type_bridge/expressions/string.py` - Changed to `attr_type`-based
- `type_bridge/expressions/aggregate.py` - Changed to `attr_type`-based
- `type_bridge/expressions/base.py` - Added `get_attribute_types()` method
- `type_bridge/expressions/boolean.py` - Added recursive attribute type collection
- `type_bridge/fields.py` - Updated to delegate to attribute class methods
- `type_bridge/crud.py` - Added validation in filter() methods
- `examples/advanced/query_expressions.py` - Updated to use new API

## [0.4.4] - 2025-11-19

### 🐛 Bug Fixes

- **Fixed inherited attributes not included in insert/get operations**
  - Entity and Relation insert queries now include all inherited attributes
  - Fetch operations properly extract inherited attribute values
  - Added `get_all_attributes()` method to collect attributes from entire class hierarchy
  - Location: `type_bridge/models/base.py`, `type_bridge/models/entity.py`, `type_bridge/crud.py`

### 🔄 API Changes

- **Removed deprecated `EntityFlags` and `RelationFlags` aliases**
  - Use `TypeFlags` for both entities and relations
  - All example files updated to use `TypeFlags`
  - Documentation updated to reflect unified API

### 📚 Documentation

- **Updated CLAUDE.md**: Replaced all EntityFlags/RelationFlags references with TypeFlags
- **Updated examples**: All 17 example files now use the unified TypeFlags API

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

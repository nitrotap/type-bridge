# Changelog

All notable changes to TypeBridge will be documented in this file.

## [0.7.0] - 2025-12-08

### 🚀 New Features

#### TransactionContext for Shared Operations
- **Added `TransactionContext` class for sharing transactions across operations**
  - Multiple managers can share a single transaction
  - Auto-commit on context exit, rollback on exception
  - Location: `type_bridge/session.py`

```python
with db.transaction(TransactionType.WRITE) as tx:
    person_mgr = Person.manager(tx)     # reuses tx
    artifact_mgr = Artifact.manager(tx)  # same tx
    # ... operations commit together
```

#### Unified Connection Type
- **Added `Connection` type alias for flexible connection handling**
  - `Connection = Database | Transaction | TransactionContext`
  - All managers accept any Connection type
  - `ConnectionExecutor` handles transaction reuse internally
  - Location: `type_bridge/session.py`

#### Entity Dict Helpers
- **Added `Entity.to_dict()` for serialization**
  - Unwraps Attribute instances to `.value`
  - Supports `include`, `exclude`, `by_alias`, `exclude_unset` options
- **Added `Entity.from_dict()` for deserialization**
  - Optional `field_mapping` for external key names
  - `strict=False` mode to ignore unknown fields
  - Location: `type_bridge/models/entity.py`

```python
person.to_dict()  # {'name': 'Alice', 'age': 30}
Person.from_dict(payload, field_mapping={"display-id": "display_id"})
```

#### Django-style Lookup Filters
- **Added lookup suffix operators to `filter()`**
  - `__contains`, `__startswith`, `__endswith`, `__regex` for strings
  - `__gt`, `__gte`, `__lt`, `__lte` for comparisons
  - `__in` for disjunction (multiple values)
  - `__isnull` for null checks
  - Location: `type_bridge/crud/entity/manager.py`

```python
person_manager.filter(name__startswith="Al", age__gt=30).execute()
person_manager.filter(status__in=["active", "pending"]).execute()
```

#### Bulk Operations
- **Added `EntityManager.update_many()`** - Update multiple entities in one transaction
- **Added `EntityManager.delete_many()`** - Bulk delete with `__in` filter support

### 📚 Documentation

- **Comprehensive documentation update**
  - Fixed broken example paths in README.md
  - Added Connection types documentation to docs/api/crud.md
  - Added TransactionContext usage examples
  - Added lookup filter documentation with TypeQL mappings
  - Added dict helpers documentation to docs/api/entities.md

### 🔧 Maintenance

- Fixed version mismatch between pyproject.toml and __init__.py
- Added `typings/` stubs for `isodate` and `typedb.driver`

### 📦 Key Files Modified

- `type_bridge/session.py` - Added TransactionContext, Connection, ConnectionExecutor
- `type_bridge/models/entity.py` - Added to_dict(), from_dict()
- `type_bridge/crud/entity/manager.py` - Added lookup filters, update_many, delete_many
- `type_bridge/crud/relation/manager.py` - Unified connection handling
- `docs/api/crud.md` - New sections for transactions, lookups, bulk ops
- `docs/api/entities.md` - Dict helpers documentation

## [0.6.4] - 2025-12-04

### 🚀 New Features

#### CRUD PUT Operations (Idempotent Insert)
- **Added `EntityManager.put()` for idempotent entity insertion**
  - Inserts entity only if it doesn't already exist
  - Safe to call multiple times without creating duplicates
  - Uses TypeQL's PUT clause for atomic match-or-insert semantics
  - Location: `type_bridge/crud/entity/manager.py`

- **Added `EntityManager.put_many()` for bulk idempotent insertion**
  - All-or-nothing semantics: entire pattern must match or all is inserted
  - Efficient batch operations for data synchronization

- **Added `RelationManager.put()` for idempotent relation insertion**
  - Same PUT semantics for relations with role players
  - Prevents duplicate relationships
  - Location: `type_bridge/crud/relation/manager.py`

- **Added `RelationManager.put_many()` for bulk relation PUT**
  - Batch idempotent insertion for relations

#### Use Cases
- Data import scripts (safe re-runs)
- Ensuring reference data exists
- Synchronization with external systems
- Idempotent API endpoints

### 📚 Documentation

- **Updated `docs/api/crud.md`** with PUT operations section
  - Comparison table: INSERT vs PUT behavior
  - All-or-nothing semantics explanation
  - Usage examples for entities and relations

- **Added `examples/basic/crud_08_put.py`** tutorial
  - Demonstrates PUT vs INSERT differences
  - Shows idempotent behavior patterns

### 🧪 Testing

- **Added entity PUT integration tests** (`tests/integration/crud/entities/test_put.py`)
  - Single put, bulk put_many
  - Idempotency verification
  - All-or-nothing behavior

- **Added relation PUT integration tests** (`tests/integration/crud/relations/test_put.py`)
  - Relation put operations
  - Role player handling

### 📦 Key Files Modified

- `type_bridge/crud/entity/manager.py` - Added `put()`, `put_many()`
- `type_bridge/crud/relation/manager.py` - Added `put()`, `put_many()`
- `docs/api/crud.md` - PUT documentation
- `examples/basic/crud_08_put.py` - New tutorial
- `tests/integration/crud/entities/test_put.py` - Entity PUT tests
- `tests/integration/crud/relations/test_put.py` - Relation PUT tests
- `README.md` - Updated features

### 💡 Usage Examples

```python
# Single PUT (idempotent insert)
alice = Person(name=Name("Alice"), age=Age(30))
person_manager.put(alice)
person_manager.put(alice)  # No duplicate created

# Bulk PUT
persons = [Person(name=Name("Bob")), Person(name=Name("Carol"))]
person_manager.put_many(persons)
person_manager.put_many(persons)  # No duplicates

# Relation PUT
employment = Employment(employee=alice, employer=techcorp)
employment_manager.put(employment)
```

## [0.6.3] - 2025-12-04

### 🚀 New Features

#### Multi-Player Roles
- **Added `Role.multi()` for roles playable by multiple entity types**
  - Syntax: `origin: Role[Document | Email] = Role.multi("origin", Document, Email)`
  - Eliminates need for artificial supertype hierarchies
  - Generates multiple `plays` declarations in TypeQL schema
  - Location: `type_bridge/models/role.py`
- **Full CRUD support for multi-role relations**
  - Filter by specific player type: `manager.get(origin=doc)`
  - Chainable operations work with multi-roles
  - Batch insert with mixed player types supported
- **Runtime validation**: TypeError if wrong player type assigned
- **Pydantic integration**: Union types provide IDE/type-checker support

#### TypeDB 3.7 Compatibility
- **Verified compatibility with TypeDB 3.7.0-rc0**
- Updated documentation to reflect tested TypeDB version

### 🐛 Bug Fixes

#### Inherited Attribute Filter Bug
- **Fixed filters on inherited attributes being silently ignored**
  - Root cause: `get_owned_attributes()` was used instead of `get_all_attributes()` in filter operations
  - Affected methods: `EntityManager.delete()`, `EntityQuery.delete()`, `QueryBuilder.match_entity()`
  - Example: `Dog.manager(db).get(name=LivingName("Buddy"))` now works when `name` is inherited from parent `Living` class
  - Location: `type_bridge/crud/entity/query.py:215`, `type_bridge/crud/entity/manager.py:219`, `type_bridge/query.py:193`
- **Impact**: Dictionary-based filters (`get()`, `delete()`) now correctly handle inherited attributes in subtype queries

### 🧪 Testing

#### Multi-Role Tests
- **Multi-role integration tests** (`tests/integration/crud/relations/test_multi_role.py`) - 37 tests
  - Insert relations with different role player types
  - Filter by multi-role players
  - Delete filtered by multi-role
  - Chainable `update_with` operations
  - Multi-role with 3+ entity types
- **Multi-role unit tests** (`tests/unit/core/test_multi_role_players.py`)
  - Role.multi() API validation
  - Type safety and runtime validation

#### Inherited Attribute Filter Tests
- **Created unit tests** (`tests/unit/core/test_inherited_attribute_filter.py`) with 9 tests:
  - `get_owned_attributes()` vs `get_all_attributes()` behavior verification
  - `QueryBuilder.match_entity()` with inherited/owned/mixed attribute filters
  - Deep inheritance chain (grandparent → parent → child) attribute access
- **Created integration tests** (`tests/integration/crud/test_inherited_attribute_filter.py`) with 5 tests:
  - `get()` with inherited key attribute
  - `delete()` with inherited attribute filter
  - Combined inherited + owned attribute filters

### 📦 Key Files Modified

- `type_bridge/models/role.py` - Added `Role.multi()` and multi-player support
- `type_bridge/schema/info.py` - Generate multiple `plays` declarations
- `type_bridge/crud/relation/manager.py` - Multi-role query handling
- `type_bridge/crud/relation/query.py` - Multi-role filtering support
- `docs/api/relations.md` - Added "Multi-player Roles" documentation
- `type_bridge/crud/entity/query.py` - Fixed `delete()` to use `get_all_attributes()`
- `type_bridge/crud/entity/manager.py` - Fixed `delete()` to use `get_all_attributes()`
- `type_bridge/query.py` - Fixed `match_entity()` to use `get_all_attributes()`
- `tests/integration/crud/relations/test_multi_role.py` - New multi-role test suite (37 tests)
- `tests/unit/core/test_multi_role_players.py` - New multi-role unit tests

## [0.6.0] - 2025-11-24

### 🚀 New Features

#### Chainable Delete and Update Operations
- **Added `EntityQuery.delete()` for chainable deletion**
  - Delete entities after complex filtering: `manager.filter(Age.gt(Age(65))).delete()`
  - Builds TypeQL delete query from both dict-based and expression-based filters
  - Single atomic transaction with automatic rollback on error
  - Returns count of deleted entities (0 if no matches)
  - Location: `type_bridge/crud.py:626-676`

- **Added `EntityQuery.update_with(func)` for functional bulk updates**
  - Update multiple entities using lambda or named functions
  - Example: `manager.filter(Age.gt(Age(30))).update_with(lambda p: setattr(p, 'age', Age(p.age.value + 1)))`
  - Fetches matching entities, applies function, updates all in single transaction
  - Returns list of updated entities (empty list if no matches)
  - Error handling: Stops immediately and raises error if function fails on any entity
  - All updates in single atomic transaction (all-or-nothing)
  - Location: `type_bridge/crud.py:678-730`

- **Helper methods added**
  - `_build_update_query(entity)`: Builds TypeQL update query for single entity
  - `_is_multi_value_attribute(flags)`: Checks attribute cardinality
  - Reuses existing EntityManager logic for consistency

#### Benefits
1. **Chainable API**: Natural method chaining for complex operations
2. **Type-safe**: Full integration with expression-based filtering
3. **Atomic transactions**: All operations are all-or-nothing
4. **Functional updates**: Clean lambda/function-based bulk updates
5. **Consistent API**: Works seamlessly with existing filter() method

#### AttributeFlags Configuration for Attribute Type Names
- **Added `AttributeFlags.name` field**
  - Explicitly override attribute type name: `flags = AttributeFlags(name="person_name")`
  - Use case: Interop with existing TypeDB schemas, legacy naming conventions
  - Location: `type_bridge/attribute/flags.py:229`

- **Added `AttributeFlags.case` field**
  - Apply case formatting to attribute type names: `flags = AttributeFlags(case=TypeNameCase.SNAKE_CASE)`
  - Supports: CLASS_NAME (default), LOWERCASE, SNAKE_CASE, KEBAB_CASE
  - Use case: Consistent naming conventions across large schemas
  - Location: `type_bridge/attribute/flags.py:230`

- **Updated `Attribute.__init_subclass__` to use AttributeFlags**
  - Priority: flags.name > attr_name > flags.case > class.case > default CLASS_NAME
  - Respects both explicit name and case formatting
  - Location: `type_bridge/attribute/base.py:108-126`

#### Benefits
1. **Flexible naming**: Support for legacy schemas and naming conventions
2. **Consistent API**: Mirrors TypeFlags.name pattern for entities/relations
3. **Migration friendly**: Easier interop with existing TypeDB databases
4. **Developer choice**: Explicit name or automatic case formatting

### 🏗️ Refactoring

#### Modularized CRUD Operations
- **Refactored monolithic `crud.py` (3008 lines) into modular structure**
  - Split into 11 focused modules under `crud/` directory
  - Entity operations: `crud/entity/` with manager, query, and group_by modules
  - Relation operations: `crud/relation/` with manager, query, and group_by modules
  - Shared utilities: `crud/utils.py` for `format_value` and `is_multi_value_attribute`
  - Base definitions: `crud/base.py` for type variables
- **Benefits**:
  - Eliminated code duplication (shared utilities now have single implementations)
  - Improved maintainability (files are now 200-800 lines each)
  - Better code organization and discoverability
  - Preserved backward compatibility (all imports still work)
- **Impact**: No breaking changes, all existing code continues to work

#### Modularized Models
- **Previously refactored `models.py` into modular structure**
  - Split into `models/` directory with base, entity, relation, role, and utils modules
  - Improved separation of concerns and maintainability

### 🐛 Bug Fixes

#### String Attribute Escaping in Multi-Value Attributes
- **Fixed proper escaping of special characters in multi-value string attributes**
  - Backslashes are now properly escaped: `\` → `\\`
  - Double quotes are properly escaped: `"` → `\"`
  - Escape order matters: backslashes first, then quotes
  - Location: `type_bridge/query.py`, `type_bridge/crud.py`, `type_bridge/models/base.py`
- **Impact**: Multi-value string attributes with quotes or backslashes now work correctly in insert/update operations
- **Examples**:
  - Quotes: `Tag('skill "Python"')` → TypeQL: `has Tag "skill \"Python\""`
  - Backslashes: `Path("C:\\Users\\Alice")` → TypeQL: `has Path "C:\\Users\\Alice"`
  - Mixed: `Description(r'Path: "C:\Program Files"')` → TypeQL: `has Description "Path: \"C:\\Program Files\""`

### 📚 Documentation

#### API Documentation Updated
- **Updated `docs/api/crud.md`** with comprehensive new sections:
  - Chainable Delete section with examples and behavior explanation
  - Bulk Update with Function section demonstrating lambda and named function usage
  - Updated EntityQuery method signatures
  - Added "New in v0.6.0" markers for discoverability
  - Error handling and empty results behavior documented

- **Updated `docs/api/attributes.md`** with new section:
  - "Configuring Attribute Type Names" section with comprehensive examples
  - Documents AttributeFlags.name for explicit type name overrides
  - Documents AttributeFlags.case for automatic case formatting
  - Shows priority order and all configuration options
  - Use cases and best practices

- **Updated `docs/INTERNALS.md`**:
  - Updated AttributeFlags dataclass documentation
  - Added name and case fields with usage examples
  - Updated cardinality field names (card_min, card_max)

#### README Updated
- **Added "Chainable Operations" to features list**
  - Highlights filter, delete, and bulk update capabilities
  - Location: `README.md`

#### New Example Created
- **Created `examples/advanced/crud_07_chainable_operations.py`**
  - Comprehensive demonstration of chainable delete and update
  - Shows lambda functions, named functions, and complex multi-attribute updates
  - Demonstrates atomic transaction behavior with rollback examples
  - Interactive tutorial format with step-by-step explanations

### 🧪 Testing

#### Integration Tests Added
- **Created `tests/integration/crud/entities/test_chainable.py`** with 9 comprehensive tests:
  1. `test_chainable_delete_with_expression_filter` - Basic delete with expressions
  2. `test_chainable_delete_with_multiple_filters` - Multiple filter combinations
  3. `test_chainable_delete_returns_zero_for_no_matches` - Empty results handling
  4. `test_chainable_delete_with_range_filter` - Range queries (gte/lt)
  5. `test_update_with_lambda_increments_age` - Lambda function updates
  6. `test_update_with_function_modifies_status` - Named function updates
  7. `test_update_with_returns_empty_list_for_no_matches` - Empty results handling
  8. `test_update_with_complex_function_multiple_attributes` - Multi-attribute updates
  9. `test_update_with_atomic_transaction` - Transaction rollback verification

#### Test Results
- **All 9 tests passing** ✅
- Tests verify:
  - Correct entity deletion with expression filters
  - Accurate counts returned
  - Proper transaction boundaries (atomic behavior)
  - Error propagation and rollback
  - Empty result handling
  - Multi-attribute updates
  - Lambda and function-based updates

#### Escaping Test Coverage Added
- **Created comprehensive string escaping test suite**
  - 7 unit tests for multi-value string escaping patterns
  - 9 integration tests verifying end-to-end escaping behavior
  - Location: `tests/unit/attributes/test_multivalue_escaping.py`, `tests/integration/crud/attributes/test_multivalue_escaping.py`
- **Test coverage includes**:
  - Quotes in strings: `'skill "Python"'`
  - Backslashes in paths: `C:\Users\Alice`
  - Mixed escaping: `"C:\Program Files\App"`
  - Empty strings and special characters
  - Unicode characters (café, 日本語, emoji😀)
  - Single quotes (not escaped in TypeQL)
  - Relations with multi-value escaping
  - Batch operations: `insert_many()`, `update_with()`

### 📦 Key Files Modified

- `type_bridge/crud.py` - Added delete() and update_with() to EntityQuery class
- `docs/api/crud.md` - Updated API documentation with new methods
- `README.md` - Added chainable operations to features list
- `examples/advanced/crud_07_chainable_operations.py` - New comprehensive example
- `tests/integration/crud/entities/test_chainable.py` - New integration test suite
- `tests/unit/attributes/test_multivalue_escaping.py` - New unit test suite (7 tests)
- `tests/integration/crud/attributes/test_multivalue_escaping.py` - New integration test suite (9 tests)

### 💡 Usage Examples

#### Chainable Delete
```python
# Delete all persons over 65
count = Person.manager(db).filter(Age.gt(Age(65))).delete()

# Delete with multiple filters
count = manager.filter(
    Age.lt(Age(18)),
    Status.eq(Status("inactive"))
).delete()
```

#### Chainable Update with Lambda
```python
# Increment age for all persons over 30
updated = manager.filter(Age.gt(Age(30))).update_with(
    lambda person: setattr(person, 'age', Age(person.age.value + 1))
)
```

#### Chainable Update with Function
```python
def promote(person):
    person.status = Status("senior")
    person.salary = Salary(int(person.salary.value * 1.1))

promoted = manager.filter(Age.gte(Age(35))).update_with(promote)
```

## [0.5.1] - 2025-11-20

### 🐛 Bug Fixes

#### Integer Key Query Bug
- **Fixed entities with Integer-type keys failing to query by key value**
  - Root cause: Attribute instances not being unwrapped before TypeQL value formatting
  - `EntityId(123)` was formatted as `"123"` (string) instead of `123` (integer)
  - Generated incorrect TypeQL: `has EntityId "123"` causing type mismatch
  - Fix: Added `.value` extraction in `_format_value()` before type checking
  - Location: `type_bridge/query.py:252-256`, `type_bridge/crud.py:419-423`, `type_bridge/crud.py:1145-1149`
- **Impact**: All non-string attribute types (Integer, Double, Decimal, Boolean, Date, DateTime, DateTimeTZ, Duration) now work correctly as entity keys and in query filters
- **Silent failure fixed**: Entities would insert successfully but couldn't be queried, now both work correctly

### 🧪 Testing

#### Regression Tests Added
- **Created comprehensive Integer key test suite**
  - 5 new integration tests specifically for Integer key bug regression
  - Tests cover: basic insert/query, comparison with String keys, various integer values, chainable queries, all()/count() methods
  - Location: `tests/integration/crud/entities/test_integer_key_bug.py`
- **Test Results**: 422/422 tests passing (284 unit + 138 integration) ✅
  - All existing tests still passing
  - All new regression tests passing
  - Zero test failures or regressions

#### Why String Keys Worked
- String attributes need quotes in TypeQL anyway
- Bug accidentally produced correct output: `"KEY-123"`
- Integer, Boolean, Double, etc. require unquoted values in TypeQL
- These would fail with incorrect quoting: `"123"`, `"true"`, `"3.14"`

### 📦 Key Files Modified

- `type_bridge/query.py` - Fixed `_format_value()` function
- `type_bridge/crud.py` - Fixed `EntityManager._format_value()` and `RelationManager._format_value()`
- `tests/integration/crud/entities/test_integer_key_bug.py` - New regression test suite (5 tests)

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

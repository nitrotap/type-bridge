# TypeNameCase Feature

## Overview

Added a new `TypeNameCase` enum to control how Python class names are converted to TypeDB type names for Entity and Relation types.

## Features

### Three Case Formatting Options

1. **LOWERCASE** (default)
   - Converts class name to all lowercase
   - Example: `PersonName` → `personname`
   - Traditional TypeDB/SQL naming convention

2. **CLASS_NAME**
   - Keeps class name as-is (preserves PascalCase)
   - Example: `PersonName` → `PersonName`
   - Useful when Python naming matches desired TypeDB names

3. **SNAKE_CASE** (recommended for multi-word names)
   - Converts PascalCase to snake_case
   - Example: `PersonName` → `person_name`
   - Most readable for complex type names
   - Handles acronyms: `HTTPResponse` → `http_response`

### Usage

```python
from type_bridge import Entity, EntityFlags, TypeNameCase

# Default: LOWERCASE
class Person(Entity):
    name: Name  # TypeDB type: "person"

# Explicit SNAKE_CASE
class PersonName(Entity):
    flags = EntityFlags(case=TypeNameCase.SNAKE_CASE)
    name: Name  # TypeDB type: "person_name"

# Keep as-is with CLASS_NAME
class PersonName(Entity):
    flags = EntityFlags(case=TypeNameCase.CLASS_NAME)
    name: Name  # TypeDB type: "PersonName"

# Explicit type_name takes precedence
class PersonName(Entity):
    flags = EntityFlags(type_name="person", case=TypeNameCase.SNAKE_CASE)
    name: Name  # TypeDB type: "person" (explicit type_name used)
```

### Relations Support

Relations also support the same case formatting options:

```python
from type_bridge import Relation, RelationFlags, TypeNameCase

class PersonCompanyEmployment(Relation):
    flags = RelationFlags(case=TypeNameCase.SNAKE_CASE)
    employee: Role[Person] = Role("employee", Person)
    employer: Role[Company] = Role("employer", Company)
    # TypeDB type: "person_company_employment"
```

## Implementation Details

### Files Modified

1. **type_bridge/attribute/flags.py**
   - Added `TypeNameCase` enum
   - Added `_to_snake_case()` helper function
   - Added `format_type_name()` function
   - Updated `EntityFlags` and `RelationFlags` with `case` parameter

2. **type_bridge/models.py**
   - Updated `Entity.get_type_name()` to use case formatting
   - Updated `Relation.get_type_name()` to use case formatting
   - Updated validation logic in `__init_subclass__`

3. **type_bridge/attribute/__init__.py**
   - Exported `TypeNameCase`

4. **type_bridge/__init__.py**
   - Exported `TypeNameCase` from top-level package

### Tests

Created comprehensive test suite: **tests/test_typename_case.py**
- 17 tests covering all three case options
- Tests for entities and relations
- Tests for schema generation
- Tests for complex class names (acronyms, multiple words)
- Tests for explicit type_name precedence
- Tests for inheritance scenarios

All 75 tests pass (17 new tests + 58 existing tests).

### Example

Created demonstration example: **examples/advanced/typename_case.py**
- Shows all three case formatting options
- Demonstrates schema generation
- Provides usage recommendations
- Interactive demo with clear output

## Quality Assurance

✅ All 75 tests pass
✅ Pyright: 0 errors, 0 warnings
✅ Code formatted with ruff
✅ Follows project conventions (PEP 604, dataclasses, modern Python)
✅ Zero technical debt added

## Backward Compatibility

✅ Fully backward compatible
- Default behavior unchanged (LOWERCASE)
- Existing code continues to work
- Explicit `type_name` takes precedence as before

## Best Practices

**When to use each option:**

- **LOWERCASE**: Simple single-word class names (Person, Company)
- **CLASS_NAME**: When preserving exact class names is important
- **SNAKE_CASE**: Multi-word class names (recommended!), provides best readability
- **Explicit type_name**: Complete control for legacy compatibility

## API Reference

```python
class TypeNameCase(Enum):
    """Type name case formatting options."""
    LOWERCASE = "lowercase"    # Default
    CLASS_NAME = "classname"   # Preserve as-is
    SNAKE_CASE = "snake_case"  # Convert to snake_case

class EntityFlags:
    type_name: str | None = None
    abstract: bool = False
    base: bool = False
    case: TypeNameCase = TypeNameCase.LOWERCASE  # New parameter

class RelationFlags:
    type_name: str | None = None
    abstract: bool = False
    base: bool = False
    case: TypeNameCase = TypeNameCase.LOWERCASE  # New parameter
```

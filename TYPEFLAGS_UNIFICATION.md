# TypeFlags Unification

## Summary

Unified `EntityFlags` and `RelationFlags` into a single `TypeFlags` class, and renamed the `type_name` parameter to `name` for simplicity and consistency.

## Changes

### 1. New Unified API

**Before:**
```python
from type_bridge import Entity, Relation, EntityFlags, RelationFlags

class Person(Entity):
    flags = EntityFlags(type_name="person")
    name: Name

class Employment(Relation):
    flags = RelationFlags(type_name="employment")
    employee: Role[Person] = Role("employee", Person)
```

**After:**
```python
from type_bridge import Entity, Relation, TypeFlags

class Person(Entity):
    flags = TypeFlags(name="person")  # Unified class, renamed parameter
    name: Name

class Employment(Relation):
    flags = TypeFlags(name="employment")  # Same class for both!
    employee: Role[Person] = Role("employee", Person)
```

### 2. Parameter Rename: `type_name` → `name`

The parameter has been simplified from `type_name` to just `name`:

```python
# NEW (recommended)
flags = TypeFlags(name="person")

# OLD (still works for backward compatibility)
flags = EntityFlags(type_name="person")
```

### 3. Backward Compatibility

**100% backward compatible!** Old code continues to work:

- `EntityFlags` → alias to `TypeFlags`
- `RelationFlags` → alias to `TypeFlags`
- `type_name` parameter → still accepted, mapped to `name`

```python
# All of these work:
flags = TypeFlags(name="person")           # ✓ New API
flags = EntityFlags(type_name="person")    # ✓ Old API still works
flags = RelationFlags(type_name="person")  # ✓ Old API still works
flags = TypeFlags(type_name="person")      # ✓ Mixed old/new still works
```

## Implementation Details

### Files Modified

1. **type_bridge/attribute/flags.py**
   - Created new `TypeFlags` class with `name` parameter
   - Added backward compatibility in `__init__()` to accept `type_name`
   - Made `EntityFlags` and `RelationFlags` aliases to `TypeFlags`

2. **type_bridge/models.py**
   - Updated `Entity.get_type_name()` to use `cls._flags.name`
   - Updated `Relation.get_type_name()` to use `cls._flags.name`
   - Updated validation logic to use `.name` instead of `.type_name`

3. **type_bridge/attribute/__init__.py**
   - Exported `TypeFlags` alongside backward compatibility aliases

4. **type_bridge/__init__.py**
   - Exported `TypeFlags` as primary API

### New Example

Created `examples/advanced/typeflags_demo.py` demonstrating:
- Using TypeFlags for both entities and relations
- The `name` parameter
- Backward compatibility with old API

## Benefits

1. **Simpler API**: One class (`TypeFlags`) instead of two
2. **Cleaner parameter name**: `name` instead of `type_name`
3. **More intuitive**: Same flags class works for both entities and relations
4. **100% backward compatible**: No breaking changes
5. **Easier to learn**: Fewer classes to remember

## Migration Guide

### For New Code

Use the new API:
```python
from type_bridge import TypeFlags

class Person(Entity):
    flags = TypeFlags(name="person")
```

### For Existing Code

No changes required! Your existing code using `EntityFlags(type_name=...)` or `RelationFlags(type_name=...)` continues to work.

### Gradual Migration

You can migrate gradually:
```python
# Mix old and new in the same codebase
class Person(Entity):
    flags = EntityFlags(type_name="person")  # Old style, still works

class Company(Entity):
    flags = TypeFlags(name="company")  # New style
```

## API Reference

```python
@dataclass
class TypeFlags:
    """Unified flags for Entity and Relation classes."""
    name: str | None = None           # TypeDB type name (was: type_name)
    abstract: bool = False            # Abstract type
    base: bool = False                # Python-only base class
    case: TypeNameCase = CLASS_NAME   # Case formatting

# Backward compatibility
EntityFlags = TypeFlags
RelationFlags = TypeFlags
```

## Quality Assurance

✅ All 93 tests pass
✅ Pyright: 0 errors, 0 warnings
✅ 100% backward compatible
✅ Code formatted with ruff
✅ New example created and tested

## Recommendations

1. **New projects**: Use `TypeFlags(name=...)`
2. **Existing projects**: No immediate action needed, migrate at your convenience
3. **Documentation**: Update to show `TypeFlags` as the primary API
4. **Future**: May deprecate `EntityFlags`/`RelationFlags` aliases in future major version

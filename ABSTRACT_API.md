# Abstract Types and Interface Hierarchies in TypeBridge

This document explains how abstract types, interface hierarchies, and polymorphic queries work in TypeDB 3.x and how to properly use them in TypeBridge.

## Table of Contents

1. [What Are Abstract Types?](#what-are-abstract-types)
2. [Interface Hierarchies](#interface-hierarchies)
3. [Abstract Types in TypeDB 3.x vs 2.x](#abstract-types-in-typedb-3x-vs-2x)
4. [Querying Abstract Types](#querying-abstract-types)
5. [TypeBridge Implementation](#typebridge-implementation)
6. [Common Patterns](#common-patterns)
7. [Known Issues and Solutions](#known-issues-and-solutions)

---

## What Are Abstract Types?

In TypeDB 3.x, **abstractness serves one primary purpose: making a type non-instantiable**. Abstract types cannot have direct instances created but serve as interface contracts that concrete subtypes must implement.

### Key Characteristics

- **Abstract types cannot be instantiated** - you cannot create direct instances
- **Abstract types CAN be queried polymorphically** - queries match all concrete subtypes
- **Abstract types define contracts** - they establish common attributes/roles that subtypes inherit
- **Granular control** - unlike TypeDB 2.x, you can choose which parts of an interface are abstract

### Example Schema

```typeql
# Abstract attribute type
attribute isbn @abstract, value string;

# Concrete subtypes
attribute isbn-10 sub isbn, value string;
attribute isbn-13 sub isbn, value string;

# Abstract entity type
entity book @abstract,
    owns isbn;

# Concrete subtypes
entity paperback sub book,
    owns isbn-10 as isbn;

entity hardback sub book,
    owns isbn-13 as isbn;
```

---

## Interface Hierarchies

TypeDB treats interfaces as first-class types that form their own hierarchies. This enables powerful polymorphic querying and prevents interface redundancies.

### Ownership Interfaces

When attributes form type hierarchies, their ownership interfaces inherit accordingly:

```typeql
attribute isbn @abstract, value string;
attribute isbn-10 sub isbn, value string;
attribute isbn-13 sub isbn, value string;

# Ownership interfaces:
# isbn:OWNER (abstract)
#   ├── isbn-10:OWNER
#   └── isbn-13:OWNER
```

### Role Interfaces

Relation type hierarchies create corresponding role interface hierarchies:

```typeql
relation contribution @abstract,
    relates contributor;

relation authoring sub contribution,
    relates author as contributor;

relation editing sub contribution,
    relates editor as contributor;

# Role interfaces:
# contribution:contributor (abstract)
#   ├── authoring:author (override)
#   └── editing:editor (override)
```

### Role Inheritance vs Override

**When to inherit roles:**
- Role players of the parent relation should also play roles in subtypes
- Example: All `contribution:contributor` instances can be `authoring:author`

**When to override roles:**
- Role players should be specialized to the subtype
- Overriding "acts like a combination of subtyping and making the inherited value abstract"
- Example: `employment:employee` overrides `relation:role-player` for specialization

---

## Abstract Types in TypeDB 3.x vs 2.x

### TypeDB 2.x: "Infectious Abstractness"

In TypeDB 2.x, abstractness was infectious - if a type was abstract, all types that referenced it were forced to be abstract as well. Non-abstract entities couldn't own abstract attributes.

### TypeDB 3.x: Granular Control

TypeDB 3.x provides **granular control** over which interface elements form contracts:

```typeql
# ✅ ALLOWED in TypeDB 3.x
entity book,  # Non-abstract entity
    owns isbn;  # Can own abstract attribute

# The entity is concrete, but it contracts to own
# the abstract isbn interface (implemented by isbn-10 or isbn-13)
```

**Key difference**: Non-abstract entities can now own abstract attributes, giving you precise control over interface contracts.

---

## Querying Abstract Types

### Polymorphic Queries

**You CAN query abstract types polymorphically** - the query matches all concrete subtypes:

```typeql
# Query abstract type - matches ALL concrete subtypes
match
$book isa book;  # Matches paperback, hardback, and any other book subtypes
```

### Exact Type Matching

Use `isa!` to match only the exact type (not subtypes):

```typeql
# Match only direct instances (won't match if book is abstract)
match
$book isa! book;

# With abstract types, this returns nothing since abstract types have no instances
```

### Attribute Polymorphism

```typeql
# Query abstract attribute - retrieves all concrete implementations
match
$book isa book, has isbn $isbn;

# This matches books with isbn-10 OR isbn-13
# The abstract type acts as a polymorphic umbrella
```

### Relation Polymorphism

```typeql
# Query abstract relation - matches all concrete subtypes
match
$contrib (contributor: $person) isa contribution;

# Matches authoring, editing, illustrating, etc.
```

---

## TypeBridge Implementation

### Defining Abstract Types

Use `TypeFlags(abstract=True)` to mark entities, relations, or attributes as abstract:

```python
from type_bridge import Entity, Relation, String, TypeFlags, Flag, Key

class ISBN(String):
    """Abstract ISBN attribute."""
    flags = TypeFlags(type_name="isbn", abstract=True)

class ISBN10(ISBN):
    """Concrete ISBN-10."""
    flags = TypeFlags(type_name="isbn-10")

class ISBN13(ISBN):
    """Concrete ISBN-13."""
    flags = TypeFlags(type_name="isbn-13")

class Book(Entity):
    """Abstract book entity."""
    flags = TypeFlags(type_name="book", abstract=True)
    isbn: ISBN = Flag(Key)

class Paperback(Book):
    """Concrete paperback book."""
    flags = TypeFlags(type_name="paperback")

class Hardback(Book):
    """Concrete hardback book."""
    flags = TypeFlags(type_name="hardback")
```

### Inherited Attributes

**Critical**: Concrete subtypes inherit attributes from abstract parents. When creating instances, you must use the concrete attribute types:

```python
# ✅ CORRECT: Use concrete attribute type
paperback = Paperback(isbn=ISBN10("0123456789"))

# ❌ WRONG: Cannot instantiate abstract attribute
paperback = Paperback(isbn=ISBN("0123456789"))  # Error!
```

### Querying with Abstract Types

TypeBridge managers support polymorphic queries:

```python
# Create manager for abstract type
book_manager = Book.manager(db)

# Query returns ALL concrete subtypes (paperback, hardback, etc.)
all_books = book_manager.all()

# Filter by inherited attribute
books_with_isbn = book_manager.filter(isbn="0123456789")
```

---

## Common Patterns

### Pattern 1: Abstract Base with Common Attributes

Define common attributes once on an abstract parent:

```python
class Token(Entity):
    """Abstract base for all token types."""
    flags = TypeFlags(type_name="token", abstract=True)
    text: TokenText = Flag(Key)
    confidence: Confidence | None

class Symptom(Token):
    """Concrete symptom token."""
    flags = TypeFlags(type_name="symptom")

class Problem(Token):
    """Concrete problem token."""
    flags = TypeFlags(type_name="problem")

class Hypothesis(Token):
    """Concrete hypothesis token."""
    flags = TypeFlags(type_name="hypothesis")
```

**Benefits**:
- DRY principle - define `text` and `confidence` once
- Polymorphic queries - `Token.manager(db).all()` returns all token types
- Type safety - each concrete type is distinct

### Pattern 2: Abstract Relations with Polymorphic Roles

Use abstract types in role definitions for flexibility:

```python
class TokenOrigin(Relation):
    """Links tokens to their source documents."""
    flags = TypeFlags(type_name="token_origin")
    token: Role[Token] = Role("token", Token)  # Abstract type!
    document: Role[Document] = Role("document", Document)

# Works with ANY concrete token type
symptom = Symptom(text=TokenText("fever"))
doc = Document(id=DocId("DOC-123"))
origin = TokenOrigin(token=symptom, document=doc)
```

**Benefits**:
- Flexible - accepts any token subtype (Symptom, Problem, Hypothesis)
- Single relation type - no need for SymptomOrigin, ProblemOrigin, etc.
- Polymorphic queries - find origins for any token type

### Pattern 3: Interface Hierarchies for Polymorphism

Avoid redundant interfaces by using unified abstract types:

```python
# ❌ BAD: Redundant interfaces
class Location(Relation):
    relates located
    relates location

class Publishing(Relation):
    relates published
    relates location  # Redundant with Location.location!

# ✅ GOOD: Nested relations with unified interface
class Locating(Relation):
    """Abstract location relation."""
    flags = TypeFlags(type_name="locating", abstract=True)
    relates located
    relates location

class CityLocation(Locating):
    """City is located in country."""
    flags = TypeFlags(type_name="city_location")

class Publishing(Relation):
    """Publishing plays 'located' role in Locating."""
    # Publishing instances can play the 'located' role
    pass
```

---

## Known Issues and Solutions

### Issue: Relation Insertion with Abstract Role Types (FIXED)

**Problem**: When a relation uses an abstract type in a role definition (e.g., `Role[Token]`), and you try to insert the relation with a concrete entity (e.g., `Symptom`), the insertion fails with:

```
[INF10] Typing information for the variable 'token' is not available.
```

**Root Cause**: The `RelationManager.insert()` method used `get_owned_attributes()` to find key attributes for matching entities. When an entity inherits its key attribute from an abstract parent (e.g., `Symptom` inherits `text` from `Token`), `get_owned_attributes()` returns an empty dict, so no match clause is generated.

**Solution**: Changed `RelationManager.insert()` and `insert_many()` to use `get_all_attributes()` instead of `get_owned_attributes()`. This includes inherited attributes when building match clauses:

```python
# Before (BROKEN):
key_attrs = {
    field_name: attr_info
    for field_name, attr_info in entity.__class__.get_owned_attributes().items()
    if attr_info.flags.is_key
}

# After (FIXED):
key_attrs = {
    field_name: attr_info
    for field_name, attr_info in entity.__class__.get_all_attributes().items()
    if attr_info.flags.is_key
}
```

**Generated TypeQL (after fix)**:

```typeql
match
$token isa symptom, has TokenText "fever";
$doc isa document, has DocId "DOC-123";
insert
(token: $token, document: $doc) isa token_origin;
```

### Best Practice: Use Concrete Types for Instances

Always instantiate with **concrete types**, never abstract types:

```python
# ✅ CORRECT
symptom = Symptom(text=TokenText("fever"))

# ❌ WRONG - Cannot instantiate abstract type
token = Token(text=TokenText("fever"))  # Error!
```

### Best Practice: get_all_attributes() for Inherited Properties

When working with entities that may inherit attributes, always use `get_all_attributes()` instead of `get_owned_attributes()`:

```python
# ✅ CORRECT: Includes inherited attributes
all_attrs = entity.__class__.get_all_attributes()

# ❌ WRONG: Only includes attributes defined directly on the class
owned_attrs = entity.__class__.get_owned_attributes()
```

---

## Summary

1. **Abstract types cannot be instantiated** but can be queried polymorphically
2. **Use abstract types for interface contracts** and common attribute definitions
3. **Concrete subtypes inherit attributes** from abstract parents
4. **Always instantiate with concrete types**, never abstract types
5. **Use `get_all_attributes()` for inherited properties** in queries and CRUD operations
6. **Abstract types in role definitions** enable flexible, polymorphic relations
7. **TypeDB 3.x provides granular control** - non-abstract entities can own abstract attributes

For more details, see the official TypeDB documentation:
- [Using Interface Hierarchies](https://typedb.com/docs/academy/9-modeling-schemas/9.6-using-interface-hierarchies/)
- [Avoiding Interface Redundancies](https://typedb.com/docs/academy/9-modeling-schemas/9.7-avoiding-interface-redundancies/)
- [Abstract Contracts](https://typedb.com/docs/academy/9-modeling-schemas/9.8-abstract-contracts/)

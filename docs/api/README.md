# TypeBridge API Reference

Complete API reference for TypeBridge - a Python ORM for TypeDB with an Attribute-based API.

## Overview

TypeBridge provides a Pythonic interface to TypeDB that aligns with TypeDB's type system, where **attributes are base types** that **entities and relations own**.

## API Documentation

### Core Concepts

- **[Attributes](attributes.md)** - All 9 attribute types and value types
- **[Entities](entities.md)** - Entity definition, ownership, and inheritance
- **[Relations](relations.md)** - Relations, roles, and role players
- **[Cardinality](cardinality.md)** - Card API and Flag system for constraints

### Data Operations

- **[CRUD Operations](crud.md)** - Create, read, update, delete with type-safe managers
- **[Queries](queries.md)** - Query expressions, filtering, aggregations, and pagination
- **[Schema Management](schema.md)** - Schema operations, conflict detection, and migrations

### Validation and Type Safety

- **[Validation](validation.md)** - Pydantic integration, type safety, and literal types

## Quick Reference

### Basic Usage Pattern

```python
from type_bridge import Entity, TypeFlags, String, Integer, Flag, Key

# 1. Define attribute types
class Name(String):
    pass

class Age(Integer):
    pass

# 2. Define entity with ownership
class Person(Entity):
    flags = TypeFlags(type_name="person")
    name: Name = Flag(Key)
    age: Age | None = None  # Optional field

# 3. Create instances (keyword arguments required)
alice = Person(name=Name("Alice"), age=Age(30))

# 4. CRUD operations
person_manager = Person.manager(db)
person_manager.insert(alice)
persons = person_manager.all()
```

## Key Principles

### 1. Attributes Are Independent Types

Define attributes once, reuse across entities/relations:

```python
class Name(String):
    pass

class Person(Entity):
    name: Name  # Person owns 'name'

class Company(Entity):
    name: Name  # Company also owns 'name'
```

### 2. Use TypeFlags for Configuration

Clean API with `TypeFlags`:

```python
class Person(Entity):
    flags = TypeFlags(type_name="person")  # Clean API
```

### 3. Use Flag System for Annotations

```python
from type_bridge import Flag, Key, Unique, Card

name: Name = Flag(Key)                    # @key (implies @card(1..1))
email: Email = Flag(Unique)               # @unique (default @card(1..1))
age: Age | None = None                    # @card(0..1) - PEP 604 syntax
tags: list[Tag] = Flag(Card(min=2))       # @card(2..) - multi-value
```

### 4. Python Inheritance Maps to TypeDB Supertypes

```python
class Animal(Entity):
    flags = TypeFlags(abstract=True)

class Dog(Animal):  # Generates: entity dog, sub animal
    pass
```

### 5. Keyword-Only Arguments

All Entity/Relation constructors require keyword arguments:

```python
# ✅ CORRECT
person = Person(name=Name("Alice"), age=Age(30))

# ❌ WRONG
person = Person(Name("Alice"), Age(30))
```

## Generated Schema Example

The Python code above generates this TypeQL schema:

```typeql
define

# Attributes (defined once, can be owned by multiple types)
attribute name, value string;
attribute age, value integer;

# Entities declare ownership with cardinality annotations
entity person,
    owns name @key,
    owns age @card(0..1);
```

## Navigation

- [Attributes Documentation](attributes.md)
- [Entities Documentation](entities.md)
- [Relations Documentation](relations.md)
- [Cardinality Documentation](cardinality.md)
- [CRUD Operations Documentation](crud.md)
- [Queries Documentation](queries.md)
- [Schema Management Documentation](schema.md)
- [Validation Documentation](validation.md)

---

For TypeDB integration details, see [../TYPEDB.md](../TYPEDB.md).

For development guidelines, see [../DEVELOPMENT.md](../DEVELOPMENT.md).

For abstract types, see [../../ABSTRACT_API.md](../../ABSTRACT_API.md).

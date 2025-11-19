"""Demonstration of base flag for Python-only base classes.

The base=True flag allows you to create intermediate Python base classes
that provide shared functionality without appearing in the TypeDB schema.
"""

import type_bridge as tbg
from type_bridge import Integer, String, TypeFlags

# ========== USE CASE 1: Creating Python base classes with conflicting names ==========

print("=" * 70)
print("USE CASE 1: Python base class with conflicting name")
print("=" * 70)


# ✅ Now you can create a custom "Entity" base class!
class Entity(tbg.Entity):
    """Custom Python base class for shared functionality."""

    flags = TypeFlags(base=True)  # Won't appear in TypeDB schema

    def custom_method(self) -> str:
        """Shared method for all entities."""
        return f"I am a {self.get_type_name()}"


class Name(String):
    pass


class Age(Integer):
    pass


# Concrete entities inherit from custom Entity
class XX(Entity):
    flags = TypeFlags(type_name="xx")
    name: Name


class YY(XX):
    flags = TypeFlags(type_name="yy")
    age: Age


print("✅ Created custom 'Entity' base class with base=True")
print(f"   Entity.is_base() = {Entity.is_base()}")
print(f"   Entity.to_schema_definition() = {Entity.to_schema_definition()}")
print()

print("Schema for XX:")
print(f"  {XX.to_schema_definition()}")
print(f"  Supertype: {XX.get_supertype()}")
print()

print("Schema for YY:")
print(f"  {YY.to_schema_definition()}")
print(f"  Supertype: {YY.get_supertype()}")
print()

# The custom method works!
xx_instance = XX(name=Name("test"))
print(f"Custom method: {xx_instance.custom_method()}")
print()


# ========== USE CASE 2: Shared attributes in base class ==========

print("=" * 70)
print("USE CASE 2: Shared attributes via Python base class")
print("=" * 70)


class Timestamped(tbg.Entity):
    """Python base class providing timestamp functionality."""

    flags = TypeFlags(base=True)  # Python-only, not in TypeDB

    # This attribute will be inherited by all children
    created_at: Integer  # Could store Unix timestamp


class Person(Timestamped):
    flags = TypeFlags(type_name="person")
    name: Name


class Company(Timestamped):
    flags = TypeFlags(type_name="company")
    name: Name


print("Timestamped base class provides 'created_at' attribute")
print(f"  Person owns: {list(Person.get_owned_attributes().keys())}")
print(f"  Company owns: {list(Company.get_owned_attributes().keys())}")
print()

print("Schema generation (Timestamped doesn't appear):")
print(f"  Person: {Person.to_schema_definition()}")
print(f"  Company: {Company.to_schema_definition()}")
print()


# ========== USE CASE 3: Complex hierarchy with both base and non-base classes ==========

print("=" * 70)
print("USE CASE 3: Mixed hierarchy (base + abstract + concrete)")
print("=" * 70)


# Python-only base
class BaseEntity(tbg.Entity):
    flags = TypeFlags(base=True)

    def audit_log(self) -> str:
        return f"Auditing {self.get_type_name()}"


# TypeDB abstract entity
class LivingThing(BaseEntity):
    flags = TypeFlags(type_name="living_thing", abstract=True)
    name: Name


# Another Python-only base
class AuditedEntity(LivingThing):
    flags = TypeFlags(base=True)

    def get_audit_metadata(self) -> dict:
        return {"entity_type": self.get_type_name(), "audited": True}


# Concrete entity
class Animal(AuditedEntity):
    flags = TypeFlags(type_name="animal")
    age: Age


print(
    "Inheritance chain: Animal -> AuditedEntity(base) -> LivingThing(abstract) -> BaseEntity(base)"
)
print(f"  Animal.get_supertype() = {Animal.get_supertype()}")
print("  Skips both base classes, finds 'living_thing'")
print()

print("Schema for Animal:")
print(f"  {Animal.to_schema_definition()}")
print()

animal = Animal(name=Name("Lion"), age=Age(5))
print("Methods from base classes work:")
print(f"  audit_log(): {animal.audit_log()}")
print(f"  get_audit_metadata(): {animal.get_audit_metadata()}")
print()


# ========== Schema Manager Integration ==========

print("=" * 70)
print("SCHEMA MANAGER: base classes are filtered from schema")
print("=" * 70)

from type_bridge import Database, SchemaManager

# Create schema manager (don't actually connect)
db = Database(address="localhost:1729", database="demo")
schema_manager = SchemaManager(db)

# Register all classes (including base ones)
schema_manager.register(Entity, Timestamped, BaseEntity, LivingThing, AuditedEntity)
schema_manager.register(XX, YY, Person, Company, Animal)

# Generate schema - base classes are automatically filtered out
schema = schema_manager.generate_schema()

print("Generated TypeQL schema (base classes omitted):")
print("-" * 70)
print(schema)
print("-" * 70)
print()

print("✅ Notice:")
print("  - 'entity', 'timestamped', 'base_entity', 'audited_entity' DO NOT appear")
print("  - 'living_thing' DOES appear (it's abstract but not base)")
print("  - All concrete entities appear with correct hierarchy")
print()


# ========== KEY TAKEAWAY ==========

print("=" * 70)
print("KEY TAKEAWAY")
print("=" * 70)
print("Use base=True for Python-only base classes that:")
print("  1. Provide shared methods/functionality")
print("  2. Need to use conflicting names (like 'Entity', 'Relation')")
print("  3. Should NOT appear in TypeDB schema")
print()
print("Children of base classes:")
print("  - Inherit Python attributes and methods")
print("  - Skip base classes in TypeDB hierarchy (get_supertype())")
print("  - Generate schema without base class references")
print("=" * 70)

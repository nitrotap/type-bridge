"""Example: Implicit Flags - No need to explicitly set empty flags.

This example demonstrates that you don't need to write `flags = EntityFlags()`
for every entity/relation. TypeBridge automatically creates default flags for
each class that doesn't explicitly set them.

This makes the code cleaner and more concise!
"""

from type_bridge import Entity, EntityFlags, Flag, Integer, Key, Relation, Role, String


# Define attributes
class Name(String):
    pass


class Age(Integer):
    pass


class Position(String):
    pass


# Example 1: Simple entities without explicit flags
print("=" * 80)
print("Example 1: Entities without explicit flags")
print("=" * 80)
print()


class Person(Entity):
    # No flags needed! Automatically gets EntityFlags() with CLASS_NAME default
    name: Name = Flag(Key)
    age: Age


class Company(Entity):
    # No flags needed!
    name: Name = Flag(Key)


print(f"Person type name: {Person.get_type_name()}")  # → "Person"
print(f"Company type name: {Company.get_type_name()}")  # → "Company"
print()
print("Person schema:")
print(Person.to_schema_definition())
print()
print("Company schema:")
print(Company.to_schema_definition())
print()


# Example 2: Inheritance with implicit flags
print("=" * 80)
print("Example 2: Inheritance without explicit flags")
print("=" * 80)
print()


# Python base class (won't appear in TypeDB schema)
class BaseEntity(Entity):
    flags = EntityFlags(base=True)  # This one needs explicit base=True


class Employee(BaseEntity):
    # No flags needed! Gets fresh EntityFlags() automatically
    name: Name = Flag(Key)
    age: Age


class Manager(Employee):
    # No flags needed! Gets fresh EntityFlags() automatically
    pass


print(f"Employee type name: {Employee.get_type_name()}")  # → "Employee"
print(f"Manager type name: {Manager.get_type_name()}")  # → "Manager"
print(f"Manager supertype: {Manager.get_supertype()}")  # → "Employee"
print()
print("Employee schema:")
print(Employee.to_schema_definition())
print()
print("Manager schema:")
print(Manager.to_schema_definition())
print()


# Example 3: Relations without explicit flags
print("=" * 80)
print("Example 3: Relations without explicit flags")
print("=" * 80)
print()


class Employment(Relation):
    # No flags needed!
    employee: Role[Person] = Role("employee", Person)
    employer: Role[Company] = Role("employer", Company)
    position: Position


print(f"Employment type name: {Employment.get_type_name()}")  # → "Employment"
print()
print("Employment schema:")
print(Employment.to_schema_definition())
print()


# Example 4: When you DO need explicit flags
print("=" * 80)
print("Example 4: When explicit flags are needed")
print("=" * 80)
print()


class AbstractPerson(Entity):
    flags = EntityFlags(abstract=True)  # Need explicit flag for abstract
    name: Name


class SpecialPerson(Entity):
    flags = EntityFlags(type_name="special_person")  # Need explicit type_name override
    name: Name


print(f"AbstractPerson is abstract: {AbstractPerson.is_abstract()}")
print(f"SpecialPerson type name: {SpecialPerson.get_type_name()}")  # → "special_person"
print()


# Summary
print("=" * 80)
print("Summary: When to use explicit flags")
print("=" * 80)
print()
print("✓ NO explicit flags needed for:")
print("  • Simple entities/relations (uses CLASS_NAME default)")
print("  • Child classes in inheritance hierarchies")
print("  • Most common use cases")
print()
print("✗ Explicit flags needed for:")
print("  • base=True (Python-only base classes)")
print("  • abstract=True (abstract entities/relations)")
print("  • Custom type_name (override CLASS_NAME default)")
print("  • Custom case formatting (LOWERCASE, SNAKE_CASE)")
print()
print("=" * 80)

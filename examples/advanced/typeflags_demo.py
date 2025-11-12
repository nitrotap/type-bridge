"""Example: TypeFlags - Unified flags for Entities and Relations.

This example demonstrates the new TypeFlags class that replaces both
EntityFlags and RelationFlags with a single, unified API.

Key changes:
- Use TypeFlags instead of EntityFlags or RelationFlags
- Use 'name' parameter instead of 'type_name'
"""

from type_bridge import Entity, Flag, Integer, Key, Relation, Role, String, TypeFlags, TypeNameCase


# Define attributes
class Name(String):
    pass


class Age(Integer):
    pass


class Position(String):
    pass


print("=" * 80)
print("TypeFlags - Unified Flags for Entities and Relations")
print("=" * 80)
print()

# Example 1: Entity with TypeFlags
print("Example 1: Entity with TypeFlags")
print("-" * 80)


class Person(Entity):
    flags = TypeFlags(name="person")  # Use 'name' instead of 'type_name'
    name: Name = Flag(Key)
    age: Age


print(f"Person type name: {Person.get_type_name()}")  # → "person"
print()
print("Schema:")
print(Person.to_schema_definition())
print()

# Example 2: Relation with TypeFlags
print("Example 2: Relation with TypeFlags")
print("-" * 80)


class Company(Entity):
    flags = TypeFlags(name="company")
    name: Name = Flag(Key)


class Employment(Relation):
    flags = TypeFlags(name="employment")  # Same TypeFlags class!
    employee: Role[Person] = Role("employee", Person)
    employer: Role[Company] = Role("employer", Company)
    position: Position


print(f"Employment type name: {Employment.get_type_name()}")  # → "employment"
print()
print("Schema:")
print(Employment.to_schema_definition())
print()

# Example 3: Using case formatting
print("Example 3: Case formatting with TypeFlags")
print("-" * 80)


class PersonData(Entity):
    flags = TypeFlags(case=TypeNameCase.SNAKE_CASE)  # No 'name', uses CLASS_NAME → snake_case
    name: Name = Flag(Key)


class CompanyData(Entity):
    flags = TypeFlags()  # No 'name', uses CLASS_NAME default
    name: Name = Flag(Key)


print(f"PersonData type name: {PersonData.get_type_name()}")  # → "person_data"
print(f"CompanyData type name: {CompanyData.get_type_name()}")  # → "CompanyData"
print()

# Example 4: Abstract and base flags
print("Example 4: Abstract and base flags")
print("-" * 80)


class AbstractEntity(Entity):
    flags = TypeFlags(abstract=True, name="abstract_entity")
    name: Name


class BaseEntity(Entity):
    flags = TypeFlags(base=True)  # Python-only base class


print(f"AbstractEntity is abstract: {AbstractEntity.is_abstract()}")
print(f"BaseEntity is base: {BaseEntity.is_base()}")
print(
    f"BaseEntity schema: {BaseEntity.to_schema_definition()}"
)  # → None (base classes don't generate schema)
print()

# Example 5: Backward compatibility
print("Example 5: Backward Compatibility")
print("-" * 80)
print("Old code using EntityFlags still works:")


from type_bridge import EntityFlags, RelationFlags


class OldPerson(Entity):
    flags = EntityFlags(type_name="old_person")  # Old API still works!
    name: Name = Flag(Key)


class OldEmployment(Relation):
    flags = RelationFlags(type_name="old_employment")  # Old API still works!
    employee: Role[OldPerson] = Role("employee", OldPerson)
    employer: Role[Company] = Role("employer", Company)


print(f"✓ EntityFlags with type_name: {OldPerson.get_type_name()}")
print(f"✓ RelationFlags with type_name: {OldEmployment.get_type_name()}")
print()

# Summary
print("=" * 80)
print("Summary")
print("=" * 80)
print()
print("NEW API (Recommended):")
print("  • Use TypeFlags for both entities and relations")
print("  • Use 'name' parameter instead of 'type_name'")
print("  • Example: flags = TypeFlags(name='person')")
print()
print("OLD API (Still Works):")
print("  • EntityFlags and RelationFlags are aliases to TypeFlags")
print("  • 'type_name' parameter still works for backward compatibility")
print("  • Example: flags = EntityFlags(type_name='person')")
print()
print("=" * 80)

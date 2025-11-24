"""Demonstration of built-in type name collision edge case and its fix.

This example shows what happens when you try to create classes with names
that conflict with TypeDB's built-in types.
"""

import type_bridge as tbg
from type_bridge import String, TypeFlags

# ❌ EDGE CASE 1: Trying to create a custom Entity base class without proper naming
# This would fail because the class name "Entity" defaults to name="entity"
# which conflicts with TypeDB's built-in "entity" type

try:

    class Entity(tbg.Entity):
        """Custom entity base class - FAILS!"""

        pass

except ValueError as e:
    print("❌ Error caught when creating class named 'Entity':")
    print(f"   {e}")
    print()


# ✅ SOLUTION 1: Use an explicit, non-conflicting type name with abstract=True
class BaseEntity(tbg.Entity):
    """Custom entity base class - WORKS!"""

    flags: TypeFlags = TypeFlags(abstract=True, name="base_entity")


print("✅ Successfully created BaseEntity with name='base_entity'")
print()


# ❌ EDGE CASE 2: Multi-level inheritance with conflicting intermediate class name
try:

    class Relation(tbg.Relation):
        """Custom relation base - FAILS!"""

        pass

except ValueError as e:
    print("❌ Error caught when creating class named 'Relation':")
    print(f"   {e}")
    print()


# ✅ SOLUTION 2: Safe multi-level inheritance with proper naming
class Name(String):
    pass


class Animal(tbg.Entity):
    """Abstract base - safe name"""

    flags: TypeFlags = TypeFlags(abstract=True, name="animal")
    name: Name


class Mammal(Animal):
    """Another level of inheritance - still safe"""

    flags: TypeFlags = TypeFlags(abstract=True, name="mammal")


class Dog(Mammal):
    """Concrete entity - works perfectly"""

    flags: TypeFlags = TypeFlags(name="dog")


print("✅ Successfully created multi-level inheritance chain:")
print(f"   Dog -> {Dog.get_supertype()} -> {Mammal.get_supertype()}")
print()

# Schema generation shows proper inheritance
print("Schema for Dog:")
print(Dog.to_schema_definition())
print()


# ❌ EDGE CASE 3: Attribute with conflicting name
try:

    class Attribute(String):
        """Attribute named 'Attribute' - FAILS!"""

        pass

except ValueError as e:
    print("❌ Error caught when creating attribute class named 'Attribute':")
    print(f"   {e}")
    print()


# ✅ Key Takeaway
print("=" * 60)
print("KEY TAKEAWAY:")
print("=" * 60)
print("TypeDB has built-in types: 'thing', 'entity', 'relation', 'attribute'")
print()
print("When creating custom classes:")
print("1. Avoid class names that match these built-ins")
print("2. Use explicit name in TypeFlags")
print("3. For intermediate base classes, use abstract=True")
print()
print("The library now automatically validates and prevents conflicts!")
print("=" * 60)

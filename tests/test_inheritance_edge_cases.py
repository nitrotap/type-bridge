"""Tests for inheritance edge cases and built-in type name collisions."""

import pytest

import type_bridge as tbg
from type_bridge import EntityFlags, Integer, RelationFlags, String


class TestInheritanceEdgeCases:
    """Test edge cases with multi-level inheritance and naming collisions."""

    def test_builtin_type_name_collision_entity(self):
        """Test that using 'entity' as a type name raises an error."""

        with pytest.raises(ValueError, match="conflicts with TypeDB built-in type"):

            class BadEntity(tbg.Entity):
                flags = EntityFlags(type_name="entity")  # Explicit collision

    def test_builtin_type_name_collision_relation(self):
        """Test that using 'relation' as a type name raises an error."""

        with pytest.raises(ValueError, match="conflicts with TypeDB built-in type"):

            class BadRelation(tbg.Relation):
                flags = RelationFlags(type_name="relation")  # Explicit collision

    def test_builtin_type_name_collision_attribute(self):
        """Test that using 'attribute' as an attribute name raises an error."""

        with pytest.raises(ValueError, match="conflicts with TypeDB built-in type"):
            # Class name directly conflicts (will lowercase to "attribute")
            class Attribute(String):  # type: ignore[misc]
                pass

    def test_builtin_type_name_collision_thing(self):
        """Test that using 'thing' as a type name raises an error."""

        with pytest.raises(ValueError, match="conflicts with TypeDB built-in type"):

            class Thing(tbg.Entity):
                flags = EntityFlags(type_name="thing")  # Explicit collision

    def test_intermediate_base_class_without_flags(self):
        """Test multi-level inheritance with intermediate class."""
        # This is the edge case: creating a custom base class that inherits from Entity
        # Should work if we use abstract=True

        class BaseEntity(tbg.Entity):
            flags = EntityFlags(abstract=True, type_name="base_entity")

        class Name(String):
            pass

        class ConcreteEntity(BaseEntity):
            flags = EntityFlags(type_name="concrete_entity")
            name: Name

        # Should generate correct schema
        schema = ConcreteEntity.to_schema_definition()
        assert "entity concrete_entity sub base_entity" in schema
        assert "owns name" in schema

        # Base entity should also have correct schema
        base_schema = BaseEntity.to_schema_definition()
        assert "entity base_entity, abstract" in base_schema

    def test_intermediate_base_class_name_default(self):
        """Test that intermediate class with default name gets validated."""

        # This should raise an error because the class name is "Entity"
        # which would default to type_name="entity" (collision)
        with pytest.raises(ValueError, match="'entity'.*conflicts with TypeDB built-in"):
            # Intentionally name the class "Entity" to trigger the edge case
            class Entity(tbg.Entity):  # type: ignore[no-redef]
                pass  # No flags - would default to type_name="entity"

    def test_multi_level_inheritance_chain(self):
        """Test deep inheritance chain works correctly."""

        class Animal(tbg.Entity):
            flags = EntityFlags(abstract=True, type_name="animal")

        class Mammal(Animal):
            flags = EntityFlags(abstract=True, type_name="mammal")

        class Name(String):
            pass

        class Dog(Mammal):
            flags = EntityFlags(type_name="dog")
            name: Name

        # Check supertype chain
        assert Dog.get_supertype() == "mammal"
        assert Mammal.get_supertype() == "animal"
        assert Animal.get_supertype() is None

        # Check schema generation
        dog_schema = Dog.to_schema_definition()
        assert "entity dog sub mammal" in dog_schema

        mammal_schema = Mammal.to_schema_definition()
        assert "entity mammal sub animal" in mammal_schema
        assert "abstract" in mammal_schema

        animal_schema = Animal.to_schema_definition()
        assert "entity animal, abstract" in animal_schema

    def test_implicit_type_name_with_safe_class_name(self):
        """Test that implicit type names work when class name is safe."""

        class Name(String):
            pass

        class Person(tbg.Entity):
            # No explicit type_name - should use "person" (safe)
            name: Name

        assert Person.get_type_name() == "person"
        schema = Person.to_schema_definition()
        assert "entity person" in schema

    def test_relation_inheritance_edge_cases(self):
        """Test relation inheritance with built-in name collision."""

        with pytest.raises(ValueError, match="'relation'.*conflicts with TypeDB built-in"):

            class Relation(tbg.Relation):  # type: ignore[no-redef]
                pass  # Would default to type_name="relation"

    def test_case_sensitivity_in_builtin_check(self):
        """Test that built-in type check is case-insensitive to match TypeDB behavior."""

        class Name(String):
            pass

        # TypeDB type names are case-insensitive in the validation (type_name.lower())
        # So "ENTITY" conflicts with "entity"
        with pytest.raises(ValueError, match="conflicts with TypeDB built-in"):

            class ENTITY(tbg.Entity):
                flags = EntityFlags(type_name="ENTITY")  # Still conflicts (case-insensitive)
                name: Name

        # But these should be allowed (different names)
        class EntityType(tbg.Entity):
            flags = EntityFlags(type_name="entity_type")  # Has suffix - safe
            name: Name

        # Should not raise errors
        assert EntityType.get_type_name() == "entity_type"


class TestInheritanceAttributePropagation:
    """Test that attributes are inherited correctly."""

    def test_child_inherits_parent_attributes(self):
        """Test that child entities inherit parent attributes via Python's MRO."""
        # In TypeDB, inheritance means the child is a subtype of the parent
        # In Python, child classes inherit annotations from parents via get_type_hints()
        # This is correct ORM behavior: a Dog IS an Animal, so it has animal attributes

        class Name(String):
            pass

        class Age(Integer):
            pass

        class Animal(tbg.Entity):
            flags = EntityFlags(abstract=True, type_name="animal")
            name: Name

        class Dog(Animal):
            flags = EntityFlags(type_name="dog")
            age: Age

        # Check owned attributes
        animal_attrs = Animal.get_owned_attributes()
        dog_attrs = Dog.get_owned_attributes()

        assert "name" in animal_attrs
        assert "age" in dog_attrs
        # Dog DOES inherit "name" from Animal via Python's MRO
        assert "name" in dog_attrs

        # Check schema generation
        animal_schema = Animal.to_schema_definition()
        assert "owns name" in animal_schema

        dog_schema = Dog.to_schema_definition()
        assert "entity dog sub animal" in dog_schema
        assert "owns age" in dog_schema
        # Dog schema DOES include "name" because get_owned_attributes() includes it
        assert "owns name" in dog_schema

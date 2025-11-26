"""Unit tests for inherited attribute filtering.

Tests that get_all_attributes() correctly includes inherited attributes,
and that query generation uses get_all_attributes() for dictionary-based filters.

Bug reference: Filters on inherited attributes were silently ignored because
get_owned_attributes() only returns directly-owned attributes.
"""

from type_bridge import Entity, Flag, Integer, Key, String, TypeFlags
from type_bridge.query import QueryBuilder


# Test model hierarchy
class LivingName(String):
    """Name attribute for Living entities."""

    pass


class LivingAge(Integer):
    """Age attribute for Living entities."""

    pass


class Living(Entity):
    """Abstract base entity with name key."""

    flags = TypeFlags(abstract=True, name="living")
    name: LivingName = Flag(Key)


class Animal(Living):
    """Abstract animal entity inheriting from Living."""

    flags = TypeFlags(abstract=True, name="animal")


class Dog(Animal):
    """Concrete Dog entity - inherits name from Living."""

    flags = TypeFlags(name="dog")
    age: LivingAge | None = None


class Cat(Animal):
    """Concrete Cat entity - inherits name from Living."""

    flags = TypeFlags(name="cat")


class TestGetAllAttributesVsGetOwnedAttributes:
    """Test that get_all_attributes includes inherited attributes."""

    def test_get_owned_attributes_excludes_inherited(self):
        """get_owned_attributes() should only return directly-owned attributes."""
        # Living owns 'name'
        living_attrs = Living.get_owned_attributes()
        assert "name" in living_attrs

        # Animal inherits 'name' but doesn't own any new attributes
        animal_attrs = Animal.get_owned_attributes()
        assert "name" not in animal_attrs
        assert len(animal_attrs) == 0

        # Dog inherits 'name' from Living and owns 'age'
        dog_attrs = Dog.get_owned_attributes()
        assert "name" not in dog_attrs  # Inherited, not owned
        assert "age" in dog_attrs  # Directly owned

        # Cat inherits 'name' and owns nothing
        cat_attrs = Cat.get_owned_attributes()
        assert "name" not in cat_attrs
        assert len(cat_attrs) == 0

    def test_get_all_attributes_includes_inherited(self):
        """get_all_attributes() should return all attributes including inherited."""
        # Living owns 'name'
        living_all = Living.get_all_attributes()
        assert "name" in living_all

        # Animal inherits 'name'
        animal_all = Animal.get_all_attributes()
        assert "name" in animal_all

        # Dog inherits 'name' and owns 'age'
        dog_all = Dog.get_all_attributes()
        assert "name" in dog_all  # Inherited
        assert "age" in dog_all  # Owned

        # Cat inherits 'name'
        cat_all = Cat.get_all_attributes()
        assert "name" in cat_all

    def test_get_all_attributes_mro_order(self):
        """get_all_attributes() should traverse MRO in correct order."""

        class ParentId(String):
            pass

        class ChildId(String):
            pass

        class ParentEntity(Entity):
            flags = TypeFlags(abstract=True, name="parent_mro")
            parent_id: ParentId = Flag(Key)

        class ChildEntity(ParentEntity):
            flags = TypeFlags(name="child_mro")
            child_id: ChildId

        child_all = ChildEntity.get_all_attributes()
        # Should have both parent and child attributes
        assert "parent_id" in child_all
        assert "child_id" in child_all
        assert child_all["parent_id"].typ == ParentId
        assert child_all["child_id"].typ == ChildId


class TestQueryBuilderMatchEntity:
    """Test that QueryBuilder.match_entity uses get_all_attributes for filters."""

    def test_match_entity_with_inherited_attribute_filter(self):
        """match_entity should include inherited attribute in TypeQL query."""
        # Filter by 'name' which is inherited from Living
        query = QueryBuilder.match_entity(Dog, var="$d", name=LivingName("Buddy"))

        query_str = query.build()

        # Should include the filter on inherited 'name' attribute
        assert "$d isa dog" in query_str
        assert 'has LivingName "Buddy"' in query_str

    def test_match_entity_with_owned_attribute_filter(self):
        """match_entity should include owned attribute in TypeQL query."""
        # Filter by 'age' which is directly owned by Dog
        query = QueryBuilder.match_entity(Dog, var="$d", age=LivingAge(5))

        query_str = query.build()

        assert "$d isa dog" in query_str
        assert "has LivingAge 5" in query_str

    def test_match_entity_with_both_inherited_and_owned_filters(self):
        """match_entity should handle both inherited and owned attributes."""
        query = QueryBuilder.match_entity(Dog, var="$d", name=LivingName("Buddy"), age=LivingAge(3))

        query_str = query.build()

        assert "$d isa dog" in query_str
        assert 'has LivingName "Buddy"' in query_str
        assert "has LivingAge 3" in query_str

    def test_match_entity_unknown_attribute_ignored(self):
        """match_entity should ignore attributes not in get_all_attributes."""
        # 'unknown_field' is not an attribute of Dog
        query = QueryBuilder.match_entity(Dog, var="$d", unknown_field="value")

        query_str = query.build()

        # Should not include the unknown field, just the base match
        assert "$d isa dog" in query_str
        assert "unknown_field" not in query_str


class TestDeepInheritanceChain:
    """Test inherited attribute filtering with deeper inheritance chains."""

    def test_three_level_inheritance(self):
        """Test that attributes from grandparent are accessible."""

        class GrandparentName(String):
            pass

        class ParentAge(Integer):
            pass

        class ChildScore(Integer):
            pass

        class Grandparent(Entity):
            flags = TypeFlags(abstract=True, name="grandparent")
            name: GrandparentName = Flag(Key)

        class Parent(Grandparent):
            flags = TypeFlags(abstract=True, name="parent")
            age: ParentAge

        class Child(Parent):
            flags = TypeFlags(name="child")
            score: ChildScore

        # Child should have all three attributes
        child_all = Child.get_all_attributes()
        assert "name" in child_all  # From Grandparent
        assert "age" in child_all  # From Parent
        assert "score" in child_all  # Own attribute

        # get_owned_attributes should only have 'score'
        child_owned = Child.get_owned_attributes()
        assert "name" not in child_owned
        assert "age" not in child_owned
        assert "score" in child_owned

    def test_query_with_grandparent_attribute(self):
        """Test that query generation works with grandparent attributes."""

        class GrandparentId(String):
            pass

        class Grandparent(Entity):
            flags = TypeFlags(abstract=True, name="gp")
            gp_id: GrandparentId = Flag(Key)

        class Parent(Grandparent):
            flags = TypeFlags(abstract=True, name="par")

        class Child(Parent):
            flags = TypeFlags(name="ch")

        query = QueryBuilder.match_entity(Child, var="$c", gp_id=GrandparentId("ID123"))

        query_str = query.build()

        assert "$c isa ch" in query_str
        assert 'has GrandparentId "ID123"' in query_str

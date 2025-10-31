"""Example demonstrating the new Attribute-based API with Card cardinality."""

from typing import ClassVar

from type_bridge import (
    Boolean,
    Card,
    Double,
    Entity,
    EntityFlags,
    Flag,
    Integer,
    Key,
    Relation,
    RelationFlags,
    Role,
    String,
)


# Step 1: Define attribute types (these are base attributes that can be owned)
class Name(String):
    """Name attribute - a string."""

    pass


class Email(String):
    """Email attribute - a string."""

    pass


class Age(Integer):
    """Age attribute - a long integer."""

    pass


class Salary(Integer):
    """Salary attribute - a long integer."""

    pass


class Position(String):
    """Position/title attribute - a string."""

    pass


class Industry(String):
    """Industry attribute - a string."""

    pass


class Score(Double):
    """Score attribute - a double."""

    pass


class IsActive(Boolean):
    """Active status attribute - a boolean."""

    pass


# Step 2: Define entities that OWN these attributes with generic type annotations
class Person(Entity):
    """Person entity with cardinality and key annotations."""

    flags = EntityFlags(type_name="person")

    name: Name = Flag(Key)  # @key (implies @card(1..1)) - exactly one, marked as key
    age: Age | None  # @card(0..1) - zero or one (optional)
    email: Email  # @card(1..1) - exactly one (default)
    score: Score  # @card(1..1) - exactly one (default)


class Company(Entity):
    """Company entity with cardinality annotations."""

    flags = EntityFlags(type_name="company")

    name: Name = Flag(Key)  # @key (implies @card(1..1)) - exactly one, marked as key
    industry: list[Industry] = Flag(Card(1, 5))  # @card(1..5) - one to five industries


# Step 3: Define relations that OWN attributes
class Employment(Relation):
    """Employment relation between person and company."""

    flags = RelationFlags(type_name="employment")

    # Roles
    employee: ClassVar[Role] = Role("employee", Person)
    employer: ClassVar[Role] = Role("employer", Company)

    # Owned attributes with cardinality
    position: Position  # @card(1..1) - exactly one (default)
    salary: Salary | None  # @card(0..1) - zero or one (optional)


def demonstrate_schema_generation():
    """Demonstrate schema generation with the new API."""
    print("=" * 80)
    print("Attribute Schema Definitions")
    print("=" * 80)

    # Generate attribute schemas
    attributes = [Name, Email, Age, Salary, Position, Industry, Score, IsActive]

    for attr_class in attributes:
        print(attr_class.to_schema_definition())

    print()
    print("=" * 80)
    print("Entity Schema Definitions")
    print("=" * 80)

    # Generate entity schemas
    print(Person.to_schema_definition())
    print()
    print(Company.to_schema_definition())
    print()

    print("=" * 80)
    print("Relation Schema Definitions")
    print("=" * 80)

    # Generate relation schema
    print(Employment.to_schema_definition())
    print()


def demonstrate_instance_creation():
    """Demonstrate creating instances with the new API."""
    print("=" * 80)
    print("Creating Entity Instances")
    print("=" * 80)

    # Two ways to create person instances:

    # Style 1: Attribute instances (fully type-safe, zero pyright errors)
    alice = Person(
        name=Name("Alice Johnson"), age=Age(30), email=Email("alice@example.com"), score=Score(95.5)
    )
    print(f"Created (attribute instances): {alice}")

    # Style 2: Raw values (convenient, Pydantic handles conversion)
    # Note: Works perfectly at runtime, may show pyright warnings
    bob = Person(name="Bob Smith", age=28, email="bob@example.com", score=87.3) # pyright: ignore [reportArgumentType]
    print(f"Created (raw values): {bob}")

    # Create company instance
    techcorp = Company(
        name=Name("TechCorp"),
        industry=[
            Industry("Technology"),
            Industry("Software"),
            Industry("AI"),
        ],  # List for Range[1,5]
    )
    print(f"Created: {techcorp}")

    print()
    print("=" * 80)
    print("Insert Queries")
    print("=" * 80)

    # Generate insert queries
    print("Alice insert:")
    print(alice.to_insert_query())
    print()

    print("Bob insert:")
    print(bob.to_insert_query())
    print()

    print("TechCorp insert:")
    print(techcorp.to_insert_query())
    print()


def demonstrate_attribute_introspection():
    """Demonstrate attribute introspection."""
    print("=" * 80)
    print("Attribute Introspection")
    print("=" * 80)

    print("Person owns:")
    for field_name, attr_info in Person.get_owned_attributes().items():
        attr_class = attr_info.typ
        flags = attr_info.flags
        attr_name = attr_class.get_attribute_name()
        value_type = attr_class.get_value_type()
        annotations = " ".join(flags.to_typeql_annotations())
        annotations_str = f" {annotations}" if annotations else ""
        print(f"  - {field_name} ({attr_name}): {value_type}{annotations_str}")

    print()

    print("Company owns:")
    for field_name, attr_info in Company.get_owned_attributes().items():
        attr_class = attr_info.typ
        flags = attr_info.flags
        attr_name = attr_class.get_attribute_name()
        value_type = attr_class.get_value_type()
        annotations = " ".join(flags.to_typeql_annotations())
        annotations_str = f" {annotations}" if annotations else ""
        print(f"  - {field_name} ({attr_name}): {value_type}{annotations_str}")

    print()

    print("Employment owns:")
    for field_name, attr_info in Employment.get_owned_attributes().items():
        attr_class = attr_info.typ
        flags = attr_info.flags
        attr_name = attr_class.get_attribute_name()
        value_type = attr_class.get_value_type()
        annotations = " ".join(flags.to_typeql_annotations())
        annotations_str = f" {annotations}" if annotations else ""
        print(f"  - {field_name} ({attr_name}): {value_type}{annotations_str}")

    print()


def demonstrate_full_schema():
    """Demonstrate full schema generation."""
    print("=" * 80)
    print("Complete TypeDB Schema")
    print("=" * 80)
    print()
    print("define")
    print()

    # First, define all attributes
    print("# Attributes")
    attributes = [Name, Email, Age, Salary, Position, Industry, Score, IsActive]
    for attr_class in attributes:
        print(attr_class.to_schema_definition())
    print()

    # Then, define entities
    print("# Entities")
    print(Person.to_schema_definition())
    print()
    print(Company.to_schema_definition())
    print()

    # Finally, define relations and role players
    print("# Relations")
    print(Employment.to_schema_definition())
    print()

    # Role player definitions
    print("# Role Players")
    for role_name, role in Employment._roles.items():
        relation_name = Employment.get_type_name()
        print(f"{role.player_type} plays {relation_name}:{role.role_name};")

    print()


def main():
    """Run all demonstrations."""
    print()
    print("TypeBridge - New Attribute-Based API")
    print("=" * 80)
    print()

    demonstrate_schema_generation()
    print()

    demonstrate_instance_creation()
    print()

    demonstrate_attribute_introspection()
    print()

    demonstrate_full_schema()

    print("=" * 80)
    print("Demonstration Complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()

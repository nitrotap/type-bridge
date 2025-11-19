"""Example demonstrating Pydantic integration features."""

from type_bridge import (
    Entity,
    Flag,
    Integer,
    Key,
    Relation,
    Role,
    String,
    TypeFlags,
)


# Define attribute types
class Name(String):
    pass


class Email(String):
    pass


class Age(Integer):
    pass


class Salary(Integer):
    pass


# Define entities with Pydantic validation
class Person(Entity):
    """Person entity with Pydantic validation."""

    flags = TypeFlags(type_name="person")
    name: Name = Flag(Key)  # Required key field
    email: Email | None = None  # Optional with default
    age: Age = Age(0)  # Default value (still required unless explicitly Optional)


class Company(Entity):
    """Company entity."""

    flags = TypeFlags(type_name="company")
    name: Name = Flag(Key)  # Required key field


class Employment(Relation):
    """Employment relation."""

    flags = TypeFlags(type_name="employment")

    employee: Role[Person] = Role("employee", Person)
    employer: Role[Company] = Role("employer", Company)

    salary: Salary | None = None  # Optional field with default


def demonstrate_validation():
    """Demonstrate Pydantic validation."""
    print("=" * 80)
    print("Pydantic Validation")
    print("=" * 80)

    # Valid creation
    alice = Person(name=Name("Alice Johnson"), email=Email("alice@example.com"), age=Age(30))
    print(f"Created: {alice}")

    # Type coercion (string to int)
    bob = Person(name=Name("Bob Smith"), age=Age(25))
    print(f"Created with coercion: {bob}")
    print(f"  age type: {type(bob.age)}")

    # Default values
    charlie = Person(name=Name("Charlie Brown"))
    print(f"Created with defaults: {charlie}")
    print(f"  age default: {charlie.age}")

    # Validation on assignment
    alice.age = Age(31)
    print(f"Updated age: {alice.age}")

    print()


def demonstrate_serialization():
    """Demonstrate Pydantic serialization."""
    print("=" * 80)
    print("Pydantic Serialization")
    print("=" * 80)

    alice = Person(name=Name("Alice Johnson"), email=Email("alice@example.com"), age=Age(30))

    # Serialize to dict
    alice_dict = alice.model_dump()
    print(f"As dict: {alice_dict}")

    # Serialize to JSON
    alice_json = alice.model_dump_json(indent=2)
    print(f"As JSON:\n{alice_json}")

    print()


def demonstrate_deserialization():
    """Demonstrate Pydantic deserialization."""
    print("=" * 80)
    print("Pydantic Deserialization")
    print("=" * 80)

    # Deserialize from dict
    person_data = {"name": "Bob Smith", "email": "bob@example.com", "age": 25}
    bob = Person(**person_data)
    print(f"From dict: {bob}")

    # Deserialize from JSON
    json_data = '{"name": "Charlie Brown", "email": "charlie@example.com", "age": 35}'
    charlie = Person.model_validate_json(json_data)
    print(f"From JSON: {charlie}")

    print()


def demonstrate_model_copy():
    """Demonstrate Pydantic model copy."""
    print("=" * 80)
    print("Pydantic Model Copy")
    print("=" * 80)

    alice = Person(name=Name("Alice Johnson"), email=Email("alice@example.com"), age=Age(30))
    print(f"Original: {alice}")

    # Create a copy with updates
    alice_older = alice.model_copy(update={"age": Age(31)})
    print(f"Copy with update: {alice_older}")
    print(f"Original unchanged: age={alice.age}")

    # Deep copy
    alice_clone = alice.model_copy(deep=True)
    print(f"Deep copy: {alice_clone}")

    print()


def demonstrate_typedb_operations():
    """Demonstrate that TypeDB operations still work with Pydantic."""
    print("=" * 80)
    print("TypeDB Operations with Pydantic")
    print("=" * 80)

    # Create entities
    alice = Person(name=Name("Alice Johnson"), email=Email("alice@example.com"), age=Age(30))
    techcorp = Company(name=Name("TechCorp"))

    # Generate TypeDB insert queries
    print("Insert queries:")
    print(f"  {alice.to_insert_query()}")
    print(f"  {techcorp.to_insert_query()}")

    # Schema generation still works
    print()
    print("Schema definitions:")
    print(Person.to_schema_definition())
    print()
    print(Company.to_schema_definition())

    print()


def demonstrate_combined_features():
    """Demonstrate combining Pydantic and TypeDB features."""
    print("=" * 80)
    print("Combined Pydantic + TypeDB Features")
    print("=" * 80)

    # 1. Create from JSON (Pydantic)
    json_data = '{"name": "Alice Johnson", "email": "alice@example.com", "age": 30}'
    alice = Person.model_validate_json(json_data)
    print(f"1. Created from JSON: {alice}")

    # 2. Validate and modify (Pydantic)
    alice.age = Age(31)
    print(f"2. Updated age: {alice.age}")

    # 3. Generate TypeDB insert query (TypeDB)
    insert_query = alice.to_insert_query()
    print(f"3. TypeDB insert: {insert_query}")

    # 4. Serialize back to JSON (Pydantic)
    json_output = alice.model_dump_json()
    print(f"4. Back to JSON: {json_output}")

    print()


def main():
    """Run all demonstrations."""
    print()
    print("TypeBridge - Pydantic Integration Features")
    print("=" * 80)
    print()

    demonstrate_validation()
    demonstrate_serialization()
    demonstrate_deserialization()
    demonstrate_model_copy()
    demonstrate_typedb_operations()
    demonstrate_combined_features()

    print("=" * 80)
    print("Demonstration Complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()

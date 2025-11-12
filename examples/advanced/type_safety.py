"""Demonstration of type safety improvements with Generic managers.

This example shows how the generic EntityManager[E] and RelationManager[R]
provide full type safety and IDE autocomplete support.
"""

from type_bridge import (
    Database,
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


# Define attribute types
class Name(String):
    pass


class Age(Integer):
    pass


class Email(String):
    pass


class Position(String):
    pass


class Salary(Integer):
    pass


# Define entity types
class Person(Entity):
    flags = EntityFlags(type_name="person")

    name: Name = Flag(Key)
    age: Age
    email: Email


class Company(Entity):
    flags = EntityFlags(type_name="company")

    name: Name = Flag(Key)


# Define relation type
class Employment(Relation):
    flags = RelationFlags(type_name="employment")

    employee: Role[Person] = Role("employee", Person)
    employer: Role[Company] = Role("employer", Company)

    position: Position
    salary: Salary | None = None


def demonstrate_type_safety():
    """Demonstrate type safety features."""
    db = Database(address="localhost:1729", database="type_safety_demo")
    db.connect()

    # Clean slate
    if db.database_exists():
        db.delete_database()
    db.create_database()

    # Define schema
    schema = """
    define

    attribute name, value string;
    attribute age, value integer;
    attribute email, value string;
    attribute position, value string;
    attribute salary, value integer;

    entity person,
        owns name @key,
        owns age,
        owns email;

    entity company,
        owns name @key;

    relation employment,
        relates employee,
        relates employer,
        owns position,
        owns salary @card(0..1);

    person plays employment:employee;
    company plays employment:employer;
    """

    db.execute_query(schema, "schema")

    print("=" * 70)
    print("Type Safety Demonstration")
    print("=" * 70)

    # 1. Type-safe entity creation
    print("\n1. Creating entities with full type inference:")
    print("-" * 70)

    # Direct instantiation: use wrapped types (type system enforces this)
    person = Person(name=Name("Alice Johnson"), age=Age(30), email=Email("alice@example.com"))
    Person.manager(db).insert(person)
    print(f"✓ Created person: {person.name.value}")
    # IDE will autocomplete: person.name, person.age, person.email

    # Direct instantiation with wrapped types
    company = Company(name=Name("TechCorp"))
    Company.manager(db).insert(company)
    print(f"✓ Created company: {company.name.value}")
    # IDE will autocomplete: company.name

    # 2. Type-safe relation creation
    print("\n2. Creating relations with full type inference:")
    print("-" * 70)

    # Direct instantiation: use wrapped types (type system enforces this)
    employment = Employment(
        employee=person,
        employer=company,
        position=Position("Software Engineer"),
        salary=Salary(100000),
    )
    Employment.manager(db).insert(employment)
    print(f"✓ Created employment: {employment.position.value}")
    # IDE will autocomplete: employment.position, employment.salary

    # 3. Type-safe manager instance
    print("\n3. Using manager instances with type safety:")
    print("-" * 70)

    # Manager is typed as EntityManager[Person]
    person_manager = Person.manager(db)
    # Create typed instance with wrapped types
    another_person = Person(name=Name("Bob Smith"), age=Age(28), email=Email("bob@example.com"))
    person_manager.insert(another_person)
    print(f"✓ Created another person: {another_person.name.value}")

    # 4. Benefits summary
    print("\n" + "=" * 70)
    print("Type Safety Benefits:")
    print("=" * 70)
    print("✓ Full type inference - IDE knows exact return types")
    print("✓ Autocomplete support - IDE suggests correct attributes")
    print("✓ Compile-time checking - Catch errors before runtime")
    print("✓ Better refactoring - Rename propagates correctly")
    print("✓ Self-documenting - Types tell you what's available")

    print("\n" + "=" * 70)
    print("Type Checker Verification:")
    print("=" * 70)
    print("Run 'pyright examples/type_safety_demo.py' to verify:")
    print("  - No type errors")
    print("  - All inferences are correct")
    print("  - Full type safety throughout")

    # Cleanup
    db.delete_database()
    db.close()

    print("\n✓ Type safety demonstration completed!")


if __name__ == "__main__":
    demonstrate_type_safety()

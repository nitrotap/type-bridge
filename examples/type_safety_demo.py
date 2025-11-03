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

    # The type checker knows that person is of type Person
    person = Person.manager(db).insert(
        name="Alice Johnson",
        age=30,
        email="alice@example.com"
    )
    print(f"✓ Created person: {person.name.value if hasattr(person.name, 'value') else person.name}")
    # IDE will autocomplete: person.name, person.age, person.email

    # The type checker knows that company is of type Company
    company = Company.manager(db).insert(name="TechCorp")
    print(f"✓ Created company: {company.name.value if hasattr(company.name, 'value') else company.name}")
    # IDE will autocomplete: company.name

    # 2. Type-safe relation creation
    print("\n2. Creating relations with full type inference:")
    print("-" * 70)

    # The type checker knows that employment is of type Employment
    employment = Employment.manager(db).insert(
        role_players={
            "employee": person,
            "employer": company
        },
        attributes={
            "position": "Software Engineer",
            "salary": 100000
        }
    )
    print(f"✓ Created employment: {employment.position.value if hasattr(employment.position, 'value') else employment.position}")
    # IDE will autocomplete: employment.position, employment.salary

    # 3. Type-safe manager instance
    print("\n3. Using manager instances with type safety:")
    print("-" * 70)

    # Manager is typed as EntityManager[Person]
    person_manager = Person.manager(db)
    # Type checker knows person_manager.insert() returns Person
    another_person = person_manager.insert(
        name="Bob Smith",
        age=28,
        email="bob@example.com"
    )
    print(f"✓ Created another person: {another_person.name.value if hasattr(another_person.name, 'value') else another_person.name}")

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

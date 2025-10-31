"""Example demonstrating the new manager() class method syntax."""

from typing import ClassVar

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


class Position(String):
    pass


# Define entity types
class Person(Entity):
    flags = EntityFlags(type_name="person")

    name: Name = Flag(Key)
    age: Age


class Company(Entity):
    flags = EntityFlags(type_name="company")

    name: Name = Flag(Key)


# Define relation type
class Employment(Relation):
    flags = RelationFlags(type_name="employment")

    employee: ClassVar[Role] = Role("employee", Person)
    employer: ClassVar[Role] = Role("employer", Company)

    position: Position


def main():
    # Connect to database
    db = Database(address="localhost:1729", database="manager_example")
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
    attribute position, value string;

    entity person,
        owns name @key,
        owns age;

    entity company,
        owns name @key;

    relation employment,
        relates employee,
        relates employer,
        owns position;

    person plays employment:employee;
    company plays employment:employer;
    """

    db.execute_query(schema, "schema")

    print("=" * 60)
    print("Old Syntax vs New Syntax Comparison")
    print("=" * 60)

    # OLD SYNTAX (still works)
    print("\n# OLD SYNTAX:")
    print("from type_bridge.crud import EntityManager, RelationManager")
    print()
    print("person_mgr = EntityManager(db, Person)")
    print("person = person_mgr.insert(name='Alice', age=30)")
    print()
    print("company_mgr = EntityManager(db, Company)")
    print("company = company_mgr.insert(name='TechCorp')")
    print()
    print("employment_mgr = RelationManager(db, Employment)")
    print("employment = employment_mgr.insert(")
    print("    role_players={'employee': person, 'employer': company},")
    print("    attributes={'position': 'Engineer'}")
    print(")")

    # NEW SYNTAX (cleaner!)
    print("\n" + "=" * 60)
    print("# NEW SYNTAX (using .manager() class method):")
    print("=" * 60)
    print()
    print("person = Person.manager(db).insert(name='Alice', age=30)")
    print("company = Company.manager(db).insert(name='TechCorp')")
    print("employment = Employment.manager(db).insert(")
    print("    role_players={'employee': person, 'employer': company},")
    print("    attributes={'position': 'Engineer'}")
    print(")")

    # Actually create the data using new syntax
    print("\n" + "=" * 60)
    print("Creating actual data with new syntax...")
    print("=" * 60)

    person = Person.manager(db).insert(name="Alice", age=30)
    print(f"✓ Created person: {person.name.value if hasattr(person.name, 'value') else person.name}")

    company = Company.manager(db).insert(name="TechCorp")
    print(f"✓ Created company: {company.name.value if hasattr(company.name, 'value') else company.name}")

    employment = Employment.manager(db).insert(
        role_players={"employee": person, "employer": company},
        attributes={"position": "Engineer"}
    )
    print(f"✓ Created employment: {employment.position.value if hasattr(employment.position, 'value') else employment.position}")

    print("\n" + "=" * 60)
    print("Benefits of the new syntax:")
    print("=" * 60)
    print("1. More concise - no need to import EntityManager/RelationManager")
    print("2. More intuitive - manager is called on the model class itself")
    print("3. Method chaining - create() immediately after manager()")
    print("4. Less verbose - fewer lines of code")
    print("5. Better IDE support - autocomplete from the model class")

    # Cleanup
    db.delete_database()
    db.close()
    print("\n✓ Example completed successfully!")


if __name__ == "__main__":
    main()

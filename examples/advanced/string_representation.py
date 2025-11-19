"""Demonstration of __str__ and __repr__ for entities and relations.

This example shows the difference between:
- __repr__: Developer-friendly representation (shows Python objects)
- __str__: User-friendly representation (shows clean values)
"""

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


class Position(String):
    pass


class Salary(Integer):
    pass


# Define entities
class Person(Entity):
    flags = TypeFlags(type_name="person")

    name: Name = Flag(Key)
    email: Email
    age: Age | None


class Company(Entity):
    flags = TypeFlags(type_name="company")

    name: Name = Flag(Key)


# Define relation
class Employment(Relation):
    flags = TypeFlags(type_name="employment")

    employee: Role[Person] = Role("employee", Person)
    employer: Role[Company] = Role("employer", Company)

    position: Position
    salary: Salary | None


def main():
    """Demonstrate string representations."""
    print("=" * 70)
    print("String Representation Demo (__str__ vs __repr__)")
    print("=" * 70)

    # Create entity instances
    print("\n1. Entity Representations")
    print("-" * 70)

    alice = Person(name=Name("Alice Johnson"), email=Email("alice@example.com"), age=Age(30))

    bob = Person(name=Name("Bob Smith"), email=Email("bob@example.com"), age=None)

    tech_corp = Company(name=Name("TechCorp"))

    print("Person with all fields:")
    print(f"  str(alice):  {str(alice)}")
    print(f"  repr(alice): {repr(alice)}")

    print("\nPerson with optional field missing:")
    print(f"  str(bob):  {str(bob)}")
    print(f"  repr(bob): {repr(bob)}")

    print("\nCompany:")
    print(f"  str(tech_corp):  {str(tech_corp)}")
    print(f"  repr(tech_corp): {repr(tech_corp)}")

    # Create relation instance
    print("\n2. Relation Representations")
    print("-" * 70)

    employment_with_salary = Employment(
        position=Position("Senior Engineer"),
        salary=Salary(120000),
        employee=alice,
        employer=tech_corp,
    )

    employment_no_salary = Employment(
        position=Position("Founder"), salary=None, employee=bob, employer=tech_corp
    )

    print("Employment with salary:")
    print(f"  str():  {str(employment_with_salary)}")
    print(f"  repr(): {repr(employment_with_salary)[:100]}...")  # Truncate for readability

    print("\nEmployment without salary:")
    print(f"  str():  {str(employment_no_salary)}")
    print(f"  repr(): {repr(employment_no_salary)[:100]}...")

    # Using in print statements
    print("\n3. Using in print() Statements")
    print("-" * 70)
    print(f"Alice works at {tech_corp}")
    print(f"Bob is a {employment_no_salary}")

    # Showing in lists
    print("\n4. Showing Collections")
    print("-" * 70)
    people = [alice, bob]
    print("People list:")
    for person in people:
        print(f"  - {person}")

    # Summary
    print("\n" + "=" * 70)
    print("Key Differences")
    print("=" * 70)
    print("__str__  (str() / print()):")
    print("  • User-friendly, clean output")
    print("  • Shows TypeDB type names (person, company, employment)")
    print("  • Extracts values from Attribute objects")
    print("  • Key attributes shown first")
    print("  • Relations show role players and attributes separately")
    print()
    print("__repr__ (repr() / debugging):")
    print("  • Developer-friendly, detailed output")
    print("  • Shows Python class names (Person, Company, Employment)")
    print("  • Shows full Attribute object representations")
    print("  • Used in debuggers and logs")
    print("=" * 70)


if __name__ == "__main__":
    main()

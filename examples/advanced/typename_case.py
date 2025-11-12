"""Example: TypeNameCase - Control how class names are converted to TypeDB type names.

This example demonstrates the three case formatting options for Entity and Relation types:
1. LOWERCASE (default): PersonName → personname
2. CLASS_NAME: PersonName → PersonName (keeps as-is)
3. SNAKE_CASE: PersonName → person_name

You can also explicitly set type_name, which takes precedence over case formatting.
"""

from type_bridge import (
    Entity,
    EntityFlags,
    Flag,
    Integer,
    Key,
    Relation,
    RelationFlags,
    Role,
    String,
    TypeNameCase,
)


# Define attributes
class PersonName(String):
    """Person's full name."""

    pass


class CompanyName(String):
    """Company name."""

    pass


class Age(Integer):
    """Person's age."""

    pass


class JobTitle(String):
    """Job title."""

    pass


# Example 1: LOWERCASE (default) - converts to all lowercase
class FirstPerson(Entity):
    """Uses default LOWERCASE formatting.

    Class name: FirstPerson
    TypeDB type: firstperson
    """

    # No case parameter specified - defaults to LOWERCASE
    flags = EntityFlags()
    name: PersonName = Flag(Key)
    age: Age | None


# Example 2: CLASS_NAME - keeps class name as-is (PascalCase)
class SecondPerson(Entity):
    """Uses CLASS_NAME formatting.

    Class name: SecondPerson
    TypeDB type: SecondPerson (unchanged)
    """

    flags = EntityFlags(case=TypeNameCase.CLASS_NAME)
    name: PersonName = Flag(Key)
    age: Age | None


# Example 3: SNAKE_CASE - converts PascalCase to snake_case
class ThirdPerson(Entity):
    """Uses SNAKE_CASE formatting.

    Class name: ThirdPerson
    TypeDB type: third_person
    """

    flags = EntityFlags(case=TypeNameCase.SNAKE_CASE)
    name: PersonName = Flag(Key)
    age: Age | None


# Example 4: Multi-word class names with SNAKE_CASE
class TechnologyCompany(Entity):
    """Multi-word class with SNAKE_CASE.

    Class name: TechnologyCompany
    TypeDB type: technology_company
    """

    flags = EntityFlags(case=TypeNameCase.SNAKE_CASE)
    name: CompanyName = Flag(Key)


# Example 5: Explicit type_name takes precedence
class FourthPerson(Entity):
    """Explicit type_name overrides case formatting.

    Class name: FourthPerson
    Case: SNAKE_CASE (but ignored)
    TypeDB type: person (explicit type_name)
    """

    flags = EntityFlags(type_name="person", case=TypeNameCase.SNAKE_CASE)
    name: PersonName = Flag(Key)
    age: Age | None


# Example 6: Relations also support case formatting
class PersonCompanyEmployment(Relation):
    """Relation with SNAKE_CASE formatting.

    Class name: PersonCompanyEmployment
    TypeDB type: person_company_employment
    """

    flags = RelationFlags(case=TypeNameCase.SNAKE_CASE)
    employee: Role[FourthPerson] = Role("employee", FourthPerson)
    employer: Role[TechnologyCompany] = Role("employer", TechnologyCompany)
    title: JobTitle


def demonstrate_case_formatting():
    """Show how different case options affect type names."""
    print("=" * 80)
    print("TypeNameCase Formatting Examples")
    print("=" * 80)
    print()

    examples = [
        ("FirstPerson", FirstPerson, "LOWERCASE (default)"),
        ("SecondPerson", SecondPerson, "CLASS_NAME"),
        ("ThirdPerson", ThirdPerson, "SNAKE_CASE"),
        ("TechnologyCompany", TechnologyCompany, "SNAKE_CASE"),
        ("FourthPerson", FourthPerson, "Explicit type_name"),
        ("PersonCompanyEmployment", PersonCompanyEmployment, "SNAKE_CASE (Relation)"),
    ]

    print("Class Name → TypeDB Type Name")
    print("-" * 80)
    for class_name, cls, description in examples:
        type_name = cls.get_type_name()
        print(f"{class_name:30} → {type_name:30} [{description}]")
    print()


def demonstrate_schema_generation():
    """Show how case formatting affects schema generation."""
    print("=" * 80)
    print("Schema Generation with Different Case Options")
    print("=" * 80)
    print()

    print("1. LOWERCASE (default):")
    print("-" * 80)
    print(FirstPerson.to_schema_definition())
    print()

    print("2. CLASS_NAME:")
    print("-" * 80)
    print(SecondPerson.to_schema_definition())
    print()

    print("3. SNAKE_CASE:")
    print("-" * 80)
    print(ThirdPerson.to_schema_definition())
    print()

    print("4. Multi-word SNAKE_CASE:")
    print("-" * 80)
    print(TechnologyCompany.to_schema_definition())
    print()

    print("5. Relation with SNAKE_CASE:")
    print("-" * 80)
    print(PersonCompanyEmployment.to_schema_definition())
    print()


def demonstrate_usage_recommendations():
    """Show best practices for choosing case options."""
    print("=" * 80)
    print("Usage Recommendations")
    print("=" * 80)
    print()

    print("When to use each option:")
    print("-" * 80)
    print()

    print("1. LOWERCASE (default)")
    print("   - Simple, single-word class names")
    print("   - Traditional TypeDB/SQL naming convention")
    print("   - Example: Person → person, Company → company")
    print()

    print("2. CLASS_NAME")
    print("   - Preserve exact class name in schema")
    print("   - When Python naming matches desired TypeDB names")
    print("   - Example: Person → Person, HTTPResponse → HTTPResponse")
    print()

    print("3. SNAKE_CASE")
    print("   - Multi-word class names (recommended!)")
    print("   - Most readable for complex type names")
    print("   - Consistent with Python naming conventions")
    print("   - Example: PersonName → person_name, HTTPResponse → http_response")
    print()

    print("4. Explicit type_name")
    print("   - When you need complete control")
    print("   - For legacy schema compatibility")
    print("   - Example: PersonName with type_name='person' → person")
    print()


def main():
    """Run all demonstrations."""
    print()
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "TypeNameCase Feature Demo" + " " * 33 + "║")
    print("╚" + "═" * 78 + "╝")
    print()

    demonstrate_case_formatting()
    input("Press Enter to continue...")
    print()

    demonstrate_schema_generation()
    input("Press Enter to continue...")
    print()

    demonstrate_usage_recommendations()

    print("=" * 80)
    print("✓ Demo Complete!")
    print("=" * 80)
    print()
    print("Key Takeaways:")
    print("  • LOWERCASE (default): Simple and traditional")
    print("  • CLASS_NAME: Preserves exact class names")
    print("  • SNAKE_CASE: Best for multi-word class names (recommended!)")
    print("  • Explicit type_name: Complete control when needed")
    print("=" * 80)


if __name__ == "__main__":
    main()

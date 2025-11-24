"""Example: Attribute TypeNameCase - Control attribute name formatting.

This example demonstrates how to control how attribute class names are converted
to TypeDB attribute names using the same TypeNameCase options:

1. LOWERCASE (default): PersonName → personname
2. CLASS_NAME: PersonName → PersonName (keeps as-is)
3. SNAKE_CASE: PersonName → person_name (recommended for multi-word names!)

You can also explicitly set attr_name, which takes precedence over case formatting.
"""

from type_bridge import (
    Boolean,
    DateTime,
    Double,
    Entity,
    Flag,
    Integer,
    Key,
    String,
    TypeFlags,
    TypeNameCase,
)


# Example 1: LOWERCASE (default) - converts to all lowercase
class FirstName(String):
    """Uses default LOWERCASE formatting.

    Class name: FirstName
    TypeDB attribute: firstname
    """

    # No case parameter specified - defaults to LOWERCASE
    pass


# Example 2: CLASS_NAME - keeps class name as-is (PascalCase)
class LastName(String):
    """Uses CLASS_NAME formatting.

    Class name: LastName
    TypeDB attribute: LastName (unchanged)
    """

    case = TypeNameCase.CLASS_NAME


# Example 3: SNAKE_CASE - converts PascalCase to snake_case
class EmailAddress(String):
    """Uses SNAKE_CASE formatting.

    Class name: EmailAddress
    TypeDB attribute: email_address
    """

    case = TypeNameCase.SNAKE_CASE


# Example 4: Multi-word attribute names with SNAKE_CASE
class PhoneNumber(String):
    """Multi-word class with SNAKE_CASE.

    Class name: PhoneNumber
    TypeDB attribute: phone_number
    """

    case = TypeNameCase.SNAKE_CASE


class StreetAddress(String):
    """Another multi-word example.

    Class name: StreetAddress
    TypeDB attribute: street_address
    """

    case = TypeNameCase.SNAKE_CASE


# Example 5: Explicit attr_name takes precedence
class DateOfBirth(DateTime):
    """Explicit attribute name overrides case formatting.

    Class name: DateOfBirth
    Case: SNAKE_CASE (but ignored)
    TypeDB attribute: dob (explicit attr_name)
    """

    attr_name = "dob"
    case = TypeNameCase.SNAKE_CASE


# Example 6: Different value types with case formatting
class PersonAge(Integer):
    """Integer attribute with SNAKE_CASE."""

    case = TypeNameCase.SNAKE_CASE


class AccountBalance(Double):
    """Double attribute with SNAKE_CASE."""

    case = TypeNameCase.SNAKE_CASE


class IsActive(Boolean):
    """Boolean attribute with SNAKE_CASE."""

    case = TypeNameCase.SNAKE_CASE


# Example 7: Using formatted attributes in an entity
class Person(Entity):
    """Entity using attributes with various case formats."""

    flags: TypeFlags = TypeFlags(case=TypeNameCase.SNAKE_CASE)

    # Mix of different attribute case formats
    # Fields without defaults first
    last_name: LastName  # → LastName (CLASS_NAME)
    email: EmailAddress  # → email_address (SNAKE_CASE)
    phone: PhoneNumber  # → phone_number (SNAKE_CASE)
    age: PersonAge | None  # → person_age (SNAKE_CASE)
    active: IsActive  # → is_active (SNAKE_CASE)
    dob: DateOfBirth | None  # → dob (explicit attr_name)
    # Fields with Flag() defaults last
    first_name: FirstName = Flag(Key)  # → firstname (LOWERCASE)


def demonstrate_case_formatting():
    """Show how different case options affect attribute names."""
    print("=" * 80)
    print("Attribute TypeNameCase Formatting Examples")
    print("=" * 80)
    print()

    examples = [
        ("FirstName", FirstName, "LOWERCASE (default)"),
        ("LastName", LastName, "CLASS_NAME"),
        ("EmailAddress", EmailAddress, "SNAKE_CASE"),
        ("PhoneNumber", PhoneNumber, "SNAKE_CASE"),
        ("StreetAddress", StreetAddress, "SNAKE_CASE"),
        ("DateOfBirth", DateOfBirth, "Explicit attr_name='dob'"),
        ("PersonAge", PersonAge, "SNAKE_CASE"),
        ("AccountBalance", AccountBalance, "SNAKE_CASE"),
        ("IsActive", IsActive, "SNAKE_CASE"),
    ]

    print("Class Name → TypeDB Attribute Name")
    print("-" * 80)
    for class_name, cls, description in examples:
        attr_name = cls.get_attribute_name()
        value_type = cls.get_value_type()
        print(f"{class_name:20} → {attr_name:25} ({value_type:8}) [{description}]")
    print()


def demonstrate_schema_generation():
    """Show how case formatting affects attribute schema generation."""
    print("=" * 80)
    print("Attribute Schema Generation with Different Case Options")
    print("=" * 80)
    print()

    print("1. LOWERCASE (default):")
    print("-" * 80)
    print(FirstName.to_schema_definition())
    print()

    print("2. CLASS_NAME:")
    print("-" * 80)
    print(LastName.to_schema_definition())
    print()

    print("3. SNAKE_CASE:")
    print("-" * 80)
    print(EmailAddress.to_schema_definition())
    print()

    print("4. Multi-word SNAKE_CASE:")
    print("-" * 80)
    print(PhoneNumber.to_schema_definition())
    print()

    print("5. Explicit attr_name:")
    print("-" * 80)
    print(DateOfBirth.to_schema_definition())
    print()


def demonstrate_entity_schema():
    """Show how formatted attributes appear in entity schema."""
    print("=" * 80)
    print("Entity Schema with Mixed Attribute Case Formats")
    print("=" * 80)
    print()

    print("Entity Definition:")
    print("-" * 80)
    print(Person.to_schema_definition())
    print()

    print("Notice how each attribute uses its own case formatting:")
    print("  • first_name uses 'firstname' (LOWERCASE)")
    print("  • last_name uses 'LastName' (CLASS_NAME)")
    print("  • email uses 'email_address' (SNAKE_CASE)")
    print("  • phone uses 'phone_number' (SNAKE_CASE)")
    print("  • age uses 'person_age' (SNAKE_CASE)")
    print("  • active uses 'is_active' (SNAKE_CASE)")
    print("  • dob uses 'dob' (explicit attr_name)")
    print()


def demonstrate_instance_creation():
    """Show how to create instances with formatted attributes."""
    print("=" * 80)
    print("Creating Entity Instances with Formatted Attributes")
    print("=" * 80)
    print()

    print("Python Code:")
    print("-" * 80)
    print(
        """
person = Person(
    first_name=FirstName("Alice"),
    last_name=LastName("Johnson"),
    email=EmailAddress("alice@example.com"),
    phone=PhoneNumber("+1-555-0100"),
    age=PersonAge(30),
    active=IsActive(True),
    dob=DateOfBirth("1994-01-15T00:00:00")
)
"""
    )

    from datetime import datetime

    person = Person(
        first_name=FirstName("Alice"),
        last_name=LastName("Johnson"),
        email=EmailAddress("alice@example.com"),
        phone=PhoneNumber("+1-555-0100"),
        age=PersonAge(30),
        active=IsActive(True),
        dob=DateOfBirth(datetime(1994, 1, 15)),
    )

    print("Generated TypeQL Insert Query:")
    print("-" * 80)
    print(f"insert {person.to_insert_query()};")
    print()

    print("Notice how the attribute names in the query match the formatted names:")
    print('  • has firstname "Alice"')
    print('  • has LastName "Johnson"')
    print('  • has email_address "alice@example.com"')
    print('  • has phone_number "+1-555-0100"')
    print("  • has person_age 30")
    print("  • has is_active true")
    print()


def demonstrate_usage_recommendations():
    """Show best practices for choosing case options."""
    print("=" * 80)
    print("Usage Recommendations for Attributes")
    print("=" * 80)
    print()

    print("When to use each option:")
    print("-" * 80)
    print()

    print("1. LOWERCASE (default)")
    print("   - Simple, single-word attribute names")
    print("   - Traditional database naming convention")
    print("   - Example: Name → name, Age → age, Email → email")
    print()

    print("2. CLASS_NAME")
    print("   - Preserve exact class name in schema")
    print("   - When Python naming matches desired TypeDB names")
    print("   - Example: Name → Name, Email → Email")
    print()

    print("3. SNAKE_CASE (recommended for multi-word names!)")
    print("   - Multi-word attribute class names")
    print("   - Most readable for complex attribute names")
    print("   - Consistent with Python/database naming conventions")
    print("   - Example: FirstName → first_name, EmailAddress → email_address")
    print()

    print("4. Explicit attr_name")
    print("   - When you need complete control")
    print("   - For legacy schema compatibility")
    print("   - For abbreviations or special names")
    print("   - Example: DateOfBirth with attr_name='dob' → dob")
    print()

    print("Best Practice Tips:")
    print("-" * 80)
    print("  ✓ Use SNAKE_CASE for multi-word attribute names")
    print("  ✓ Use explicit attr_name for abbreviations (e.g., dob, ssn)")
    print("  ✓ Be consistent across your schema")
    print("  ✓ Consider readability in TypeQL queries")
    print()


def main():
    """Run all demonstrations."""
    print()
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 15 + "Attribute TypeNameCase Feature Demo" + " " * 28 + "║")
    print("╚" + "═" * 78 + "╝")
    print()

    demonstrate_case_formatting()
    input("Press Enter to continue...")
    print()

    demonstrate_schema_generation()
    input("Press Enter to continue...")
    print()

    demonstrate_entity_schema()
    input("Press Enter to continue...")
    print()

    demonstrate_instance_creation()
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
    print("  • SNAKE_CASE: Best for multi-word names (recommended!)")
    print("  • Explicit attr_name: Complete control when needed")
    print("  • Can mix different case formats in the same entity")
    print("=" * 80)


if __name__ == "__main__":
    main()

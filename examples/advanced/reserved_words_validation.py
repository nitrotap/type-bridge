"""Example demonstrating TypeQL reserved word validation.

TypeBridge prevents you from using TypeQL reserved words as type names,
attribute names, or role names. This helps avoid syntax conflicts and
confusing error messages when working with TypeDB.

Run this example:
    uv run python examples/advanced/reserved_words_validation.py
"""

from type_bridge import Entity, Integer, Relation, Role, String, TypeFlags
from type_bridge.validation import ReservedWordError


def demonstrate_entity_validation():
    """Show how Entity validation catches reserved words."""
    print("=" * 60)
    print("Entity Validation Examples")
    print("=" * 60)

    # Example 1: Valid entity name
    try:

        class Person(Entity):
            flags: TypeFlags = TypeFlags(name="person")

        print("✓ Valid: 'person' is not a reserved word")
    except ReservedWordError as e:
        print(f"✗ Error: {e}")

    # Example 2: Using TypeQL keyword as entity name (will fail)
    try:

        class Match(Entity):
            flags: TypeFlags = TypeFlags(name="match")

        print("✓ Created entity with name 'match'")
    except ReservedWordError as e:
        print("✗ Error creating 'match' entity:")
        print(f"  {str(e).split(chr(10))[0]}")  # First line of error
        print("  (This is expected - 'match' is a TypeQL keyword)")

    # Example 3: Escape hatch with base=True
    try:

        class Define(Entity):
            flags: TypeFlags = TypeFlags(base=True, name="define")

        print("✓ Created base entity with reserved name 'define' (base=True bypasses validation)")
    except ReservedWordError as e:
        print(f"✗ Error: {e}")

    print()


def demonstrate_attribute_validation():
    """Show how Attribute validation catches reserved words."""
    print("=" * 60)
    print("Attribute Validation Examples")
    print("=" * 60)

    # Example 1: Valid attribute name
    try:

        class Name(String):
            pass

        print("✓ Valid: 'Name' is not a reserved word")
    except ReservedWordError as e:
        print(f"✗ Error: {e}")

    # Example 2: Using TypeQL value type as attribute name (will fail)
    try:

        class MyString(String):
            attr_name = "string"  # 'string' is a TypeQL value type

        print("✓ Created attribute with name 'string'")
    except ReservedWordError as e:
        print("✗ Error creating 'string' attribute:")
        print(f"  {str(e).split(chr(10))[0]}")
        print("  (This is expected - 'string' is a TypeQL value type keyword)")

    # Example 3: Using reduction keyword (will fail)
    try:

        class CountAttribute(Integer):
            attr_name = "count"  # 'count' is a reduction keyword

        print("✓ Created attribute with name 'count'")
    except ReservedWordError as e:
        print("✗ Error creating 'count' attribute:")
        print(f"  {str(e).split(chr(10))[0]}")
        print("  (This is expected - 'count' is a TypeQL reduction keyword)")

    print()


def demonstrate_relation_validation():
    """Show how Relation validation catches reserved words."""
    print("=" * 60)
    print("Relation Validation Examples")
    print("=" * 60)

    # Example 1: Valid relation name
    try:

        class Employment(Relation):
            flags: TypeFlags = TypeFlags(name="employment")

        print("✓ Valid: 'employment' is not a reserved word")
    except ReservedWordError as e:
        print(f"✗ Error: {e}")

    # Example 2: Using TypeQL keyword as relation name (will fail)
    try:

        class Update(Relation):
            flags: TypeFlags = TypeFlags(name="update")

        print("✓ Created relation with name 'update'")
    except ReservedWordError as e:
        print("✗ Error creating 'update' relation:")
        print(f"  {str(e).split(chr(10))[0]}")
        print("  (This is expected - 'update' is a TypeQL data manipulation keyword)")

    print()


def demonstrate_role_validation():
    """Show how Role validation catches reserved words."""
    print("=" * 60)
    print("Role Validation Examples")
    print("=" * 60)

    # Need valid entities for role examples
    class Person(Entity):
        pass

    class Company(Entity):
        pass

    # Example 1: Valid role names
    try:
        employee_role = Role("employee", Person)
        employer_role = Role("employer", Company)
        print("✓ Valid: 'employee' and 'employer' are not reserved words")
    except ReservedWordError as e:
        print(f"✗ Error: {e}")

    # Example 2: Using TypeQL keyword as role name (will fail)
    try:
        from_role = Role("from", Person)  # 'from' is a TypeQL keyword
        print("✓ Created role with name 'from'")
    except ReservedWordError as e:
        print("✗ Error creating 'from' role:")
        print(f"  {str(e).split(chr(10))[0]}")
        print("  (This is expected - 'from' is a TypeQL keyword)")

    # Example 3: Another reserved word example
    try:
        plays_role = Role("plays", Company)  # 'plays' is a TypeQL statement
        print("✓ Created role with name 'plays'")
    except ReservedWordError as e:
        print("✗ Error creating 'plays' role:")
        print(f"  {str(e).split(chr(10))[0]}")
        print("  (This is expected - 'plays' is a TypeQL constraint statement)")

    print()


def demonstrate_error_suggestions():
    """Show how TypeBridge provides helpful suggestions for reserved words."""
    print("=" * 60)
    print("Error Messages with Suggestions")
    print("=" * 60)

    # Catch full error to show suggestions
    try:

        class StringAttribute(String):
            attr_name = "string"
    except ReservedWordError as e:
        print("Full error message for using 'string' as attribute name:")
        print("-" * 40)
        print(e)
        print("-" * 40)

    print()


def list_some_reserved_words():
    """List some common TypeQL reserved words."""
    from type_bridge.reserved_words import get_reserved_words

    print("=" * 60)
    print("Some Common TypeQL Reserved Words")
    print("=" * 60)

    reserved = sorted(get_reserved_words())

    # Group by category for display
    categories = {
        "Schema Queries": ["define", "undefine", "redefine"],
        "Data Manipulation": ["match", "fetch", "insert", "delete", "update", "put"],
        "Type Definitions": ["entity", "relation", "attribute", "struct", "fun"],
        "Constraints": ["sub", "relates", "plays", "owns", "has", "isa"],
        "Value Types": ["boolean", "integer", "double", "decimal", "string", "date", "datetime"],
        "Reductions": ["count", "sum", "max", "min", "mean", "median"],
        "Logic": ["or", "not", "try"],
        "Miscellaneous": ["true", "false", "from", "as", "in", "of", "return"],
    }

    for category, words in categories.items():
        # Filter to only words that are actually reserved
        actual_reserved = [w for w in words if w in reserved]
        if actual_reserved:
            print(f"\n{category}:")
            print(f"  {', '.join(actual_reserved)}")

    print(f"\nTotal reserved words: {len(reserved)}")
    print()


def main():
    """Run all validation demonstrations."""
    print("\n" + "=" * 60)
    print("TypeBridge Reserved Word Validation Demonstration")
    print("=" * 60 + "\n")

    demonstrate_entity_validation()
    demonstrate_attribute_validation()
    demonstrate_relation_validation()
    demonstrate_role_validation()
    demonstrate_error_suggestions()
    list_some_reserved_words()

    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print("""
TypeBridge helps prevent common mistakes by validating that your
type names don't conflict with TypeQL reserved words. This validation:

1. Prevents syntax errors in generated TypeQL queries
2. Provides helpful error messages with suggestions
3. Can be bypassed with base=True for Python-only base classes
4. Works for entities, relations, attributes, and roles

If you need to use a reserved word for some reason, consider:
- Using a prefix/suffix (e.g., 'my_match', 'match_entity')
- Using a synonym (e.g., 'text' instead of 'string')
- Using base=True if it's a Python-only base class
""")


if __name__ == "__main__":
    main()

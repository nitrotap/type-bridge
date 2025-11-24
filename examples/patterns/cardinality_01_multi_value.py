"""Pattern Example: Cardinality and Multi-Value Attributes.

This example demonstrates:
- Single-value attributes (Card(1, 1) or default)
- Optional attributes (Type | None or Card(0, 1))
- Multi-value attributes (list[Type])
- Bounded cardinality (Card(min, max))
- CRUD operations on multi-value attributes
- Cardinality validation

Pattern: Cardinality controls how many values an attribute can have.
TypeDB supports rich cardinality constraints beyond simple "required/optional".
"""

from type_bridge import (
    Card,
    Database,
    Entity,
    Flag,
    Integer,
    Key,
    SchemaManager,
    String,
    TypeFlags,
)


# Define attribute types
class Name(String):
    pass


class Email(String):
    pass


class Tag(String):
    pass


class Skill(String):
    pass


class Phone(String):
    pass


class Address(String):
    pass


class ExperienceYears(Integer):
    pass


# Entity demonstrating different cardinality patterns
class Person(Entity):
    """Person with various cardinality patterns."""

    flags: TypeFlags = TypeFlags(name="person")

    # Required single-value (default cardinality)
    name: Name = Flag(Key)

    # Required single-value (explicit)
    email: Email  # Same as Card(1, 1)

    # Optional single-value (Type | None)
    experience_years: ExperienceYears | None = None

    # Optional single-value (explicit Card(0, 1))
    address: Address | None = None

    # Multi-value unbounded (list[Type])
    tags: list[Tag]  # Can have 0 or more tags

    # Multi-value with minimum (at least 1 skill)
    skills: list[Skill] = Flag(Card(1))

    # Multi-value with maximum (up to 3 phone numbers)
    phones: list[Phone] = Flag(Card(0, 3))


def demonstrate_cardinality_patterns(db: Database):
    """Step 1: Demonstrate different cardinality patterns."""
    print("=" * 80)
    print("STEP 1: Cardinality Patterns")
    print("=" * 80)
    print()
    print("TypeBridge supports various cardinality patterns:")
    print()

    print("Python Code:")
    print("-" * 80)
    print("""
class Person(Entity):
    # Required single-value (default)
    name: Name = Flag(Key)
    email: Email

    # Optional single-value
    experience_years: ExperienceYears | None
    address: Address | None = None

    # Multi-value unbounded
    tags: list[Tag]

    # Multi-value with minimum (at least 1)
    skills: list[Skill] = Flag(Card(1))

    # Multi-value bounded (0 to 3)
    phones: list[Phone] = Flag(Card(0, 3))
""")
    print("-" * 80)
    print()

    print("Cardinality Patterns:")
    print("  • name: Required (1, 1) - Must have exactly one")
    print("  • email: Required (1, 1) - Must have exactly one")
    print("  • experience_years: Optional (0, 1) - Can have zero or one")
    print("  • address: Optional (0, 1) - Can have zero or one")
    print("  • tags: Unbounded (0, ∞) - Can have zero or more")
    print("  • skills: Minimum 1 (1, ∞) - Must have at least one")
    print("  • phones: Bounded (0, 3) - Can have zero to three")
    print()
    input("Press Enter to continue...")
    print()


def demonstrate_creating_with_multi_value(db: Database):
    """Step 2: Demonstrate creating entities with multi-value attributes."""
    print("=" * 80)
    print("STEP 2: Creating Entities with Multi-Value Attributes")
    print("=" * 80)
    print()

    person_mgr = Person.manager(db)

    # Create person with multiple skills and tags
    print("Creating person with multi-value attributes...")
    print("-" * 80)
    print("""
alice = Person(
    name=Name("Alice Johnson"),
    email=Email("alice@example.com"),
    experience_years=ExperienceYears(5),
    tags=[Tag("python"), Tag("typedb"), Tag("backend")],
    skills=[Skill("Python"), Skill("TypeDB"), Skill("FastAPI")],
    phones=[Phone("555-0101"), Phone("555-0102")]
)
""")
    print("-" * 80)
    print()

    alice = Person(
        name=Name("Alice Johnson"),
        email=Email("alice@example.com"),
        experience_years=ExperienceYears(5),
        tags=[Tag("python"), Tag("typedb"), Tag("backend")],
        skills=[Skill("Python"), Skill("TypeDB"), Skill("FastAPI")],
        phones=[Phone("555-0101"), Phone("555-0102")],
    )

    person_mgr.insert(alice)
    print("✓ Created Alice with:")
    print(f"  • {len(alice.tags)} tags")
    print(f"  • {len(alice.skills)} skills")
    print(f"  • {len(alice.phones)} phone numbers")
    print()

    # Create person with minimal multi-value attributes
    print("Creating person with minimal multi-value attributes...")
    print("-" * 80)
    bob = Person(
        name=Name("Bob Smith"),
        email=Email("bob@example.com"),
        tags=[],  # Empty list is valid for unbounded
        skills=[Skill("JavaScript")],  # Minimum 1 skill required
        phones=[],  # Empty list is valid for Card(0, 3)
    )

    person_mgr.insert(bob)
    print("✓ Created Bob with:")
    print(f"  • {len(bob.tags)} tags (empty list)")
    print(f"  • {len(bob.skills)} skill (minimum satisfied)")
    print(f"  • {len(bob.phones)} phone numbers (empty list)")
    print()

    # Create person with maximum multi-value attributes
    print("Creating person with maximum phone numbers...")
    print("-" * 80)
    charlie = Person(
        name=Name("Charlie Davis"),
        email=Email("charlie@example.com"),
        tags=[Tag("java"), Tag("spring"), Tag("cloud"), Tag("devops")],
        skills=[Skill("Java"), Skill("Spring Boot"), Skill("Kubernetes")],
        phones=[
            Phone("555-0201"),
            Phone("555-0202"),
            Phone("555-0203"),
        ],  # Maximum 3
    )

    person_mgr.insert(charlie)
    print("✓ Created Charlie with:")
    print(f"  • {len(charlie.tags)} tags")
    print(f"  • {len(charlie.skills)} skills")
    print(f"  • {len(charlie.phones)} phone numbers (maximum)")
    print()
    input("Press Enter to continue...")
    print()


def demonstrate_reading_multi_value(db: Database):
    """Step 3: Demonstrate reading multi-value attributes."""
    print("=" * 80)
    print("STEP 3: Reading Multi-Value Attributes")
    print("=" * 80)
    print()

    person_mgr = Person.manager(db)

    # Get all persons
    all_persons = person_mgr.all()

    print(f"Retrieved {len(all_persons)} persons:")
    print()

    for person in sorted(all_persons, key=lambda p: p.name.value):
        print(f"• {person.name.value}")
        print(f"  Email: {person.email.value}")

        # Handle optional single-value
        exp = person.experience_years.value if person.experience_years else "N/A"
        print(f"  Experience: {exp} years")

        # Iterate multi-value attributes
        print(f"  Tags: {', '.join([t.value for t in person.tags])}")
        print(f"  Skills: {', '.join([s.value for s in person.skills])}")
        print(f"  Phones: {', '.join([p.value for p in person.phones])}")
        print()

    print("Note: Multi-value attributes are Python lists of Attribute instances.")
    print("Use [attr.value for attr in person.multi_value_field] to get values.")
    print()
    input("Press Enter to continue...")
    print()


def demonstrate_updating_multi_value(db: Database):
    """Step 4: Demonstrate updating multi-value attributes."""
    print("=" * 80)
    print("STEP 4: Updating Multi-Value Attributes")
    print("=" * 80)
    print()
    print("Multi-value attributes use REPLACE semantics in TypeDB.")
    print("The entire list is replaced, not appended or merged.")
    print()

    person_mgr = Person.manager(db)

    # Get Alice
    alice = person_mgr.get(name="Alice Johnson")[0]

    print(f"Alice's current tags: {[t.value for t in alice.tags]}")
    print()

    # Update tags (REPLACE entire list)
    print("Updating tags...")
    print("-" * 80)
    print("""
# Fetch
alice = person_mgr.get(name="Alice Johnson")[0]

# Modify (REPLACE the list)
alice.tags = [Tag("python"), Tag("typedb"), Tag("orm"), Tag("advanced")]

# Update
person_mgr.update(alice)
""")
    print("-" * 80)
    print()

    alice.tags = [Tag("python"), Tag("typedb"), Tag("orm"), Tag("advanced")]
    person_mgr.update(alice)

    # Verify
    alice_updated = person_mgr.get(name="Alice Johnson")[0]
    print(f"✓ Alice's updated tags: {[t.value for t in alice_updated.tags]}")
    print()

    # Append pattern (fetch, modify, update)
    print("Appending to multi-value attributes:")
    print("-" * 80)
    print("""
# Fetch current values
alice = person_mgr.get(name="Alice Johnson")[0]
current_skills = [s.value for s in alice.skills]

# Append new value
current_skills.append("Docker")
alice.skills = [Skill(s) for s in current_skills]

# Update
person_mgr.update(alice)
""")
    print("-" * 80)
    print()

    alice = person_mgr.get(name="Alice Johnson")[0]
    current_skills = [s.value for s in alice.skills]
    current_skills.append("Docker")
    alice.skills = [Skill(s) for s in current_skills]
    person_mgr.update(alice)

    alice_updated = person_mgr.get(name="Alice Johnson")[0]
    print(f"✓ Alice's updated skills: {[s.value for s in alice_updated.skills]}")
    print()

    # Clear multi-value attribute
    print("Clearing multi-value attributes (for unbounded):")
    print("-" * 80)
    bob = person_mgr.get(name="Bob Smith")[0]
    print(f"Bob's tags before: {[t.value for t in bob.tags]}")

    bob.tags = []  # Clear tags (valid for unbounded)
    person_mgr.update(bob)

    bob_updated = person_mgr.get(name="Bob Smith")[0]
    print(f"Bob's tags after: {[t.value for t in bob_updated.tags]} (empty)")
    print()
    input("Press Enter to continue...")
    print()


def demonstrate_cardinality_validation(db: Database):
    """Step 5: Demonstrate cardinality validation."""
    print("=" * 80)
    print("STEP 5: Cardinality Validation")
    print("=" * 80)
    print()
    print("TypeDB enforces cardinality constraints at the database level.")
    print()

    person_mgr = Person.manager(db)

    # Valid: Within cardinality bounds
    print("✓ Valid: Person with 1-3 phones (within Card(0, 3)):")
    diana = Person(
        name=Name("Diana Evans"),
        email=Email("diana@example.com"),
        tags=[],
        skills=[Skill("React")],
        phones=[Phone("555-0301")],
    )
    person_mgr.insert(diana)
    print("  Created successfully")
    print()

    # Note about cardinality violations
    print("Note: Cardinality violations:")
    print("-" * 80)
    print("  • Too few values (e.g., skills=[] when Card(1) required):")
    print("    TypeDB will reject the insert/update")
    print()
    print("  • Too many values (e.g., 4 phones when Card(0, 3)):")
    print("    TypeDB will reject the insert/update")
    print()
    print("  • Missing required attribute (e.g., email=None):")
    print("    Pydantic will raise ValidationError before database")
    print()

    print("Example of constraint satisfaction:")
    print("-" * 80)
    print("""
# This would work (minimum 1 skill):
person.skills = [Skill("Python")]

# This would fail (below minimum):
person.skills = []  # Error: Card(1) requires at least 1

# This would work (within maximum):
person.phones = [Phone("555-0101"), Phone("555-0102")]

# This would fail (above maximum):
person.phones = [Phone("1"), Phone("2"), Phone("3"), Phone("4")]  # Error: Card(0, 3)
""")
    print("-" * 80)
    print()
    input("Press Enter to continue...")
    print()


def demonstrate_querying_multi_value(db: Database):
    """Step 6: Demonstrate querying by multi-value attributes."""
    print("=" * 80)
    print("STEP 6: Querying Multi-Value Attributes")
    print("=" * 80)
    print()
    print("You can filter by multi-value attributes to find entities")
    print("that have specific values in their lists.")
    print()

    person_mgr = Person.manager(db)

    # Find persons with specific tag
    print("Find persons with 'python' tag:")
    print("-" * 80)
    python_devs = person_mgr.filter(Tag.eq(Tag("python"))).execute()

    print(f"✓ Found {len(python_devs)} person(s) with 'python' tag:")
    for person in python_devs:
        print(f"  • {person.name.value}")
        print(f"    Tags: {[t.value for t in person.tags]}")
    print()

    # Find persons with specific skill
    print("Find persons with 'TypeDB' skill:")
    print("-" * 80)
    typedb_experts = person_mgr.filter(Skill.eq(Skill("TypeDB"))).execute()

    print(f"✓ Found {len(typedb_experts)} person(s) with 'TypeDB' skill:")
    for person in typedb_experts:
        print(f"  • {person.name.value}")
        print(f"    Skills: {[s.value for s in person.skills]}")
    print()

    # Find persons with phone numbers
    print("Find persons with at least one phone number:")
    print("-" * 80)
    with_phones = person_mgr.filter(Phone.like(Phone(".*"))).execute()

    print(f"✓ Found {len(with_phones)} person(s) with phone numbers:")
    for person in with_phones:
        print(f"  • {person.name.value}: {len(person.phones)} phone(s)")
    print()
    input("Press Enter to continue...")
    print()


def show_cardinality_summary():
    """Show summary of cardinality patterns."""
    print("=" * 80)
    print("Cardinality and Multi-Value Attributes Summary")
    print("=" * 80)
    print()

    print("Cardinality Syntax:")
    print("  • Single required: AttributeType (default)")
    print("  • Single optional: AttributeType | None")
    print("  • Multi unbounded: list[AttributeType]")
    print("  • Multi minimum: list[AttributeType] = Flag(Card(min))")
    print("  • Multi bounded: list[AttributeType] = Flag(Card(min, max))")
    print()

    print("Common Patterns:")
    print("  • Card(1, 1): Exactly one (default for non-list)")
    print("  • Card(0, 1): Zero or one (Type | None)")
    print("  • Card(0): Zero or more (list[Type] or unbounded)")
    print("  • Card(1): At least one (list[Type] = Flag(Card(1)))")
    print("  • Card(M, N): Between M and N inclusive")
    print()

    print("CRUD with Multi-Value:")
    print("  • Create: Pass list of Attribute instances")
    print("  • Read: Returns list of Attribute instances")
    print("  • Update: REPLACES entire list (not append/merge)")
    print("  • Delete: Set to [] if cardinality allows")
    print()

    print("Best Practices:")
    print("  ✓ Use list[Type] for collections (tags, skills, etc.)")
    print("  ✓ Use Card(min) to enforce minimum requirements")
    print("  ✓ Use Card(min, max) to enforce bounded lists")
    print("  ✓ Remember update REPLACES the list (fetch-modify-update for append)")
    print("  ✓ Use Type | None for truly optional single values")
    print()


def main():
    """Run cardinality and multi-value demonstration."""
    print()
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 13 + "Pattern: Cardinality and Multi-Value Attributes" + " " * 17 + "║")
    print("╚" + "═" * 78 + "╝")
    print()

    # Create fresh database
    db = Database(address="localhost:1729", database="pattern_cardinality")
    db.connect()

    if db.database_exists():
        print("Deleting existing database...")
        db.delete_database()

    db.create_database()
    print("✓ Created database 'pattern_cardinality'")
    print()

    # Set up schema
    schema_mgr = SchemaManager(db)
    schema_mgr.register(Person)
    schema_mgr.sync_schema()
    print("✓ Schema synchronized")
    print()

    # Run demonstrations
    demonstrate_cardinality_patterns(db)
    demonstrate_creating_with_multi_value(db)
    demonstrate_reading_multi_value(db)
    demonstrate_updating_multi_value(db)
    demonstrate_cardinality_validation(db)
    demonstrate_querying_multi_value(db)
    show_cardinality_summary()

    # Clean up
    print("=" * 80)
    print("Demonstration complete!")
    print("=" * 80)
    print()

    delete_db = input("Delete 'pattern_cardinality' database? [y/N]: ").strip().lower()
    if delete_db in ("y", "yes"):
        db.delete_database()
        print("✓ Database deleted")
    else:
        print("Database 'pattern_cardinality' preserved for exploration")

    db.close()


if __name__ == "__main__":
    main()

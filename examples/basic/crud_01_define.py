"""CRUD Tutorial Part 1: Schema Definition Only.

This example demonstrates:
- Defining attributes, entities, and relations
- Configuring cardinality with Flag(Key), Flag(Card(...)), and Type | None
- Generating TypeQL schema definitions
- Creating and connecting to a TypeDB database
- Syncing schema to TypeDB (no data insertion)

The database "crud_demo" persists for use in subsequent examples.
Data insertion happens in crud_02_insert.py.
"""

from type_bridge import (
    Boolean,
    Card,
    Database,
    Double,
    Entity,
    Flag,
    Integer,
    Key,
    Relation,
    Role,
    SchemaManager,
    String,
    TypeFlags,
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

    flags = TypeFlags(type_name="person")

    name: Name = Flag(Key)  # @key (implies @card(1..1)) - exactly one, marked as key
    age: Age | None  # @card(0..1) - zero or one (optional)
    email: Email  # @card(1..1) - exactly one (default)
    score: Score  # @card(1..1) - exactly one (default)


class Company(Entity):
    """Company entity with cardinality annotations."""

    flags = TypeFlags(type_name="company")

    name: Name = Flag(Key)  # @key (implies @card(1..1)) - exactly one, marked as key
    industry: list[Industry] = Flag(Card(1, 5))  # @card(1..5) - one to five industries


# Step 3: Define relations that OWN attributes
class Employment(Relation):
    """Employment relation between person and company."""

    flags = TypeFlags(type_name="employment")

    # Roles - using generic Role[T] for type safety
    employee: Role[Person] = Role("employee", Person)
    employer: Role[Company] = Role("employer", Company)

    # Owned attributes with cardinality
    position: Position  # @card(1..1) - exactly one (default)
    salary: Salary | None  # @card(0..1) - zero or one (optional)


def demonstrate_step1_attributes():
    """Step 1: Define attributes with code examples."""
    print("=" * 80)
    print("STEP 1: Defining Attribute Types")
    print("=" * 80)
    print()
    print("Attributes are the basic data types in TypeDB.")
    print("Each attribute inherits from a base type (String, Integer, Double, Boolean).")
    print()

    print("Python Code:")
    print("-" * 80)
    print("""
class Name(String):
    \"\"\"Name attribute - a string.\"\"\"
    pass

class Age(Integer):
    \"\"\"Age attribute - a long integer.\"\"\"
    pass

class Score(Double):
    \"\"\"Score attribute - a double.\"\"\"
    pass
""")
    print("-" * 80)
    print()

    print("Generated TypeQL Schema:")
    print("-" * 80)
    attributes = [Name, Age, Score]
    for attr_class in attributes:
        print(f"{attr_class.to_schema_definition()}")
    print("-" * 80)
    print()


def demonstrate_step2_entities():
    """Step 2: Define entities with ownership and cardinality."""
    print("=" * 80)
    print("STEP 2: Defining Entity Types")
    print("=" * 80)
    print()
    print("Entities own attributes with specific cardinality constraints:")
    print("  • Flag(Key) - exactly one, used as key (@key)")
    print("  • Type - exactly one by default (@card(1..1))")
    print("  • Type | None - zero or one (@card(0..1))")
    print("  • list[Type] = Flag(Card(1, 5)) - one to five (@card(1..5))")
    print()

    print("Python Code:")
    print("-" * 80)
    print("""
class Person(Entity):
    flags = TypeFlags(type_name="person")

    name: Name = Flag(Key)  # @key - exactly one, marked as key
    age: Age | None         # @card(0..1) - zero or one (optional)
    email: Email            # @card(1..1) - exactly one (default)
    score: Score            # @card(1..1) - exactly one (default)

class Company(Entity):
    flags = TypeFlags(type_name="company")

    name: Name = Flag(Key)                      # @key
    industry: list[Industry] = Flag(Card(1, 5)) # @card(1..5)
""")
    print("-" * 80)
    print()

    print("Generated TypeQL Schema:")
    print("-" * 80)
    print(Person.to_schema_definition())
    print()
    print(Company.to_schema_definition())
    print("-" * 80)
    print()


def demonstrate_step3_relations():
    """Step 3: Define relations with roles and attributes."""
    print("=" * 80)
    print("STEP 3: Defining Relation Types")
    print("=" * 80)
    print()
    print("Relations connect entities through roles and can own attributes.")
    print("  • Role[EntityType] defines which entities can play which roles")
    print("  • Relations can own attributes just like entities")
    print()

    print("Python Code:")
    print("-" * 80)
    print("""
class Employment(Relation):
    flags = TypeFlags(type_name="employment")

    # Roles - using generic Role[T] for type safety
    employee: Role[Person] = Role("employee", Person)
    employer: Role[Company] = Role("employer", Company)

    # Owned attributes with cardinality
    position: Position      # @card(1..1) - exactly one (default)
    salary: Salary | None   # @card(0..1) - zero or one (optional)
""")
    print("-" * 80)
    print()

    print("Generated TypeQL Schema:")
    print("-" * 80)
    print(Employment.to_schema_definition())
    print()
    print("# Role player definitions:")
    for role_name, role in Employment._roles.items():
        relation_name = Employment.get_type_name()
        print(f"{role.player_type} plays {relation_name}:{role.role_name};")
    print("-" * 80)
    print()


def demonstrate_step4_instance_creation():
    """Step 4: Create instances and generate insert queries."""
    print("=" * 80)
    print("STEP 4: Creating Entity Instances")
    print("=" * 80)
    print()
    print("Instances are created by calling the class constructor with attribute values.")
    print("TypeBridge automatically generates TypeQL insert queries.")
    print()

    print("Example 1: Creating a Person")
    print("-" * 80)
    print("Python Code:")
    print("""
alice = Person(
    name=Name("Alice Johnson"),
    age=Age(30),
    email=Email("alice@example.com"),
    score=Score(95.5)
)
""")

    alice = Person(
        name=Name("Alice Johnson"), age=Age(30), email=Email("alice@example.com"), score=Score(95.5)
    )

    print("\nGenerated TypeQL Insert Query:")
    print(f"insert {alice.to_insert_query()}")
    print("-" * 80)
    print()

    print("Example 2: Creating a Company with Multiple Industries")
    print("-" * 80)
    print("Python Code:")
    print("""
techcorp = Company(
    name=Name("TechCorp"),
    industry=[
        Industry("Technology"),
        Industry("Software"),
        Industry("AI"),
    ]
)
""")

    techcorp = Company(
        name=Name("TechCorp"),
        industry=[
            Industry("Technology"),
            Industry("Software"),
            Industry("AI"),
        ],
    )

    print("\nGenerated TypeQL Insert Query:")
    print(f"insert {techcorp.to_insert_query()}")
    print("-" * 80)
    print()

    print("Example 3: Creating an Employment Relation")
    print("-" * 80)
    print("Python Code:")
    print("""
# First, we need person and company instances
employment = Employment(
    employee=alice,
    employer=techcorp,
    position=Position("Software Engineer"),
    salary=Salary(120000)
)
""")

    employment = Employment(
        employee=alice,
        employer=techcorp,
        position=Position("Software Engineer"),
        salary=Salary(120000),
    )

    print("\nGenerated TypeQL Insert Query:")
    print(f"insert {employment.to_insert_query()}")
    print("-" * 80)
    print()


def demonstrate_step5_complete_schema():
    """Step 5: Show the complete TypeQL schema."""
    print("=" * 80)
    print("STEP 5: Complete TypeQL Schema Definition")
    print("=" * 80)
    print()
    print("This is the full TypeQL schema that will be synced to TypeDB.")
    print("It includes all attributes, entities, relations, and role players.")
    print()

    print("Complete TypeQL Schema:")
    print("-" * 80)
    print("define\n")

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

    print("-" * 80)
    print()


def main():
    """Run CRUD Part 1: Schema Definition Only."""
    print()
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 15 + "CRUD Tutorial Part 1: Schema Definition" + " " * 23 + "║")
    print("╚" + "═" * 78 + "╝")
    print()

    # Step-by-step schema definition demonstrations
    demonstrate_step1_attributes()
    input("Press Enter to continue to Step 2...")
    print()

    demonstrate_step2_entities()
    input("Press Enter to continue to Step 3...")
    print()

    demonstrate_step3_relations()
    input("Press Enter to continue to Step 4...")
    print()

    demonstrate_step4_instance_creation()
    input("Press Enter to continue to Step 5...")
    print()

    demonstrate_step5_complete_schema()
    input("Press Enter to continue to database setup...")
    print()

    # Connect to database
    print("=" * 80)
    print("STEP 6: Database Setup and Schema Sync")
    print("=" * 80)
    print()

    print("Python Code:")
    print("-" * 80)
    print("""
# Connect to TypeDB
db = Database(address="localhost:1729", database="crud_demo")
db.connect()

# Create database (delete if exists)
if db.database_exists():
    db.delete_database()
db.create_database()

# Register models and sync schema
schema_manager = SchemaManager(db)
schema_manager.register(Person, Company, Employment)
schema_manager.sync_schema()
""")
    print("-" * 80)
    print()

    print("Executing...")
    print()

    db = Database(address="localhost:1729", database="crud_demo")
    db.connect()
    print("✓ Connected to TypeDB at localhost:1729")

    # Clean slate for fresh start
    if db.database_exists():
        db.delete_database()
        print("✓ Deleted existing 'crud_demo' database")

    db.create_database()
    print("✓ Created database 'crud_demo'")
    print()

    # Set up schema
    print("Syncing schema to database...")
    schema_manager = SchemaManager(db)
    schema_manager.register(Person, Company, Employment)
    schema_manager.sync_schema()
    print("✓ Schema synced successfully!")
    print()
    print("The TypeQL schema shown in Step 5 has been executed in TypeDB.")
    print()

    # Don't delete database - keep it for next example!
    db.close()
    print("✓ Database connection closed")
    print()
    print("=" * 80)
    print("✓ Tutorial Part 1 Complete!")
    print("=" * 80)
    print()
    print("What we accomplished:")
    print("  ✓ Defined attribute, entity, and relation types")
    print("  ✓ Generated TypeQL schema definitions")
    print("  ✓ Created TypeDB database 'crud_demo'")
    print("  ✓ Synced schema to database")
    print()
    print("Next step: Run crud_02_insert.py to insert data")
    print("=" * 80)


if __name__ == "__main__":
    main()

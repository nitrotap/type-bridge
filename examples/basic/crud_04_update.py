"""CRUD Tutorial Part 4: Updating Entities.

This example demonstrates:
- Connecting to the existing "crud_demo" database (with data from crud_01, crud_02, crud_03)
- Updating single-value attributes (@card(0..1) or @card(1..1))
- Updating multi-value attributes (e.g., @card(1..5))
- The Fetch → Modify → Update pattern
- Generated TypeQL update queries

TypeDB update semantics:
- Single-value attributes: Use TypeQL 'update' clause
- Multi-value attributes: Delete old values, then insert new ones

Prerequisites: Run crud_01_define.py, crud_02_insert.py, and crud_03_read.py first.
"""

from type_bridge import (
    Card,
    Database,
    Double,
    Entity,
    EntityFlags,
    Flag,
    Integer,
    Key,
    String,
)


# Define attribute types (must match crud_01_define.py schema)
class Name(String):
    """Name attribute."""


class Email(String):
    """Email attribute."""


class Age(Integer):
    """Age attribute."""


class Score(Double):
    """Score attribute."""


class Industry(String):
    """Industry attribute."""


# Define entities (must match crud_01_define.py schema)
class Person(Entity):
    """Person entity with single and multi-value attributes."""

    flags = EntityFlags(type_name="person")

    # Single-value attributes
    name: Name = Flag(Key)  # @key (implies @card(1..1))
    age: Age | None  # @card(0..1) - optional single value
    email: Email  # @card(1..1) - required single value
    score: Score  # @card(1..1) - required single value


class Company(Entity):
    """Company entity with multi-value attribute."""

    flags = EntityFlags(type_name="company")

    name: Name = Flag(Key)  # @key
    industry: list[Industry] = Flag(Card(1, 5))  # @card(1..5) - 1 to 5 industries


def demonstrate_update_single_value(db: Database):
    """Step 1: Demonstrate updating single-value attributes."""
    print("=" * 80)
    print("STEP 1: Updating Single-Value Attributes")
    print("=" * 80)
    print()
    print("Single-value attributes use TypeQL 'update' clause.")
    print()

    person_manager = Person.manager(db)

    # Fetch entity
    print("Fetching Alice Johnson...")
    alice = person_manager.get(name="Alice Johnson")[0]
    print(
        f"  Before: {alice.name.value}, age={alice.age.value if alice.age else 'N/A'}, score={alice.score.value}"
    )
    print()

    # Modify single-value attributes
    print("Modifying attributes:")
    print("  • age: 30 → 31")
    print("  • score: 95.5 → 96.0")
    alice.age = Age(31)
    alice.score = Score(96.0)
    print()

    # Update in database
    print("Persisting changes to database...")
    person_manager.update(alice)
    print("✓ Update completed!")
    print()

    # Verify
    alice_updated = person_manager.get(name="Alice Johnson")[0]
    print(
        f"  After: {alice_updated.name.value}, age={alice_updated.age.value if alice_updated.age else 'N/A'}, score={alice_updated.score.value}"
    )
    print()


def demonstrate_update_multi_value(db: Database):
    """Step 2: Demonstrate updating multi-value attributes."""
    print("=" * 80)
    print("STEP 2: Updating Multi-Value Attributes")
    print("=" * 80)
    print()
    print("Multi-value attributes use TypeQL 'delete' + 'insert' clauses.")
    print()

    company_manager = Company.manager(db)

    # Fetch entity
    print("Fetching TechCorp...")
    techcorp = company_manager.get(name="TechCorp")[0]
    old_industries = [i.value for i in techcorp.industry]
    print(f"  Before: {techcorp.name.value}")
    print(f"    Industries: {', '.join(old_industries)}")
    print()

    # Modify multi-value attribute
    print("Modifying industries:")
    print("  • Adding: Machine Learning, Cloud Computing")
    print("  • Keeping: Technology, Software")
    techcorp.industry = [
        Industry("Technology"),
        Industry("Software"),
        Industry("Machine Learning"),
        Industry("Cloud Computing"),
    ]
    print()

    # Update in database
    print("Persisting changes to database...")
    company_manager.update(techcorp)
    print("✓ Update completed!")
    print()

    # Verify
    techcorp_updated = company_manager.get(name="TechCorp")[0]
    new_industries = [i.value for i in techcorp_updated.industry]
    print(f"  After: {techcorp_updated.name.value}")
    print(f"    Industries: {', '.join(sorted(new_industries))}")
    print()


def demonstrate_update_multiple_persons(db: Database):
    """Step 3: Demonstrate updating multiple persons."""
    print("=" * 80)
    print("STEP 3: Updating Multiple Persons")
    print("=" * 80)
    print()
    print("Update operations can be performed on multiple entities.")
    print()

    person_manager = Person.manager(db)

    # Update Bob
    print("Updating Bob Smith:")
    bob = person_manager.get(name="Bob Smith")[0]
    print(f"  Before: age={bob.age.value if bob.age else 'N/A'}, score={bob.score.value}")
    bob.age = Age(29)
    bob.score = Score(88.5)
    person_manager.update(bob)
    print(f"  After: age={bob.age.value if bob.age else 'N/A'}, score={bob.score.value}")
    print("  ✓ Updated")
    print()

    # Update Charlie
    print("Updating Charlie Davis:")
    charlie = person_manager.get(name="Charlie Davis")[0]
    print(
        f"  Before: age={charlie.age.value if charlie.age else 'N/A'}, score={charlie.score.value}"
    )
    charlie.age = Age(33)
    charlie.score = Score(93.0)
    person_manager.update(charlie)
    print(
        f"  After: age={charlie.age.value if charlie.age else 'N/A'}, score={charlie.score.value}"
    )
    print("  ✓ Updated")
    print()


def demonstrate_typical_workflow(db: Database):
    """Step 4: Demonstrate typical update workflow."""
    print("=" * 80)
    print("STEP 4: Typical Update Workflow (Fetch → Modify → Update)")
    print("=" * 80)
    print()
    print("The standard pattern: Fetch entity, modify in memory, persist to database.")
    print()

    person_manager = Person.manager(db)

    print("Workflow: Fetch → Modify → Update")
    print()

    # Step 1: Fetch
    print("Step 1: Fetch entity")
    diana = person_manager.get(name="Diana Evans")[0]
    print(f"  ✓ Fetched: {diana.name.value}")
    print()

    # Step 2: Modify
    print("Step 2: Modify attributes (in memory)")
    print("  • age: 27 → 28")
    print("  • score: 88.5 → 90.0")
    diana.age = Age(28)
    diana.score = Score(90.0)
    print("  ✓ Modified (not yet persisted)")
    print()

    # Step 3: Update
    print("Step 3: Persist changes to database")
    person_manager.update(diana)
    print("  ✓ Updated in database")
    print()

    # Verify
    diana_updated = person_manager.get(name="Diana Evans")[0]
    print(
        f"Verification: {diana_updated.name.value}, age={diana_updated.age.value if diana_updated.age else 'N/A'}, score={diana_updated.score.value}"
    )
    print()


def show_generated_typeql():
    """Step 5: Show example of generated TypeQL for updates."""
    print("=" * 80)
    print("STEP 5: Generated TypeQL Update Queries")
    print("=" * 80)
    print()
    print("TypeBridge generates different TypeQL for single vs. multi-value attributes.")
    print()

    print("For single-value attributes (age, score):")
    print("```typeql")
    print("match")
    print('$e isa person, has name "Alice Johnson";')
    print("update")
    print("$e has age 31;")
    print("$e has score 96.0;")
    print("```")
    print()

    print("For multi-value attributes (industry):")
    print("```typeql")
    print("match")
    print('$e isa company, has name "TechCorp";')
    print("$e has industry $industry;")
    print("delete")
    print("$industry of $e;")
    print("insert")
    print('$e has industry "Technology";')
    print('$e has industry "Software";')
    print('$e has industry "Machine Learning";')
    print('$e has industry "Cloud Computing";')
    print("```")
    print()


def show_final_state(db: Database):
    """Show final state of database."""
    print("=" * 80)
    print("Final Database State")
    print("=" * 80)
    print()

    person_manager = Person.manager(db)
    company_manager = Company.manager(db)

    # Show updated persons
    print("Updated Persons:")
    updated_persons = ["Alice Johnson", "Bob Smith", "Charlie Davis", "Diana Evans"]
    for name in updated_persons:
        person = person_manager.get(name=name)[0]
        print(
            f"  • {person.name.value}: age={person.age.value if person.age else 'N/A'}, score={person.score.value}"
        )
    print()

    # Show updated companies
    print("Updated Companies:")
    techcorp = company_manager.get(name="TechCorp")[0]
    industries = [i.value for i in techcorp.industry]
    print(f"  • {techcorp.name.value}: {', '.join(sorted(industries))}")
    print()

    print("Database 'crud_demo' updates complete!")
    print()


def main():
    """Run CRUD Part 4: Updating Entities."""
    print()
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 16 + "CRUD Tutorial Part 4: Updating Entities" + " " * 22 + "║")
    print("╚" + "═" * 78 + "╝")
    print()

    # Connect to existing database
    db = Database(address="localhost:1729", database="crud_demo")
    db.connect()
    print("✓ Connected to existing 'crud_demo' database")
    print()

    if not db.database_exists():
        print("❌ ERROR: Database 'crud_demo' does not exist!")
        print("   Please run crud_01_define.py, crud_02_insert.py, and crud_03_read.py first.")
        return

    # Run demonstrations
    demonstrate_update_single_value(db)
    demonstrate_update_multi_value(db)
    demonstrate_update_multiple_persons(db)
    demonstrate_typical_workflow(db)
    show_generated_typeql()
    show_final_state(db)

    # Tutorial complete
    print("=" * 80)
    print("CRUD Tutorial Series Complete!")
    print("=" * 80)
    print()
    print("=" * 80)
    print("Verify in TypeDB Studio")
    print("=" * 80)
    print()
    print("match")
    print("  $emp isa employment (employee: $person, employer: $company);")
    print("  $company has name 'TechCorp';")
    print("fetch {")
    print('  "employee": {$person.*},')
    print('  "employer": {$company.*},')
    print('  "position": $emp.position,')
    print('  "salary": $emp.salary')
    print("};")
    print()
    print("-" * 80)
    print()

    # Ask user if they want to delete the database
    delete_db = input("Delete 'crud_demo' database? [y/N]: ").strip().lower()
    if delete_db in ("y", "yes"):
        print("Cleaning up: Deleting 'crud_demo' database...")
        db.delete_database()
        print("✓ Database deleted")
        print()
        print("To restart the tutorial series, run crud_01_define.py")
    else:
        print("Database 'crud_demo' preserved.")
        print()
        print("To restart the tutorial:")
        print("  1. Manually delete the database, or")
        print("  2. Run crud_01_define.py (it will delete and recreate)")
    print()

    db.close()
    print("✓ Connection closed")


if __name__ == "__main__":
    main()

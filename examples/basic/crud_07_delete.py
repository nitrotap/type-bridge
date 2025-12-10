"""CRUD Tutorial Part 7: Deleting Data.

This example demonstrates:
- Deleting entities by instance (v0.7.1+ API)
- Deleting entities with filters using filter().delete()
- Deleting relations by instance
- Using instance delete method: entity.delete(db)
- Understanding delete return values

Prerequisites: Run crud_01_define.py and crud_02_insert.py first.
"""

from type_bridge import (
    Card,
    Database,
    Double,
    Entity,
    Flag,
    Integer,
    Key,
    Relation,
    Role,
    String,
    TypeFlags,
)


# Define attribute types (must match crud_01_define.py schema)
class Name(String):
    pass


class Email(String):
    pass


class Age(Integer):
    pass


class Score(Double):
    pass


class Position(String):
    pass


class Salary(Integer):
    pass


class Industry(String):
    pass


# Define entities (must match crud_01_define.py schema)
class Person(Entity):
    flags: TypeFlags = TypeFlags(name="person")

    name: Name = Flag(Key)
    age: Age | None
    email: Email
    score: Score


class Company(Entity):
    flags: TypeFlags = TypeFlags(name="company")

    name: Name = Flag(Key)
    industry: list[Industry] = Flag(Card(1, 5))


# Define relation (must match crud_01_define.py schema)
class Employment(Relation):
    flags: TypeFlags = TypeFlags(name="employment")

    employee: Role[Person] = Role("employee", Person)
    employer: Role[Company] = Role("employer", Company)

    position: Position
    salary: Salary | None


def demonstrate_delete_by_instance(db: Database):
    """Step 1: Demonstrate deleting by entity instance."""
    print("=" * 80)
    print("STEP 1: Delete by Entity Instance")
    print("=" * 80)
    print()
    print("In v0.7.1+, delete takes an entity instance (like insert and update).")
    print()

    person_manager = Person.manager(db)

    # Show current persons
    print("Current persons:")
    all_persons = person_manager.all()
    for person in sorted(all_persons, key=lambda p: p.name.value):
        print(f"  • {person.name.value}")
    print(f"  Total: {len(all_persons)} persons")
    print()

    # Delete by instance
    print("Python Code:")
    print("-" * 80)
    print("""
# Step 1: Get the entity instance
frank = person_manager.get(name="Frank Garcia")[0]

# Step 2: Delete using the instance
deleted = person_manager.delete(frank)  # Returns the deleted entity
""")
    print("-" * 80)
    print()

    print("Executing...")
    frank_list = person_manager.get(name="Frank Garcia")
    if frank_list:
        frank = frank_list[0]
        deleted = person_manager.delete(frank)
        print(f"\n✓ Deleted: {deleted.name.value}")
    else:
        print("\n⚠ Frank Garcia not found (may have been deleted already)")
    print()

    # Show remaining persons
    print("Remaining persons:")
    remaining = person_manager.all()
    for person in sorted(remaining, key=lambda p: p.name.value):
        print(f"  • {person.name.value}")
    print(f"  Total: {len(remaining)} persons")
    print()
    input("Press Enter to continue...")
    print()


def demonstrate_delete_with_filters(db: Database):
    """Step 2: Demonstrate deleting with filters."""
    print("=" * 80)
    print("STEP 2: Delete with Filters")
    print("=" * 80)
    print()
    print("You can delete multiple entities using filter conditions.")
    print()

    person_manager = Person.manager(db)

    # Show current persons
    print("Current persons:")
    all_persons = person_manager.all()
    for person in sorted(all_persons, key=lambda p: p.name.value):
        age_val = person.age.value if person.age else 0
        print(f"  • {person.name.value}: {age_val} years old, score: {person.score.value}")
    print()

    # Delete using expression filter
    print("Python Code:")
    print("-" * 80)
    print("""
# Delete persons with low scores (< 88.0)
deleted = person_manager.filter(Score.lt(Score(88.0))).delete()
""")
    print("-" * 80)
    print()

    print("Executing...")
    deleted = person_manager.filter(Score.lt(Score(88.0))).delete()
    print(f"\n✓ Deleted {deleted} person(s)")
    print()

    # Show remaining persons
    print("Remaining persons:")
    remaining = person_manager.all()
    for person in sorted(remaining, key=lambda p: p.name.value):
        age_val = person.age.value if person.age else 0
        print(f"  • {person.name.value}: {age_val} years old, score: {person.score.value}")
    print(f"  Total: {len(remaining)} persons")
    print()
    input("Press Enter to continue...")
    print()


def demonstrate_delete_relations(db: Database):
    """Step 3: Demonstrate deleting relations."""
    print("=" * 80)
    print("STEP 3: Delete Relations")
    print("=" * 80)
    print()
    print("Relations can be deleted just like entities.")
    print()

    employment_manager = Employment.manager(db)

    # Show current employment relations
    print("Current employment relations:")
    all_jobs = employment_manager.all()
    for job in all_jobs:
        salary_val = job.salary.value if job.salary else 0
        print(f"  • {job.employee.name.value} @ {job.employer.name.value}: ${salary_val:,}")
    print(f"  Total: {len(all_jobs)} employment relations")
    print()

    # Delete low-paying jobs
    print("Python Code:")
    print("-" * 80)
    print("""
# Delete employment relations with salary < $110,000
deleted = employment_manager.filter(Salary.lt(Salary(110000))).delete()
""")
    print("-" * 80)
    print()

    print("Executing...")
    deleted = employment_manager.filter(Salary.lt(Salary(110000))).delete()
    print(f"\n✓ Deleted {deleted} employment relation(s)")
    print()

    # Show remaining employment relations
    print("Remaining employment relations:")
    remaining = employment_manager.all()
    for job in remaining:
        salary_val = job.salary.value if job.salary else 0
        print(f"  • {job.employee.name.value} @ {job.employer.name.value}: ${salary_val:,}")
    print(f"  Total: {len(remaining)} employment relations")
    print()
    input("Press Enter to continue...")
    print()


def demonstrate_delete_return_values(db: Database):
    """Step 4: Demonstrate delete return values."""
    print("=" * 80)
    print("STEP 4: Delete Return Values")
    print("=" * 80)
    print()
    print("Instance delete returns the deleted entity/relation.")
    print("Filter delete returns the count of deleted items.")
    print()

    person_manager = Person.manager(db)

    # Instance delete returns the entity
    print("Instance delete returns the entity:")
    print("-" * 80)
    print("""
# Instance-based delete returns the entity
alice = person_manager.get(name="Alice")[0]
deleted = person_manager.delete(alice)
print(deleted.name.value)  # "Alice"
""")
    print()

    # Filter delete returns count
    print("Filter delete returns count:")
    print("-" * 80)
    deleted = person_manager.filter(Age.gt(Age(1000))).delete()
    print(f"✓ Deleted {deleted} person(s)")
    print("  (filter().delete() returns 0 if no matches)")
    print()

    # Show safe deletion pattern
    print("Safe deletion pattern:")
    print("-" * 80)
    print("""
# Check before deleting with filter
target = person_manager.filter(Score.lt(Score(90.0))).execute()
if target:
    print(f"About to delete {len(target)} person(s)")
    deleted = person_manager.filter(Score.lt(Score(90.0))).delete()
    print(f"Deleted {deleted} person(s)")
else:
    print("No persons match the criteria")

# Or use instance delete for single entities
person = person_manager.get(name="Alice")[0]
if person:
    deleted = person_manager.delete(person)  # Returns the entity
""")
    print()
    input("Press Enter to continue...")
    print()


def demonstrate_delete_cascade(db: Database):
    """Step 5: Demonstrate deletion behavior with relations."""
    print("=" * 80)
    print("STEP 5: Deletion and Relations")
    print("=" * 80)
    print()
    print("Important: In TypeDB, deleting an entity that plays a role in")
    print("relations may have different behaviors depending on configuration.")
    print()

    person_manager = Person.manager(db)
    employment_manager = Employment.manager(db)

    # Show current state
    print("Current state:")
    persons = person_manager.all()
    jobs = employment_manager.all()
    print(f"  Persons: {len(persons)}")
    print(f"  Employment relations: {len(jobs)}")
    print()

    # Note about cascade behavior
    print("Note:")
    print("-" * 80)
    print("In this tutorial, we delete relations before entities to avoid")
    print("issues with dangling references. In production:")
    print()
    print("  1. Delete relations that reference the entity first, OR")
    print("  2. Configure cascade deletion in your TypeDB schema, OR")
    print("  3. Use transactions to ensure atomicity")
    print()
    print("Example: To delete a person with their employment relations:")
    print()
    print("""
# First find the person
alice = person_manager.get(name="Alice Johnson")[0]

# Then delete their employment relations using filter
employment_manager.filter(employee=alice).delete()

# Finally delete the person using instance delete
person_manager.delete(alice)

# OR use instance method
alice.delete(db)
""")
    print()
    input("Press Enter to continue...")
    print()


def show_delete_summary(db: Database):
    """Show summary of delete capabilities."""
    print("=" * 80)
    print("Delete Operations Summary")
    print("=" * 80)
    print()

    person_manager = Person.manager(db)
    employment_manager = Employment.manager(db)
    company_manager = Company.manager(db)

    # Show final state
    persons = person_manager.all()
    jobs = employment_manager.all()
    companies = company_manager.all()

    print("Final database state:")
    print(f"  Persons: {len(persons)}")
    print(f"  Companies: {len(companies)}")
    print(f"  Employment relations: {len(jobs)}")
    print()

    print("Delete Methods Available (v0.7.1+):")
    print("  .delete(entity) - Delete by instance, returns deleted entity")
    print("  .delete_many([entities]) - Delete multiple, returns deleted list")
    print("  entity.delete(db) - Instance method, returns self")
    print("  .filter(...).delete() - Filter-based deletion, returns count")
    print()

    print("Best Practices:")
    print("  ✓ Instance delete returns the entity, filter delete returns count")
    print("  ✓ Use instance delete for single entities (safer)")
    print("  ✓ Use filter().delete() for bulk conditional deletion")
    print("  ✓ Delete relations before deleting entities they reference")
    print("  ✓ Entity must have @key or match exactly 1 record")
    print()


def main():
    """Run CRUD Part 7: Deleting Data."""
    print()
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "CRUD Tutorial Part 7: Deleting Data" + " " * 23 + "║")
    print("╚" + "═" * 78 + "╝")
    print()

    # Connect to existing database
    db = Database(address="localhost:1729", database="crud_demo")
    db.connect()
    print("✓ Connected to existing 'crud_demo' database")
    print()

    if not db.database_exists():
        print("❌ ERROR: Database 'crud_demo' does not exist!")
        print("   Please run crud_01_define.py and crud_02_insert.py first.")
        return

    # Run demonstrations
    demonstrate_delete_by_instance(db)
    demonstrate_delete_with_filters(db)
    demonstrate_delete_relations(db)
    demonstrate_delete_return_values(db)
    demonstrate_delete_cascade(db)
    show_delete_summary(db)

    # Clean up
    print("=" * 80)
    print("Tutorial complete! Cleaning up...")
    print("=" * 80)
    print()

    delete_db = input("Delete 'crud_demo' database? [y/N]: ").strip().lower()
    if delete_db in ("y", "yes"):
        print("Deleting 'crud_demo' database...")
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

    db.close()
    print("✓ Connection closed")
    print()
    print("=" * 80)
    print("✓ Delete tutorial complete!")
    print("=" * 80)
    print()
    print("What we learned:")
    print("  ✓ Deleting by entity instance with .delete(entity)")
    print("  ✓ Using instance method: entity.delete(db)")
    print("  ✓ Filter-based deletion with .filter().delete()")
    print("  ✓ Understanding delete return values (entity vs count)")
    print("  ✓ Best practices for deletion with relations")
    print()
    print("The basic CRUD tutorial series is complete!")
    print("Explore advanced/ examples for more features:")
    print("  • advanced/crud_07_chainable_operations.py - Advanced delete and update_with")
    print("  • advanced/query_01_expressions.py - Complex query patterns")
    print("=" * 80)


if __name__ == "__main__":
    main()

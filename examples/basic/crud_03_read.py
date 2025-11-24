"""CRUD Tutorial Part 3: Reading and Querying Data.

This example demonstrates:
- Connecting to the existing "crud_demo" database (with data from crud_01 and crud_02)
- EntityManager.get() with exact match attribute filters
- EntityManager.all() to fetch all entities
- EntityManager.filter() for chainable queries with limit(), offset(), first()
- RelationManager.get() with role player and attribute filters
- Query result counting

NOTE: Advanced filtering (range queries, comparisons, complex WHERE clauses) is WIP.
      Current workaround: Fetch all and filter in Python.

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


def demonstrate_get_all(db: Database):
    """Step 1: Demonstrate fetching all entities."""
    print("=" * 80)
    print("STEP 1: Fetching All Entities with all()")
    print("=" * 80)
    print()
    print("The all() method fetches all instances of an entity type.")
    print()

    print("Python Code:")
    print("-" * 80)
    print("""
person_manager = Person.manager(db)
all_persons = person_manager.all()

for person in all_persons:
    print(person.name.value, person.age.value)
""")
    print("-" * 80)
    print()

    person_manager = Person.manager(db)
    company_manager = Company.manager(db)

    print("Executing...")
    # Fetch all persons
    all_persons = person_manager.all()
    print(f"\nTotal persons: {len(all_persons)}")
    for person in sorted(all_persons, key=lambda p: p.name.value):
        print(f"  • {person.name.value}, {person.age.value if person.age else 'N/A'} years old")
    print()

    # Fetch all companies
    all_companies = company_manager.all()
    print(f"Total companies: {len(all_companies)}")
    for company in sorted(all_companies, key=lambda c: c.name.value):
        industries = [i.value for i in company.industry]
        print(f"  • {company.name.value}: {', '.join(industries)}")
    print()
    input("Press Enter to continue...")
    print()


def demonstrate_get_with_filters(db: Database):
    """Step 2: Demonstrate get() with attribute filters."""
    print("=" * 80)
    print("STEP 2: Fetching Entities with get() Filters")
    print("=" * 80)
    print()
    print("The get() method filters entities by attribute values.")
    print()
    print("⚠️  NOTE: Advanced filtering (range queries, comparisons, etc.) is WIP.")
    print("   Currently supports exact match filtering only.")
    print()

    person_manager = Person.manager(db)

    # Get specific person by name (key attribute)
    print("get(name='Alice Johnson'):")
    alice_results = person_manager.get(name="Alice Johnson")
    if alice_results:
        alice = alice_results[0]
        print(f"  ✓ Found: {alice.name.value} ({alice.email.value})")
        print(f"    Age: {alice.age.value if alice.age else 'N/A'}, Score: {alice.score.value}")
    print()

    # Get by email
    print("get(email='bob@example.com'):")
    bob_results = person_manager.get(email="bob@example.com")
    if bob_results:
        bob = bob_results[0]
        print(f"  ✓ Found: {bob.name.value}")
    print()

    # Get persons older than 30 (note: range queries are WIP)
    print("⚠️  WIP: Range queries (age > 30, score >= 90, etc.) are not yet supported.")
    print("Workaround: Fetch all and filter in Python:")
    print()
    all_persons = person_manager.all()
    older_persons = [p for p in all_persons if p.age and p.age.value > 30]
    print(f"  Persons older than 30: {len(older_persons)}")
    for person in older_persons:
        age_val = person.age.value if person.age else 0
        print(f"    • {person.name.value} ({age_val} years old)")
    print()


def demonstrate_filter_chaining(db: Database):
    """Step 3: Demonstrate filter() with chainable query methods."""
    print("=" * 80)
    print("STEP 3: Chainable Queries with filter()")
    print("=" * 80)
    print()
    print("The filter() method returns a chainable query object.")
    print()
    print("⚠️  NOTE: Filter criteria (WHERE clauses) are WIP.")
    print("   Currently supports limit(), offset(), first(), count() without filters.")
    print()

    person_manager = Person.manager(db)

    # Get first 3 persons
    print("filter().limit(3):")
    first_three = person_manager.filter().limit(3).execute()
    for person in first_three:
        print(f"  • {person.name.value}")
    print()

    # Get first person
    print("filter().first():")
    first_person = person_manager.filter().first()
    if first_person:
        print(f"  ✓ First person: {first_person.name.value}")
    print()

    # Count all persons
    print("filter().count():")
    person_count = person_manager.filter().count()
    print(f"  Total count: {person_count}")
    print()


def demonstrate_relation_queries(db: Database):
    """Step 4: Demonstrate querying relations."""
    print("=" * 80)
    print("STEP 4: Querying Relations")
    print("=" * 80)
    print()
    print("Relations can be queried by role players and attributes.")
    print()

    person_manager = Person.manager(db)
    company_manager = Company.manager(db)
    employment_manager = Employment.manager(db)

    # Get all employments
    print("All employment relations:")
    all_employments = employment_manager.all()
    print(f"  Total: {len(all_employments)}")
    for emp in all_employments:
        employee_name = emp.employee.name.value
        employer_name = emp.employer.name.value
        position = emp.position.value
        salary = emp.salary.value if emp.salary else "N/A"
        print(f"  • {employee_name} @ {employer_name} ({position}, ${salary})")
    print()

    # Get employments for a specific person
    print("Get employments for Alice Johnson:")
    alice = person_manager.get(name="Alice Johnson")[0]
    alice_jobs = employment_manager.get(employee=alice)
    for job in alice_jobs:
        print(f"  ✓ {job.employer.name.value} - {job.position.value}")
    print()

    # Get employments at a specific company
    print("Get employments at TechCorp:")
    techcorp = company_manager.get(name="TechCorp")[0]
    techcorp_employees = employment_manager.get(employer=techcorp)
    print(f"  TechCorp has {len(techcorp_employees)} employees:")
    for job in techcorp_employees:
        print(f"    • {job.employee.name.value} ({job.position.value})")
    print()


def demonstrate_complex_queries(db: Database):
    """Step 5: Demonstrate more complex query patterns."""
    print("=" * 80)
    print("STEP 5: Complex Query Patterns")
    print("=" * 80)
    print()
    print("Combining Python filtering with TypeBridge queries.")
    print()
    print("⚠️  NOTE: Complex TypeQL queries (aggregations, subqueries, etc.) are WIP.")
    print("   Current workaround: Fetch all and filter in Python.")
    print()

    person_manager = Person.manager(db)
    company_manager = Company.manager(db)
    employment_manager = Employment.manager(db)

    # Find all persons with high scores
    print("Persons with score >= 90:")
    all_persons = person_manager.all()
    high_scorers = [p for p in all_persons if p.score.value >= 90]
    for person in sorted(high_scorers, key=lambda p: p.score.value, reverse=True):
        print(f"  • {person.name.value}: {person.score.value}")
    print()

    # Find companies in Technology sector
    print("Companies in Technology sector:")
    all_companies = company_manager.all()
    tech_companies = [
        c for c in all_companies if any(ind.value == "Technology" for ind in c.industry)
    ]
    for company in tech_companies:
        print(f"  • {company.name.value}")
    print()

    # Find high-paying positions (salary >= 110000)
    print("High-paying positions (salary >= $110,000):")
    all_jobs = employment_manager.all()
    high_paying = [j for j in all_jobs if j.salary and j.salary.value >= 110000]
    for job in sorted(high_paying, key=lambda j: j.salary.value if j.salary else 0, reverse=True):
        salary_val = job.salary.value if job.salary else 0
        print(f"  • {job.employee.name.value}: ${salary_val} at {job.employer.name.value}")
    print()


def show_query_summary(db: Database):
    """Show final summary of database contents."""
    print("=" * 80)
    print("Database Query Summary")
    print("=" * 80)
    print()

    person_manager = Person.manager(db)
    company_manager = Company.manager(db)
    employment_manager = Employment.manager(db)

    print(f"✓ Total Persons: {person_manager.filter().count()}")
    print(f"✓ Total Companies: {company_manager.filter().count()}")
    print(f"✓ Total Employment Relations: {len(employment_manager.all())}")
    print()

    print("Database is ready for crud_04_update.py")
    print()


def main():
    """Run CRUD Part 3: Reading and Querying Data."""
    print()
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 13 + "CRUD Tutorial Part 3: Reading and Querying Data" + " " * 18 + "║")
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
    demonstrate_get_all(db)
    demonstrate_get_with_filters(db)
    demonstrate_filter_chaining(db)
    demonstrate_relation_queries(db)
    demonstrate_complex_queries(db)
    show_query_summary(db)

    # Don't delete database - keep it for next example!
    db.close()

    print("=" * 80)
    print("Query demonstrations complete!")
    print("=" * 80)
    print()
    print("What we learned:")
    print("  ✓ Getting all entities with .all()")
    print("  ✓ Dictionary-based filtering with .get()")
    print("  ✓ Chainable queries with .filter(), .limit(), .first()")
    print("  ✓ Querying relations and role players")
    print()
    print("Next steps:")
    print("  • crud_04_update.py - Learn about updating entities")
    print("  • crud_05_filter.py - Advanced filtering with query expressions")
    print("  • crud_06_aggregate.py - Aggregations and group-by queries")
    print("=" * 80)


if __name__ == "__main__":
    main()

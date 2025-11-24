"""CRUD Tutorial Part 5: Filtering with Query Expressions.

This example demonstrates:
- Type-safe filtering with query expressions
- Comparison operators (>, <, >=, <=, ==, !=)
- String operations (contains, like for regex)
- Combining multiple filters (AND logic)
- Using .first(), .limit(), .execute()

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


def demonstrate_comparison_filters(db: Database):
    """Step 1: Demonstrate comparison operators."""
    print("=" * 80)
    print("STEP 1: Comparison Filters (>, <, >=, <=, ==, !=)")
    print("=" * 80)
    print()
    print("Query expressions allow type-safe filtering with comparison operators.")
    print()

    person_manager = Person.manager(db)

    # Greater than
    print("Python Code:")
    print("-" * 80)
    print("""
# Find persons older than 30
older = person_manager.filter(Age.gt(Age(30))).execute()
""")
    print("-" * 80)
    print()

    print("Executing...")
    older_persons = person_manager.filter(Age.gt(Age(30))).execute()
    print(f"\n✓ Persons older than 30: {len(older_persons)}")
    for person in sorted(older_persons, key=lambda p: p.age.value if p.age else 0, reverse=True):
        age_val = person.age.value if person.age else 0
        print(f"  • {person.name.value}: {age_val} years old")
    print()

    # Exact match
    print("Exact match (age == 35):")
    print("-" * 80)
    age_35 = person_manager.filter(Age.eq(Age(35))).execute()
    print(f"✓ Found {len(age_35)} person(s) exactly 35 years old")
    for person in age_35:
        print(f"  • {person.name.value}")
    print()

    # Score comparison
    print("High scorers (score >= 90.0):")
    print("-" * 80)
    high_scorers = person_manager.filter(Score.gte(Score(90.0))).execute()
    print(f"✓ Found {len(high_scorers)} high scorer(s)")
    for person in sorted(high_scorers, key=lambda p: p.score.value, reverse=True):
        print(f"  • {person.name.value}: {person.score.value}")
    print()
    input("Press Enter to continue...")
    print()


def demonstrate_range_queries(db: Database):
    """Step 2: Demonstrate range queries (combining filters)."""
    print("=" * 80)
    print("STEP 2: Range Queries (Combining Multiple Filters)")
    print("=" * 80)
    print()
    print("Multiple filter expressions create AND conditions.")
    print()

    person_manager = Person.manager(db)

    # Age range: 25 <= age <= 40
    print("Python Code:")
    print("-" * 80)
    print("""
# Find persons aged 25-40 (inclusive)
mid_age = person_manager.filter(
    Age.gte(Age(25)),
    Age.lte(Age(40))
).execute()
""")
    print("-" * 80)
    print()

    print("Executing...")
    mid_age_persons = person_manager.filter(Age.gte(Age(25)), Age.lte(Age(40))).execute()
    print(f"\n✓ Persons aged 25-40: {len(mid_age_persons)}")
    for person in sorted(mid_age_persons, key=lambda p: p.age.value if p.age else 0):
        age_val = person.age.value if person.age else 0
        print(f"  • {person.name.value}: {age_val} years old, score: {person.score.value}")
    print()

    # Combined filters: age > 30 AND score > 85
    print("Combined conditions (age > 30 AND score > 85):")
    print("-" * 80)
    experienced_high_performers = person_manager.filter(
        Age.gt(Age(30)), Score.gt(Score(85.0))
    ).execute()
    print(f"✓ Found {len(experienced_high_performers)} experienced high performer(s)")
    for person in experienced_high_performers:
        age_val = person.age.value if person.age else 0
        print(f"  • {person.name.value}: {age_val} years old, score: {person.score.value}")
    print()
    input("Press Enter to continue...")
    print()


def demonstrate_string_filters(db: Database):
    """Step 3: Demonstrate string operations."""
    print("=" * 80)
    print("STEP 3: String Filters (contains, like)")
    print("=" * 80)
    print()
    print("String attributes support contains and like (regex) operations.")
    print()

    person_manager = Person.manager(db)

    # Contains
    print("Python Code:")
    print("-" * 80)
    print("""
# Find persons with '@example.com' email
example_users = person_manager.filter(
    Email.contains(Email("@example.com"))
).execute()
""")
    print("-" * 80)
    print()

    print("Executing...")
    example_users = person_manager.filter(Email.contains(Email("@example.com"))).execute()
    print(f"\n✓ Users with '@example.com' email: {len(example_users)}")
    for person in sorted(example_users, key=lambda p: p.name.value):
        print(f"  • {person.name.value}: {person.email.value}")
    print()

    # Like (regex) - names starting with specific letter
    print("Pattern matching with like (regex):")
    print("-" * 80)
    print("""
# Find names starting with 'A'
a_names = person_manager.filter(
    Name.like(Name("^A.*"))
).execute()
""")
    print()

    a_names = person_manager.filter(Name.like(Name("^A.*"))).execute()
    print(f"✓ Names starting with 'A': {len(a_names)}")
    for person in a_names:
        print(f"  • {person.name.value}")
    print()
    input("Press Enter to continue...")
    print()


def demonstrate_relation_filters(db: Database):
    """Step 4: Demonstrate filtering on relations."""
    print("=" * 80)
    print("STEP 4: Filtering Relations")
    print("=" * 80)
    print()
    print("Relations can be filtered by their owned attributes.")
    print()

    employment_manager = Employment.manager(db)

    # Filter by salary
    print("Python Code:")
    print("-" * 80)
    print("""
# Find high-paying jobs (salary >= 110000)
high_paying = employment_manager.filter(
    Salary.gte(Salary(110000))
).execute()
""")
    print("-" * 80)
    print()

    print("Executing...")
    high_paying = employment_manager.filter(Salary.gte(Salary(110000))).execute()
    print(f"\n✓ High-paying positions (>= $110k): {len(high_paying)}")
    for job in sorted(high_paying, key=lambda j: j.salary.value if j.salary else 0, reverse=True):
        salary_val = job.salary.value if job.salary else 0
        print(f"  • {job.employee.name.value} @ {job.employer.name.value}: ${salary_val:,}")
        print(f"    Position: {job.position.value}")
    print()

    # Filter by position (string contains)
    print("Filter by position (contains 'Engineer'):")
    print("-" * 80)
    engineers = employment_manager.filter(Position.contains(Position("Engineer"))).execute()
    print(f"✓ Engineering positions: {len(engineers)}")
    for job in engineers:
        print(f"  • {job.employee.name.value}: {job.position.value}")
    print()
    input("Press Enter to continue...")
    print()


def demonstrate_query_modifiers(db: Database):
    """Step 5: Demonstrate limit, offset, first."""
    print("=" * 80)
    print("STEP 5: Query Modifiers (limit, offset, first)")
    print("=" * 80)
    print()
    print("Control result set size with limit(), offset(), and first().")
    print()

    person_manager = Person.manager(db)

    # Limit
    print("Python Code:")
    print("-" * 80)
    print("""
# Get first 3 persons ordered by name
first_three = person_manager.filter().limit(3).execute()
""")
    print("-" * 80)
    print()

    first_three = person_manager.filter().limit(3).execute()
    print(f"✓ First 3 persons: {len(first_three)}")
    for person in first_three:
        print(f"  • {person.name.value}")
    print()

    # First with filter
    print("Get first high scorer (score > 90):")
    print("-" * 80)
    first_high_scorer = person_manager.filter(Score.gt(Score(90.0))).first()
    if first_high_scorer:
        print(f"✓ First high scorer: {first_high_scorer.name.value}")
        print(f"  Score: {first_high_scorer.score.value}")
    print()

    # Offset and limit (pagination)
    print("Pagination with offset and limit:")
    print("-" * 80)
    print("""
# Get second page (skip first 2, take 2)
page_2 = person_manager.filter().offset(2).limit(2).execute()
""")
    print()

    page_2 = person_manager.filter().offset(2).limit(2).execute()
    print(f"✓ Page 2 (offset=2, limit=2): {len(page_2)}")
    for person in page_2:
        print(f"  • {person.name.value}")
    print()


def show_filtering_summary(db: Database):
    """Show summary of filtering capabilities."""
    print("=" * 80)
    print("Filtering Summary")
    print("=" * 80)
    print()

    person_manager = Person.manager(db)
    employment_manager = Employment.manager(db)

    # Some quick stats using filters
    total_persons = len(person_manager.filter().execute())
    older_than_30 = len(person_manager.filter(Age.gt(Age(30))).execute())
    high_scorers = len(person_manager.filter(Score.gte(Score(90.0))).execute())
    high_paying_jobs = len(employment_manager.filter(Salary.gte(Salary(110000))).execute())

    print("Database Statistics:")
    print(f"  Total Persons: {total_persons}")
    print(f"  Persons > 30 years old: {older_than_30}")
    print(f"  High Scorers (>= 90): {high_scorers}")
    print(f"  High-Paying Jobs (>= $110k): {high_paying_jobs}")
    print()

    print("Filter Expressions Available:")
    print("  Comparison: .gt(), .gte(), .lt(), .lte(), .eq(), .neq()")
    print("  String: .contains(), .like() (regex)")
    print("  Modifiers: .limit(), .offset(), .first()")
    print("  Execution: .execute(), .count()")
    print()


def main():
    """Run CRUD Part 5: Filtering with Query Expressions."""
    print()
    print("╔" + "═" * 78 + "╗")
    print(
        "║" + " " * 10 + "CRUD Tutorial Part 5: Filtering with Query Expressions" + " " * 13 + "║"
    )
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
    demonstrate_comparison_filters(db)
    demonstrate_range_queries(db)
    demonstrate_string_filters(db)
    demonstrate_relation_filters(db)
    demonstrate_query_modifiers(db)
    show_filtering_summary(db)

    # Don't delete database - keep it for next example!
    db.close()

    print("=" * 80)
    print("✓ Filtering tutorial complete!")
    print("=" * 80)
    print()
    print("What we learned:")
    print("  ✓ Comparison operators for numbers and strings")
    print("  ✓ Range queries with multiple filters")
    print("  ✓ String operations (contains, regex)")
    print("  ✓ Filtering relations by attributes")
    print("  ✓ Query modifiers (limit, offset, first)")
    print()
    print("Next step: Run crud_06_aggregate.py to learn aggregations")
    print("=" * 80)


if __name__ == "__main__":
    main()

"""CRUD Tutorial Part 6: Aggregations and Grouping.

This example demonstrates:
- Database-side aggregations (count, avg, sum, max, min)
- Combining filters with aggregations
- Group-by queries for categorical analysis
- Practical use cases for business analytics

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


def demonstrate_count(db: Database):
    """Step 1: Demonstrate count() for counting results."""
    print("=" * 80)
    print("STEP 1: Counting with count()")
    print("=" * 80)
    print()
    print("The count() method returns the number of matching entities.")
    print()

    person_manager = Person.manager(db)
    employment_manager = Employment.manager(db)

    # Basic count
    print("Python Code:")
    print("-" * 80)
    print("""
# Count all persons
total_persons = person_manager.filter().count()
""")
    print("-" * 80)
    print()

    print("Executing...")
    total_persons = person_manager.filter().count()
    print(f"\n✓ Total persons: {total_persons}")
    print()

    # Count with filter
    print("Count with filter (age > 30):")
    print("-" * 80)
    print("""
older_count = person_manager.filter(Age.gt(Age(30))).count()
""")
    print()

    older_count = person_manager.filter(Age.gt(Age(30))).count()
    print(f"✓ Persons older than 30: {older_count}")
    print()

    # Count relations
    total_jobs = employment_manager.filter().count()
    print(f"✓ Total employment relations: {total_jobs}")
    print()
    input("Press Enter to continue...")
    print()


def demonstrate_basic_aggregations(db: Database):
    """Step 2: Demonstrate avg, sum, max, min."""
    print("=" * 80)
    print("STEP 2: Basic Aggregations (avg, sum, max, min)")
    print("=" * 80)
    print()
    print("Aggregations are computed in the database for efficiency.")
    print()

    person_manager = Person.manager(db)

    # Multiple aggregations at once
    print("Python Code:")
    print("-" * 80)
    print("""
# Get statistics about all persons
stats = person_manager.filter().aggregate(
    Age.avg(),
    Age.max(),
    Age.min(),
    Score.avg()
)
""")
    print("-" * 80)
    print()

    print("Executing...")
    stats = person_manager.filter().aggregate(Age.avg(), Age.max(), Age.min(), Score.avg())

    print("\n✓ Person Statistics:")
    print(f"  Average age: {stats.get('avg_age', 'N/A')}")
    print(f"  Maximum age: {stats.get('max_age', 'N/A')}")
    print(f"  Minimum age: {stats.get('min_age', 'N/A')}")
    print(f"  Average score: {stats.get('avg_score', 'N/A'):.2f}")
    print()

    # Note about return values
    print("Note: Results are returned as a dictionary:")
    print("-" * 80)
    print(f"  Result dict: {stats}")
    print("  Keys follow pattern: '<aggregation>_<attribute_name>'")
    print()
    input("Press Enter to continue...")
    print()


def demonstrate_filtered_aggregations(db: Database):
    """Step 3: Demonstrate combining filters with aggregations."""
    print("=" * 80)
    print("STEP 3: Filtered Aggregations")
    print("=" * 80)
    print()
    print("Combine filters with aggregations for targeted analysis.")
    print()

    person_manager = Person.manager(db)
    employment_manager = Employment.manager(db)

    # Filter + aggregate
    print("Python Code:")
    print("-" * 80)
    print("""
# Get average score for persons older than 30
older_stats = person_manager.filter(
    Age.gt(Age(30))
).aggregate(Score.avg(), Score.max())
""")
    print("-" * 80)
    print()

    print("Executing...")
    older_stats = person_manager.filter(Age.gt(Age(30))).aggregate(Score.avg(), Score.max())

    print("\n✓ Statistics for persons > 30 years old:")
    print(f"  Average score: {older_stats.get('avg_score', 'N/A'):.2f}")
    print(f"  Maximum score: {older_stats.get('max_score', 'N/A'):.2f}")
    print()

    # Salary statistics
    print("Salary statistics:")
    print("-" * 80)
    salary_stats = employment_manager.filter().aggregate(
        Salary.avg(), Salary.sum(), Salary.max(), Salary.min()
    )

    print("✓ Compensation Analysis:")
    print(f"  Average salary: ${salary_stats.get('avg_salary', 0):,}")
    print(f"  Total payroll: ${salary_stats.get('sum_salary', 0):,}")
    print(f"  Highest salary: ${salary_stats.get('max_salary', 0):,}")
    print(f"  Lowest salary: ${salary_stats.get('min_salary', 0):,}")
    print()

    # High earners (filter + aggregate)
    print("Statistics for high earners (salary >= $110k):")
    print("-" * 80)
    high_earner_stats = employment_manager.filter(Salary.gte(Salary(110000))).aggregate(
        Salary.avg()
    )
    high_earner_count = employment_manager.filter(Salary.gte(Salary(110000))).count()

    print(f"✓ Count: {high_earner_count}")
    print(f"  Average salary: ${high_earner_stats.get('avg_salary', 0):,}")
    print()
    input("Press Enter to continue...")
    print()


def demonstrate_group_by(db: Database):
    """Step 4: Demonstrate group-by queries."""
    print("=" * 80)
    print("STEP 4: Group-By Queries")
    print("=" * 80)
    print()
    print("Group results by attribute values for categorical analysis.")
    print()

    employment_manager = Employment.manager(db)

    # Group by position
    print("Python Code:")
    print("-" * 80)
    print("""
# Get salary statistics by position
position_stats = employment_manager.group_by(
    Employment.position
).aggregate(Salary.avg(), Salary.max())
""")
    print("-" * 80)
    print()

    print("Executing...")
    position_stats = employment_manager.group_by(Employment.position).aggregate(
        Salary.avg(), Salary.max()
    )

    print("\n✓ Salary by Position:")
    for position, stats in sorted(position_stats.items()):
        avg_sal = stats.get("avg_salary", 0)
        max_sal = stats.get("max_salary", 0)
        print(f"\n  {position}:")
        print(f"    Average salary: ${avg_sal:,}")
        print(f"    Maximum salary: ${max_sal:,}")
    print()
    input("Press Enter to continue...")
    print()


def demonstrate_practical_analytics(db: Database):
    """Step 5: Demonstrate practical business analytics scenarios."""
    print("=" * 80)
    print("STEP 5: Practical Business Analytics")
    print("=" * 80)
    print()
    print("Real-world use cases combining filters, aggregations, and grouping.")
    print()

    person_manager = Person.manager(db)
    employment_manager = Employment.manager(db)

    # Workforce demographics
    print("1. Workforce Demographics:")
    print("-" * 80)
    age_ranges = [
        ("Under 30", Age.lt(Age(30))),
        ("30-40", Age.gte(Age(30)), Age.lte(Age(40))),
        ("Over 40", Age.gt(Age(40))),
    ]

    for range_name, *filters in age_ranges:
        count = person_manager.filter(*filters).count()
        if count > 0:
            stats = person_manager.filter(*filters).aggregate(Score.avg())
            avg_score = stats.get("avg_score", 0)
            print(f"  {range_name}: {count} person(s), avg score: {avg_score:.2f}")
    print()

    # Performance distribution
    print("2. Performance Distribution:")
    print("-" * 80)
    perf_levels = [
        ("Excellent (>= 95)", Score.gte(Score(95.0))),
        ("Good (85-94)", Score.gte(Score(85.0)), Score.lt(Score(95.0))),
        ("Satisfactory (< 85)", Score.lt(Score(85.0))),
    ]

    for level_name, *filters in perf_levels:
        count = person_manager.filter(*filters).count()
        print(f"  {level_name}: {count} person(s)")
    print()

    # Compensation insights
    print("3. Compensation Insights:")
    print("-" * 80)

    # All jobs with salary
    jobs_with_salary = employment_manager.filter().execute()
    jobs_with_salary = [j for j in jobs_with_salary if j.salary]

    if jobs_with_salary:
        total_payroll_stats = employment_manager.filter().aggregate(Salary.sum())
        avg_salary_stats = employment_manager.filter().aggregate(Salary.avg())

        print(f"  Total positions: {len(jobs_with_salary)}")
        print(f"  Total payroll: ${total_payroll_stats.get('sum_salary', 0):,}")
        print(f"  Average salary: ${avg_salary_stats.get('avg_salary', 0):,}")

        # Salary distribution
        high_paying = employment_manager.filter(Salary.gte(Salary(110000))).count()
        mid_range = employment_manager.filter(
            Salary.gte(Salary(90000)), Salary.lt(Salary(110000))
        ).count()

        print("\n  Salary Distribution:")
        print(f"    High (>= $110k): {high_paying}")
        print(f"    Mid ($90k-$110k): {mid_range}")
    print()

    # Top performers compensation check
    print("4. Top Performers Compensation Check:")
    print("-" * 80)

    # Get all persons and their jobs
    all_jobs = employment_manager.filter().execute()

    # Find high scorers
    high_scorers = person_manager.filter(Score.gte(Score(90.0))).execute()

    print(f"  High performers (score >= 90): {len(high_scorers)}")

    # Check their salaries
    for person in high_scorers:
        jobs = [j for j in all_jobs if j.employee.name.value == person.name.value]
        if jobs:
            job = jobs[0]
            salary = job.salary.value if job.salary else 0
            status = "✓" if salary >= 100000 else "⚠"
            print(
                f"    {status} {person.name.value}: score {person.score.value:.1f}, salary ${salary:,}"
            )
    print()


def show_aggregation_summary(db: Database):
    """Show summary of aggregation capabilities."""
    print("=" * 80)
    print("Aggregation Summary")
    print("=" * 80)
    print()

    person_manager = Person.manager(db)
    employment_manager = Employment.manager(db)

    # Quick comprehensive stats
    person_stats = person_manager.filter().aggregate(Age.avg(), Score.avg())
    salary_stats = employment_manager.filter().aggregate(Salary.avg(), Salary.sum())

    print("Overall Statistics:")
    print(f"  Total Persons: {person_manager.filter().count()}")
    print(f"  Average Age: {person_stats.get('avg_age', 'N/A')}")
    print(f"  Average Score: {person_stats.get('avg_score', 'N/A'):.2f}")
    print(f"  Total Employment Relations: {employment_manager.filter().count()}")
    print(f"  Average Salary: ${salary_stats.get('avg_salary', 0):,}")
    print(f"  Total Payroll: ${salary_stats.get('sum_salary', 0):,}")
    print()

    print("Aggregation Functions Available:")
    print("  .count() - Count matching entities")
    print("  .aggregate() - Compute avg, sum, max, min")
    print("  .group_by() - Group and aggregate by attribute")
    print()


def main():
    """Run CRUD Part 6: Aggregations and Grouping."""
    print()
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 12 + "CRUD Tutorial Part 6: Aggregations and Grouping" + " " * 17 + "║")
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
    demonstrate_count(db)
    demonstrate_basic_aggregations(db)
    demonstrate_filtered_aggregations(db)
    demonstrate_group_by(db)
    demonstrate_practical_analytics(db)
    show_aggregation_summary(db)

    # Don't delete database - keep it for future examples!
    db.close()

    print("=" * 80)
    print("✓ Aggregation tutorial complete!")
    print("=" * 80)
    print()
    print("What we learned:")
    print("  ✓ Counting with count()")
    print("  ✓ Basic aggregations (avg, sum, max, min)")
    print("  ✓ Combining filters with aggregations")
    print("  ✓ Group-by queries for categorical analysis")
    print("  ✓ Practical business analytics patterns")
    print()
    print("The CRUD tutorial series is complete!")
    print("Explore advanced/ examples for more features")
    print("=" * 80)


if __name__ == "__main__":
    main()

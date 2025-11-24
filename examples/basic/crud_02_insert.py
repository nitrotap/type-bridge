"""CRUD Tutorial Part 2: All Data Insertion.

This example demonstrates:
- Connecting to the existing "crud_demo" database (created in crud_01_define.py)
- Inserting initial data (Alice, Bob, TechCorp)
- Using insert_many() for efficient bulk insertions
- EntityManager.insert_many(entities: List[E])
- RelationManager.insert_many(relations: List[R])
- Populating the database with all tutorial data

Prerequisites: Run crud_01_define.py first to create the database and schema.
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


def insert_initial_data(db: Database):
    """Step 1: Insert initial data with detailed code and query display."""
    print("=" * 80)
    print("STEP 1: Inserting Initial Persons")
    print("=" * 80)
    print()

    person_manager = Person.manager(db)
    company_manager = Company.manager(db)
    employment_manager = Employment.manager(db)

    print("Python Code:")
    print("-" * 80)
    print("""
alice = Person(
    name=Name("Alice Johnson"),
    age=Age(30),
    email=Email("alice@example.com"),
    score=Score(95.5)
)

person_manager = Person.manager(db)
person_manager.insert(bob)
""")
    print("-" * 80)
    print()

    alice = Person(
        name=Name("Alice Johnson"),
        age=Age(30),
        email=Email("alice@example.com"),
        score=Score(95.5),
    )

    print("Generated TypeQL Insert Queries:")
    print("-" * 80)
    print(f"insert {alice.to_insert_query()}")
    print("-" * 80)
    print()

    print("Executing...")
    person_manager.insert(alice)
    print("✓ Inserted Alice Johnson")
    print()
    input("Press Enter to continue...")
    print()

    print("=" * 80)
    print("STEP 2: Inserting Initial Company")
    print("=" * 80)
    print()

    print("Python Code:")
    print("-" * 80)
    print("""
techcorp = Company(
    name=Name("TechCorp"),
    industry=[
        Industry("Technology"),
        Industry("Software"),
        Industry("AI"),
    ]
)

company_manager = Company.manager(db)
company_manager.insert(techcorp)
""")
    print("-" * 80)
    print()

    techcorp = Company(
        name=Name("TechCorp"),
        industry=[
            Industry("Technology"),
            Industry("Software"),
            Industry("AI"),
        ],
    )

    print("Generated TypeQL Insert Query:")
    print("-" * 80)
    print(f"insert {techcorp.to_insert_query()}")
    print("-" * 80)
    print()

    print("Executing...")
    company_manager.insert(techcorp)
    print("✓ Inserted TechCorp")
    print()
    input("Press Enter to continue...")
    print()

    print("=" * 80)
    print("STEP 3: Creating Employment Relations")
    print("=" * 80)
    print()

    print("Python Code:")
    print("-" * 80)
    print("""
alice_job = Employment(
    employee=alice,
    employer=techcorp,
    position=Position("Software Engineer"),
    salary=Salary(120000)
)
employment_manager = Employment.manager(db)
employment_manager.insert(alice_job)
""")
    print("-" * 80)
    print()

    alice_job = Employment(
        employee=alice,
        employer=techcorp,
        position=Position("Software Engineer"),
        salary=Salary(120000),
    )

    print("Generated TypeQL Insert Queries:")
    print("-" * 80)
    print(f"insert {alice_job.to_insert_query()}")
    print("-" * 80)
    print()

    print("Executing...")
    employment_manager.insert(alice_job)
    print("✓ Created employment relation for Alice at TechCorp")
    print()
    persons = person_manager.all()
    for person in persons:
        print(f"  • {person}")
    print()
    companies = company_manager.all()
    for company in companies:
        print(f"  • {company}")
    print()
    employments = employment_manager.all()

    print(f"Total Employment Relations: {len(employments)}")
    for employment in employments:
        print(f"  • {employment}")
    print()

    input("Press Enter to continue...")
    print()


def bulk_insert_persons(db: Database):
    """Step 4: Demonstrate bulk person insertion."""
    print("=" * 80)
    print("STEP 4: Bulk Inserting Additional Persons")
    print("=" * 80)
    print()
    print("Using insert_many() for efficient bulk operations.")
    print()

    person_manager = Person.manager(db)

    # Create multiple persons at once
    persons = [
        Person(
            name=Name("Charlie Davis"),
            age=Age(32),
            email=Email("charlie@example.com"),
            score=Score(92.0),
        ),
        Person(
            name=Name("Diana Evans"),
            age=Age(27),
            email=Email("diana@example.com"),
            score=Score(88.5),
        ),
        Person(
            name=Name("Eve Foster"),
            age=Age(35),
            email=Email("eve@example.com"),
            score=Score(94.2),
        ),
        Person(
            name=Name("Frank Garcia"),
            age=Age(29),
            email=Email("frank@example.com"),
            score=Score(86.7),
        ),
        Person(
            name=Name("Bob Smith"),
            age=Age(28),
            email=Email("bob@example.com"),
            score=Score(87.3),
        ),
    ]

    print(f"Inserting {len(persons)} persons in a single transaction...")
    person_manager.insert_many(persons)
    print("✓ Bulk insert completed!")
    print()
    persons = person_manager.all()
    print(f"Total Persons: {len(persons)}")

    for person in persons:
        print(f"  • {person}")
    print()


def bulk_insert_companies(db: Database):
    """Step 5: Demonstrate bulk company insertion."""
    print("=" * 80)
    print("STEP 5: Bulk Inserting Additional Companies")
    print("=" * 80)
    print()

    company_manager = Company.manager(db)

    companies = [
        Company(
            name=Name("DataCorp"),
            industry=[Industry("Data Science"), Industry("Analytics")],
        ),
        Company(
            name=Name("CloudSystems"),
            industry=[Industry("Cloud Computing"), Industry("Infrastructure")],
        ),
        Company(
            name=Name("AI Labs"),
            industry=[Industry("Artificial Intelligence"), Industry("Research")],
        ),
    ]

    print(f"Inserting {len(companies)} companies in a single transaction...")
    company_manager.insert_many(companies)
    print("✓ Bulk insert completed!")
    print()

    companies = company_manager.all()
    print(f"Total Companies: {len(companies)}")
    for company in companies:
        print(f"  • {company}")
    print()


def bulk_insert_employments(db: Database):
    """Step 6: Demonstrate bulk employment relation insertion."""
    print("=" * 80)
    print("STEP 6: Bulk Inserting Additional Employment Relations")
    print("=" * 80)
    print()

    person_manager = Person.manager(db)
    company_manager = Company.manager(db)
    employment_manager = Employment.manager(db)

    # Fetch persons and companies to create relations
    charlie = person_manager.get(name="Charlie Davis")[0]
    diana = person_manager.get(name="Diana Evans")[0]
    eve = person_manager.get(name="Eve Foster")[0]
    eve = person_manager.get(name="Eve Foster")[0]
    bob = person_manager.get(name="Bob Smith")[0]

    datacorp = company_manager.get(name="DataCorp")[0]
    cloudsystems = company_manager.get(name="CloudSystems")[0]
    ai_labs = company_manager.get(name="AI Labs")[0]
    techcorp = company_manager.get(name="TechCorp")[0]

    # Create employment relations
    employments = [
        Employment(
            employee=charlie,
            employer=datacorp,
            position=Position("Data Scientist"),
            salary=Salary(110000),
        ),
        Employment(
            employee=diana,
            employer=cloudsystems,
            position=Position("Cloud Engineer"),
            salary=Salary(105000),
        ),
        Employment(
            employee=eve,
            employer=ai_labs,
            position=Position("AI Researcher"),
            salary=Salary(130000),
        ),
        Employment(
            employee=bob,
            employer=techcorp,
            position=Position("Senior Developer"),
            salary=Salary(115000),
        ),
    ]

    print(f"Inserting {len(employments)} employment relations in a single transaction...")
    employment_manager.insert_many(employments)
    print("✓ Bulk insert completed!")
    print()
    employments = employment_manager.all()
    print(f"Total Employment Relations: {len(employments)}")
    for employment in employments:
        print(f"  • {employment}")
    print()


def show_database_summary(db: Database):
    """Show summary of all data in the database."""
    print("=" * 80)
    print("Database Summary")
    print("=" * 80)
    print()

    person_manager = Person.manager(db)
    company_manager = Company.manager(db)
    employment_manager = Employment.manager(db)

    all_persons = person_manager.all()
    all_companies = company_manager.all()
    all_employments = employment_manager.all()

    print(f"Total Persons: {len(all_persons)}")
    for person in sorted(all_persons, key=lambda p: p.name.value):
        print(f"  • {person.name.value} ({person.email.value})")
    print()

    print(f"Total Companies: {len(all_companies)}")
    for company in sorted(all_companies, key=lambda c: c.name.value):
        industries = [i.value for i in company.industry]
        print(f"  • {company.name.value} - {', '.join(industries)}")
    print()

    print(f"Total Employment Relations: {len(all_employments)}")
    employments = all_employments
    for employment in employments:
        print(f"  • {employment}")
    print()


def main():
    """Run CRUD Part 2: All Data Insertion."""
    print()
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 15 + "CRUD Tutorial Part 2: All Data Insertion" + " " * 22 + "║")
    print("╚" + "═" * 78 + "╝")
    print()

    # Connect to existing database
    db = Database(address="localhost:1729", database="crud_demo")
    db.connect()
    print("✓ Connected to existing 'crud_demo' database")
    print()

    if not db.database_exists():
        print("❌ ERROR: Database 'crud_demo' does not exist!")
        print("   Please run crud_01_define.py first to create the database.")
        return

    # Insert initial data (Alice, Bob, TechCorp)
    insert_initial_data(db)

    # Bulk insert additional data
    bulk_insert_persons(db)
    bulk_insert_companies(db)
    bulk_insert_employments(db)

    # Show summary
    show_database_summary(db)

    # Don't delete database - keep it for next example!
    db.close()

    print("=" * 80)
    print("Data insertion complete!")
    print("=" * 80)

    print("Database 'crud_demo' is ready for crud_03_read.py")
    print("=" * 80)


if __name__ == "__main__":
    main()

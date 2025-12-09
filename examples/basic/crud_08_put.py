"""CRUD Tutorial Part 8: PUT Operations (Idempotent Insert).

This example demonstrates:
- Using put() for idempotent single entity/relation insertion
- Using put_many() for bulk idempotent insertions
- Understanding PUT vs INSERT semantics
- All-or-nothing behavior of PUT operations
- Practical use cases for PUT operations

Prerequisites: Run crud_01_define.py first to create the database and schema.

PUT vs INSERT:
- INSERT: Always creates new instances (may cause duplicates or constraint violations)
- PUT: Idempotent - matches pattern first, inserts only if pattern doesn't exist
- PUT has "all-or-nothing" semantics - entire pattern must match or all is inserted
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
    salary: Salary


def main():
    """Demonstrate PUT operations with type-bridge."""
    # Connect to database
    db = Database(address="localhost:1729", database="crud_demo")
    db.connect()

    # Create managers
    person_manager = Person.manager(db)
    company_manager = Company.manager(db)
    employment_manager = Employment.manager(db)

    print("\n=== PUT Operations Demo ===\n")

    # -------------------------------------------------------------------------
    # Example 1: Single Entity PUT (Idempotent)
    # -------------------------------------------------------------------------
    print("1. Single Entity PUT - Idempotent Behavior")
    print("-" * 50)

    # Create a new person
    eva = Person(
        name=Name("Eva Martinez"),
        age=Age(29),
        email=Email("eva@example.com"),
        score=Score(88.5),
    )

    # First put - will insert since Eva doesn't exist
    print(f"First PUT: {eva.name.value}")
    person_manager.put(eva)
    count_1 = len(person_manager.get(name="Eva Martinez"))
    print(f"  → Persons named 'Eva Martinez': {count_1}")

    # Second put - idempotent, won't create duplicate
    print(f"\nSecond PUT (same data): {eva.name.value}")
    person_manager.put(eva)
    count_2 = len(person_manager.get(name="Eva Martinez"))
    print(f"  → Persons named 'Eva Martinez': {count_2} (no duplicate!)")

    assert count_1 == count_2 == 1, "PUT should be idempotent"

    # -------------------------------------------------------------------------
    # Example 2: Bulk Entity PUT
    # -------------------------------------------------------------------------
    print("\n2. Bulk Entity PUT - put_many()")
    print("-" * 50)

    # Create multiple new persons
    new_persons = [
        Person(
            name=Name("Frank Lee"),
            age=Age(32),
            email=Email("frank@example.com"),
            score=Score(90.0),
        ),
        Person(
            name=Name("Grace Kim"),
            age=Age(27),
            email=Email("grace@example.com"),
            score=Score(92.5),
        ),
    ]

    print(f"First put_many: {len(new_persons)} persons")
    person_manager.put_many(new_persons)
    count_before = len(person_manager.all())
    print(f"  → Total persons in database: {count_before}")

    # Second put_many - idempotent
    print(f"\nSecond put_many (same data): {len(new_persons)} persons")
    person_manager.put_many(new_persons)
    count_after = len(person_manager.all())
    print(f"  → Total persons in database: {count_after} (no duplicates!)")

    assert count_before == count_after, "put_many should be idempotent"

    # -------------------------------------------------------------------------
    # Example 3: Relation PUT
    # -------------------------------------------------------------------------
    print("\n3. Relation PUT - Idempotent Relationships")
    print("-" * 50)

    # Ensure we have entities to relate
    eva_fetched = person_manager.get(name="Eva Martinez")[0]
    frank_fetched = person_manager.get(name="Frank Lee")[0]

    # Ensure company exists
    startup_inc = Company(
        name=Name("StartupInc"),
        industry=[Industry("technology"), Industry("consulting")],
    )
    company_manager.put(startup_inc)
    startup_fetched = company_manager.get(name="StartupInc")[0]

    # Create employment relation
    eva_employment = Employment(
        employee=eva_fetched,
        employer=startup_fetched,
        position=Position("Data Scientist"),
        salary=Salary(95000),
    )

    print(f"First PUT: {eva_fetched.name.value} → {startup_fetched.name.value}")
    employment_manager.put(eva_employment)
    emp_count_1 = len(employment_manager.get(employee=eva_fetched))
    print(f"  → Eva's employments: {emp_count_1}")

    # Second put - idempotent
    print(f"\nSecond PUT (same relation): {eva_fetched.name.value} → {startup_fetched.name.value}")
    employment_manager.put(eva_employment)
    emp_count_2 = len(employment_manager.get(employee=eva_fetched))
    print(f"  → Eva's employments: {emp_count_2} (no duplicate!)")

    assert emp_count_1 == emp_count_2, "Relation PUT should be idempotent"

    # -------------------------------------------------------------------------
    # Example 4: Bulk Relation PUT
    # -------------------------------------------------------------------------
    print("\n4. Bulk Relation PUT - put_many()")
    print("-" * 50)

    # Create multiple employment relations
    new_employments = [
        Employment(
            employee=frank_fetched,
            employer=startup_fetched,
            position=Position("Backend Engineer"),
            salary=Salary(90000),
        ),
    ]

    print(f"First put_many: {len(new_employments)} employments")
    employment_manager.put_many(new_employments)
    total_emp_before = len(employment_manager.all())
    print(f"  → Total employments: {total_emp_before}")

    # Second put_many - idempotent
    print(f"\nSecond put_many (same data): {len(new_employments)} employments")
    employment_manager.put_many(new_employments)
    total_emp_after = len(employment_manager.all())
    print(f"  → Total employments: {total_emp_after} (no duplicates!)")

    assert total_emp_before == total_emp_after, "Relation put_many should be idempotent"

    # -------------------------------------------------------------------------
    # Example 5: PUT vs INSERT Comparison
    # -------------------------------------------------------------------------
    print("\n5. PUT vs INSERT - Understanding the Difference")
    print("-" * 50)

    test_person = Person(
        name=Name("TestUser"),
        age=Age(99),
        email=Email("test@example.com"),
        score=Score(0.0),
    )

    # Use INSERT - creates new instance every time
    print("Using INSERT twice:")
    person_manager.insert(test_person)
    count_after_first_insert = len(person_manager.get(name="TestUser"))
    print(f"  After 1st insert: {count_after_first_insert} TestUser(s)")

    # Note: Second insert would violate @key constraint on 'name'
    # So we can't demonstrate this without catching the error
    print("  (Second insert would violate @key constraint)")

    # Clean up test user
    person_manager.filter(name="TestUser").delete()

    # Use PUT - idempotent
    print("\nUsing PUT twice:")
    person_manager.put(test_person)
    count_after_first_put = len(person_manager.get(name="TestUser"))
    print(f"  After 1st put: {count_after_first_put} TestUser(s)")

    person_manager.put(test_person)
    count_after_second_put = len(person_manager.get(name="TestUser"))
    print(f"  After 2nd put: {count_after_second_put} TestUser(s) (idempotent!)")

    # Clean up
    person_manager.filter(name="TestUser").delete()

    # -------------------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------------------
    print("\n" + "=" * 50)
    print("PUT Operations Summary:")
    print("=" * 50)
    print("✓ PUT is idempotent - safe to run multiple times")
    print("✓ PUT matches entire pattern before inserting")
    print("✓ PUT is ideal for data loading and synchronization")
    print("✓ PUT has 'all-or-nothing' semantics")
    print("✓ Use PUT when you want to avoid duplicates")
    print("✓ Use INSERT when you always want to create new instances")

    print("\nUse Cases for PUT:")
    print("  • Data import scripts (run safely multiple times)")
    print("  • Ensuring reference data exists")
    print("  • Synchronization with external systems")
    print("  • Testing/demo data setup (idempotent)")

    db.close()
    print("\n✅ PUT operations demo complete!")


if __name__ == "__main__":
    main()

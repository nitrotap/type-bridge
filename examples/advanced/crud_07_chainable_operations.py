"""Advanced CRUD Example: Chainable Delete and Update Operations.

This example demonstrates:
- Chainable delete with expression filters
- Chainable update_with using lambda functions
- Chainable update_with using named functions
- Atomic transactions and error handling

New in v0.6.0: EntityQuery.delete() and EntityQuery.update_with()
"""

from type_bridge import (
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


class Age(Integer):
    pass


class Salary(Integer):
    pass


class Status(String):
    pass


class Department(String):
    pass


# Define entity
class Employee(Entity):
    flags: TypeFlags = TypeFlags(name="employee")
    name: Name = Flag(Key)
    email: Email
    age: Age
    salary: Salary
    status: Status
    department: Department


def demonstrate_chainable_delete(db: Database):
    """Demonstrate chainable delete operations."""
    print("=" * 80)
    print("CHAINABLE DELETE OPERATIONS")
    print("=" * 80)
    print()

    employee_mgr = Employee.manager(db)

    # Show current employees
    all_employees = employee_mgr.all()
    print(f"Current employees: {len(all_employees)}")
    for emp in all_employees:
        print(f"  - {emp.name.value}: {emp.age.value} years old, {emp.status.value}")
    print()

    # Delete employees approaching retirement (age > 60)
    print("1. Delete employees approaching retirement (age > 60)...")
    count = employee_mgr.filter(Age.gt(Age(60))).delete()
    print(f"   Deleted: {count} employee(s)")
    print()

    # Delete inactive junior employees
    print("2. Delete inactive junior employees (age < 25 AND status = inactive)...")
    count = employee_mgr.filter(Age.lt(Age(25)), Status.eq(Status("inactive"))).delete()
    print(f"   Deleted: {count} employee(s)")
    print()

    # Try to delete non-existent employees (age > 100)
    print("3. Try to delete very old employees (age > 100)...")
    count = employee_mgr.filter(Age.gt(Age(100))).delete()
    print(f"   Deleted: {count} employee(s) (returns 0 if no matches)")
    print()

    # Show remaining employees
    remaining = employee_mgr.all()
    print(f"Remaining employees: {len(remaining)}")
    for emp in remaining:
        print(f"  - {emp.name.value}: {emp.age.value} years old, {emp.status.value}")
    print()


def demonstrate_update_with_lambda(db: Database):
    """Demonstrate update_with using lambda functions."""
    print("=" * 80)
    print("UPDATE WITH LAMBDA FUNCTIONS")
    print("=" * 80)
    print()

    employee_mgr = Employee.manager(db)

    # Show current ages
    all_employees = employee_mgr.all()
    print("Current ages:")
    for emp in sorted(all_employees, key=lambda e: e.age.value):
        print(f"  - {emp.name.value}: {emp.age.value} years old")
    print()

    # Increment age for employees over 30 (birthday!)
    print("1. Celebrate birthdays for employees over 30...")
    updated = employee_mgr.filter(Age.gt(Age(30))).update_with(
        lambda emp: setattr(emp, "age", Age(emp.age.value + 1))
    )
    print(f"   Updated: {len(updated)} employee(s)")
    print()

    # Show updated ages
    all_employees = employee_mgr.all()
    print("Updated ages:")
    for emp in sorted(all_employees, key=lambda e: e.age.value):
        print(f"  - {emp.name.value}: {emp.age.value} years old")
    print()


def demonstrate_update_with_function(db: Database):
    """Demonstrate update_with using named functions."""
    print("=" * 80)
    print("UPDATE WITH NAMED FUNCTIONS")
    print("=" * 80)
    print()

    employee_mgr = Employee.manager(db)

    # Define promotion function
    def promote_to_senior(employee):
        """Promote employee to senior status with 10% raise."""
        employee.status = Status("senior")
        employee.salary = Salary(int(employee.salary.value * 1.1))

    # Show current status and salaries
    print("Current status and salaries:")
    for emp in employee_mgr.all():
        print(f"  - {emp.name.value}: {emp.status.value}, ${emp.salary.value:,}")
    print()

    # Promote all regular employees to senior
    print("Promoting all 'regular' employees to 'senior' with 10% raise...")
    updated = employee_mgr.filter(Status.eq(Status("regular"))).update_with(promote_to_senior)
    print(f"   Updated: {len(updated)} employee(s)")
    print()

    # Show updated status and salaries
    print("Updated status and salaries:")
    for emp in employee_mgr.all():
        print(f"  - {emp.name.value}: {emp.status.value}, ${emp.salary.value:,}")
    print()


def demonstrate_complex_update(db: Database):
    """Demonstrate complex multi-attribute updates."""
    print("=" * 80)
    print("COMPLEX MULTI-ATTRIBUTE UPDATES")
    print("=" * 80)
    print()

    employee_mgr = Employee.manager(db)

    # Define complex update function
    def year_end_review(employee):
        """Perform year-end review: status and salary adjustments."""
        # Junior -> Regular after 2 years
        if employee.status.value == "junior" and employee.age.value >= 25:
            employee.status = Status("regular")
            employee.salary = Salary(int(employee.salary.value * 1.15))  # 15% raise

        # Regular -> Senior for experienced employees
        elif employee.status.value == "regular" and employee.age.value >= 35:
            employee.status = Status("senior")
            employee.salary = Salary(int(employee.salary.value * 1.20))  # 20% raise

    # Show before
    print("Before year-end review:")
    for emp in sorted(employee_mgr.all(), key=lambda e: e.age.value):
        print(f"  - {emp.name.value} ({emp.age.value}y): {emp.status.value}, ${emp.salary.value:,}")
    print()

    # Perform year-end review for all employees
    print("Performing year-end review for all employees...")
    updated = employee_mgr.filter(Age.gt(Age(0))).update_with(year_end_review)
    print(f"   Reviewed: {len(updated)} employee(s)")
    print()

    # Show after
    print("After year-end review:")
    for emp in sorted(employee_mgr.all(), key=lambda e: e.age.value):
        print(f"  - {emp.name.value} ({emp.age.value}y): {emp.status.value}, ${emp.salary.value:,}")
    print()


def demonstrate_atomic_transactions(db: Database):
    """Demonstrate atomic transaction behavior."""
    print("=" * 80)
    print("ATOMIC TRANSACTION BEHAVIOR")
    print("=" * 80)
    print()

    employee_mgr = Employee.manager(db)

    # Show current salaries
    print("Current salaries:")
    for emp in employee_mgr.all():
        print(f"  - {emp.name.value}: ${emp.salary.value:,}")
    print()

    # Define function that will fail
    counter = [0]

    def failing_update(employee):
        """Update function that fails on second employee."""
        counter[0] += 1
        if counter[0] == 2:
            raise ValueError("Intentional failure to demonstrate rollback")
        employee.salary = Salary(int(employee.salary.value * 1.5))

    # Try to update (will fail and rollback)
    print("Attempting update that will fail on second employee...")
    try:
        employee_mgr.filter(Age.gt(Age(0))).update_with(failing_update)
    except ValueError as e:
        print(f"   ❌ Error: {e}")
    print()

    # Show salaries unchanged (atomic rollback)
    print("Salaries after failed update (should be unchanged):")
    for emp in employee_mgr.all():
        print(f"  - {emp.name.value}: ${emp.salary.value:,}")
    print()
    print("✓ All updates rolled back - transaction is atomic!")
    print()


def main():
    """Run chainable operations examples."""
    print()
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 15 + "Chainable Delete and Update Operations" + " " * 24 + "║")
    print("╚" + "═" * 78 + "╝")
    print()

    # Setup database
    db = Database(address="localhost:1729", database="chainable_ops_demo")
    db.connect()

    if db.database_exists():
        db.delete_database()
    db.create_database()

    # Define schema
    schema_manager = SchemaManager(db)
    schema_manager.register(Employee)
    schema_manager.sync_schema(force=True)

    # Insert sample data
    print("Inserting sample employees...")
    employee_mgr = Employee.manager(db)
    employees = [
        Employee(
            name=Name("Alice"),
            email=Email("alice@company.com"),
            age=Age(28),
            salary=Salary(60000),
            status=Status("junior"),
            department=Department("Engineering"),
        ),
        Employee(
            name=Name("Bob"),
            email=Email("bob@company.com"),
            age=Age(35),
            salary=Salary(80000),
            status=Status("regular"),
            department=Department("Engineering"),
        ),
        Employee(
            name=Name("Charlie"),
            email=Email("charlie@company.com"),
            age=Age(42),
            salary=Salary(100000),
            status=Status("senior"),
            department=Department("Management"),
        ),
        Employee(
            name=Name("Diana"),
            email=Email("diana@company.com"),
            age=Age(65),
            salary=Salary(120000),
            status=Status("senior"),
            department=Department("Executive"),
        ),
        Employee(
            name=Name("Eve"),
            email=Email("eve@company.com"),
            age=Age(23),
            salary=Salary(50000),
            status=Status("inactive"),
            department=Department("HR"),
        ),
    ]
    employee_mgr.insert_many(employees)
    print(f"✓ Inserted {len(employees)} employees")
    print()

    # Run demonstrations
    demonstrate_chainable_delete(db)
    input("Press Enter to continue to update_with examples...")
    print()

    # Re-insert data for update examples
    employee_mgr.insert_many(
        [
            Employee(
                name=Name("Frank"),
                email=Email("frank@company.com"),
                age=Age(32),
                salary=Salary(70000),
                status=Status("regular"),
                department=Department("Engineering"),
            ),
            Employee(
                name=Name("Grace"),
                email=Email("grace@company.com"),
                age=Age(28),
                salary=Salary(65000),
                status=Status("junior"),
                department=Department("Sales"),
            ),
            Employee(
                name=Name("Henry"),
                email=Email("henry@company.com"),
                age=Age(38),
                salary=Salary(85000),
                status=Status("regular"),
                department=Department("Engineering"),
            ),
        ]
    )

    demonstrate_update_with_lambda(db)
    input("Press Enter to continue...")
    print()

    demonstrate_update_with_function(db)
    input("Press Enter to continue...")
    print()

    demonstrate_complex_update(db)
    input("Press Enter to continue...")
    print()

    demonstrate_atomic_transactions(db)

    # Cleanup
    db.delete_database()
    db.close()

    print("=" * 80)
    print("✓ Chainable operations examples complete!")
    print("=" * 80)
    print()
    print("Key takeaways:")
    print("  ✓ filter().delete() - Delete with complex expression filters")
    print("  ✓ filter().update_with(lambda) - Bulk update with lambda functions")
    print("  ✓ filter().update_with(func) - Bulk update with named functions")
    print("  ✓ All operations use atomic transactions")
    print("  ✓ Returns count (delete) or list of entities (update_with)")
    print("=" * 80)


if __name__ == "__main__":
    main()

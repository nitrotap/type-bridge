"""Pattern Example: Abstract Types and Inheritance.

This example demonstrates:
- Defining abstract entity types
- Creating concrete subtypes with inheritance
- Polymorphic queries (querying abstract types)
- Shared attribute ownership via inheritance
- get_all_attributes() vs get_owned_attributes()
- Using abstract types in relation roles

Pattern: Abstract types allow you to define common attributes once and
share them across multiple concrete subtypes, enabling polymorphic queries.
"""

from type_bridge import (
    Database,
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


# Define shared attribute types
class Name(String):
    pass


class Email(String):
    pass


class Phone(String):
    pass


class Address(String):
    pass


class Salary(Integer):
    pass


class StudentId(String):
    pass


class EmployeeId(String):
    pass


class GPA(String):
    pass


# Abstract base entity with common attributes
class Person(Entity):
    """Abstract person type with common attributes."""

    flags: TypeFlags = TypeFlags(name="person", abstract=True)

    name: Name = Flag(Key)
    email: Email
    phone: Phone | None = None


# Concrete subtype: Student
class Student(Person):
    """Concrete student type inheriting from Person."""

    flags: TypeFlags = TypeFlags(name="student")

    student_id: StudentId = Flag(Key)
    gpa: GPA


# Concrete subtype: Employee
class Employee(Person):
    """Concrete employee type inheriting from Person."""

    flags: TypeFlags = TypeFlags(name="employee")

    employee_id: EmployeeId = Flag(Key)
    salary: Salary


# Another abstract type: Organization
class Organization(Entity):
    """Abstract organization type."""

    flags: TypeFlags = TypeFlags(name="organization", abstract=True)

    name: Name = Flag(Key)
    address: Address


# Concrete organization types
class University(Organization):
    """Concrete university type."""

    flags: TypeFlags = TypeFlags(name="university")


class Company(Organization):
    """Concrete company type."""

    flags: TypeFlags = TypeFlags(name="company")


# Relations using abstract types
class Membership(Relation):
    """Abstract membership relation."""

    flags: TypeFlags = TypeFlags(name="membership", abstract=True)

    member: Role[Person] = Role("member", Person)  # Abstract role type!
    organization: Role[Organization] = Role("organization", Organization)


class Enrollment(Membership):
    """Concrete enrollment (student at university)."""

    flags: TypeFlags = TypeFlags(name="enrollment")


class Employment(Membership):
    """Concrete employment (employee at company)."""

    flags: TypeFlags = TypeFlags(name="employment")


def demonstrate_abstract_definition(db: Database):
    """Step 1: Demonstrate abstract type definition."""
    print("=" * 80)
    print("STEP 1: Abstract Type Definition")
    print("=" * 80)
    print()
    print("Abstract types define common structure without being instantiable.")
    print()

    print("Python Code:")
    print("-" * 80)
    print("""
# Abstract base entity
class Person(Entity):
    flags: TypeFlags = TypeFlags(name="person", abstract=True)
    name: Name = Flag(Key)
    email: Email
    phone: Phone | None

# Concrete subtypes
class Student(Person):
    flags: TypeFlags = TypeFlags(name="student")
    student_id: StudentId = Flag(Key)
    gpa: GPA

class Employee(Person):
    flags: TypeFlags = TypeFlags(name="employee")
    employee_id: EmployeeId = Flag(Key)
    salary: Salary
""")
    print("-" * 80)
    print()

    print("Key points:")
    print("  • abstract=True prevents direct instantiation of Person")
    print("  • Student and Employee inherit name, email, phone from Person")
    print("  • Each subtype adds its own specific attributes")
    print("  • In TypeDB schema: student sub person, employee sub person")
    print()
    input("Press Enter to continue...")
    print()


def demonstrate_concrete_instances(db: Database):
    """Step 2: Demonstrate creating instances of concrete types."""
    print("=" * 80)
    print("STEP 2: Creating Concrete Instances")
    print("=" * 80)
    print()
    print("You can only create instances of concrete (non-abstract) types.")
    print()

    # Create students
    print("Creating students...")
    alice = Student(
        name=Name("Alice Johnson"),
        email=Email("alice@university.edu"),
        phone=Phone("555-0101"),
        student_id=StudentId("S001"),
        gpa=GPA("3.8"),
    )

    bob = Student(
        name=Name("Bob Smith"),
        email=Email("bob@university.edu"),
        student_id=StudentId("S002"),
        gpa=GPA("3.5"),
    )

    # Create employees
    print("Creating employees...")
    charlie = Employee(
        name=Name("Charlie Davis"),
        email=Email("charlie@company.com"),
        phone=Phone("555-0102"),
        employee_id=EmployeeId("E001"),
        salary=Salary(75000),
    )

    diana = Employee(
        name=Name("Diana Evans"),
        email=Email("diana@company.com"),
        employee_id=EmployeeId("E002"),
        salary=Salary(85000),
    )

    # Insert into database
    student_mgr = Student.manager(db)
    employee_mgr = Employee.manager(db)

    student_mgr.insert_many([alice, bob])
    employee_mgr.insert_many([charlie, diana])

    print("✓ Created 2 students and 2 employees")
    print()

    # Show what was created
    print("Students:")
    for student in student_mgr.all():
        phone_val = student.phone.value if student.phone else "N/A"
        print(f"  • {student.name.value} ({student.student_id.value})")
        print(f"    Email: {student.email.value}, Phone: {phone_val}")
        print(f"    GPA: {student.gpa.value}")
    print()

    print("Employees:")
    for employee in employee_mgr.all():
        phone_val = employee.phone.value if employee.phone else "N/A"
        print(f"  • {employee.name.value} ({employee.employee_id.value})")
        print(f"    Email: {employee.email.value}, Phone: {phone_val}")
        print(f"    Salary: ${employee.salary.value:,}")
    print()
    input("Press Enter to continue...")
    print()


def demonstrate_polymorphic_queries(db: Database):
    """Step 3: Demonstrate polymorphic queries."""
    print("=" * 80)
    print("STEP 3: Polymorphic Queries")
    print("=" * 80)
    print()
    print("Query abstract types to retrieve all instances of subtypes.")
    print()

    print("Python Code:")
    print("-" * 80)
    print("""
# Query the abstract Person type
person_mgr = Person.manager(db)
all_persons = person_mgr.all()

# This returns BOTH students and employees!
""")
    print("-" * 80)
    print()

    print("Executing...")
    person_mgr = Person.manager(db)
    all_persons = person_mgr.all()

    print(f"\n✓ Found {len(all_persons)} persons (students + employees)")
    print()
    print("All persons:")
    for person in sorted(all_persons, key=lambda p: p.name.value):
        # Type information
        type_name = person.__class__.__name__
        print(f"  • {person.name.value} ({type_name})")
        print(f"    Email: {person.email.value}")

    print()
    print("Note: Polymorphic queries return instances of concrete subtypes,")
    print("not instances of the abstract type itself.")
    print()
    input("Press Enter to continue...")
    print()


def demonstrate_attribute_ownership(db: Database):
    """Step 4: Demonstrate attribute ownership with inheritance."""
    print("=" * 80)
    print("STEP 4: Attribute Ownership")
    print("=" * 80)
    print()
    print("Subtypes inherit attributes from their parent types.")
    print()

    print("Python Code:")
    print("-" * 80)
    print("""
# Get owned vs all attributes
owned = Student.get_owned_attributes()
all_attrs = Student.get_all_attributes()

print(f"Owned by Student: {list(owned.keys())}")
print(f"All (including inherited): {list(all_attrs.keys())}")
""")
    print("-" * 80)
    print()

    owned = Student.get_owned_attributes()
    all_attrs = Student.get_all_attributes()

    print(f"Owned by Student directly: {list(owned.keys())}")
    print(f"All attributes (including inherited): {list(all_attrs.keys())}")
    print()

    print("Inherited attributes:")
    inherited = set(all_attrs.keys()) - set(owned.keys())
    for attr_name in sorted(inherited):
        print(f"  • {attr_name} (from Person)")
    print()

    print("Note: In TypeDB schema, inherited attributes are owned by the parent type.")
    print("Subtypes have access to them but don't own them in the schema.")
    print()
    input("Press Enter to continue...")
    print()


def demonstrate_abstract_roles(db: Database):
    """Step 5: Demonstrate abstract types in relation roles."""
    print("=" * 80)
    print("STEP 5: Abstract Types in Relation Roles")
    print("=" * 80)
    print()
    print("Relations can use abstract types for role players, allowing")
    print("different concrete subtypes to play the same role.")
    print()

    # Create organizations
    mit = University(name=Name("MIT"), address=Address("77 Massachusetts Ave, Cambridge, MA"))

    tech_corp = Company(
        name=Name("TechCorp"), address=Address("123 Tech Street, San Francisco, CA")
    )

    university_mgr = University.manager(db)
    company_mgr = Company.manager(db)

    university_mgr.insert(mit)
    company_mgr.insert(tech_corp)

    # Get persons
    student_mgr = Student.manager(db)
    employee_mgr = Employee.manager(db)

    alice = student_mgr.get(student_id="S001")[0]
    charlie = employee_mgr.get(employee_id="E001")[0]

    # Create memberships
    enrollment_mgr = Enrollment.manager(db)
    employment_mgr = Employment.manager(db)

    # Student enrolled at university
    alice_enrollment = Enrollment(member=alice, organization=mit)
    enrollment_mgr.insert(alice_enrollment)

    # Employee employed at company
    charlie_employment = Employment(member=charlie, organization=tech_corp)
    employment_mgr.insert(charlie_employment)

    print("✓ Created memberships:")
    print(f"  • {alice.name.value} (Student) enrolled at {mit.name.value}")
    print(f"  • {charlie.name.value} (Employee) employed at {tech_corp.name.value}")
    print()

    # Query all memberships polymorphically
    print("Querying abstract Membership relation:")
    membership_mgr = Membership.manager(db)
    all_memberships = membership_mgr.all()

    print(f"\n✓ Found {len(all_memberships)} memberships:")
    for membership in all_memberships:
        member_name = membership.member.name.value
        org_name = membership.organization.name.value
        membership_type = membership.__class__.__name__
        print(f"  • {member_name} - {org_name} ({membership_type})")

    print()
    print("Note: Both Student and Employee can play the 'member' role")
    print("because they are subtypes of the abstract Person type.")
    print()
    input("Press Enter to continue...")
    print()


def demonstrate_filtering_subtypes(db: Database):
    """Step 6: Demonstrate filtering by subtype."""
    print("=" * 80)
    print("STEP 6: Filtering by Concrete Subtypes")
    print("=" * 80)
    print()
    print("You can filter polymorphic queries by specific attributes")
    print("to target concrete subtypes.")
    print()

    # Query only students (by student-specific attribute)
    print("Query students using student-specific filter:")
    print("-" * 80)
    student_mgr = Student.manager(db)
    high_gpa_students = student_mgr.filter(GPA.like(GPA("^3\\.[8-9].*"))).execute()

    print(f"✓ Students with GPA >= 3.8: {len(high_gpa_students)}")
    for student in high_gpa_students:
        print(f"  • {student.name.value}: GPA {student.gpa.value}")
    print()

    # Query only employees (by employee-specific attribute)
    print("Query employees using employee-specific filter:")
    print("-" * 80)
    employee_mgr = Employee.manager(db)
    high_earners = employee_mgr.filter(Salary.gte(Salary(80000))).execute()

    print(f"✓ Employees with salary >= $80,000: {len(high_earners)}")
    for employee in high_earners:
        print(f"  • {employee.name.value}: ${employee.salary.value:,}")
    print()

    # Filter on shared attributes
    print("Filter on shared (inherited) attributes:")
    print("-" * 80)
    person_mgr = Person.manager(db)
    persons_with_phone = person_mgr.filter(Phone.like(Phone(".*"))).execute()

    print(f"✓ Persons with phone numbers: {len(persons_with_phone)}")
    for person in persons_with_phone:
        phone_val = person.phone.value if person.phone else "N/A"
        print(f"  • {person.name.value}: {phone_val} ({person.__class__.__name__})")
    print()
    input("Press Enter to continue...")
    print()


def show_inheritance_summary():
    """Show summary of inheritance patterns."""
    print("=" * 80)
    print("Inheritance and Abstract Types Summary")
    print("=" * 80)
    print()

    print("Key Concepts:")
    print("  1. Abstract Types (abstract=True):")
    print("     • Cannot be instantiated directly")
    print("     • Define common attributes for subtypes")
    print("     • Enable polymorphic queries")
    print()

    print("  2. Concrete Subtypes:")
    print("     • Inherit attributes from parent types")
    print("     • Add their own specific attributes")
    print("     • Can be instantiated and queried")
    print()

    print("  3. Polymorphic Queries:")
    print("     • Query abstract type → returns all subtype instances")
    print("     • Query concrete type → returns only that type")
    print("     • Use type-specific filters to target subtypes")
    print()

    print("  4. Abstract Types in Relations:")
    print("     • Role players can be abstract types")
    print("     • Any concrete subtype can play the role")
    print("     • Enables flexible relationship modeling")
    print()

    print("Best Practices:")
    print("  ✓ Use abstract types for common attributes (Person, Organization)")
    print("  ✓ Create concrete types for instantiable entities (Student, Employee)")
    print("  ✓ Use get_all_attributes() to see inherited attributes")
    print("  ✓ Use polymorphic queries when you need all subtypes")
    print("  ✓ Use concrete managers when you need specific subtypes")
    print()


def main():
    """Run inheritance and abstract types demonstration."""
    print()
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 15 + "Pattern: Abstract Types and Inheritance" + " " * 23 + "║")
    print("╚" + "═" * 78 + "╝")
    print()

    # Create fresh database
    db = Database(address="localhost:1729", database="pattern_inheritance")
    db.connect()

    if db.database_exists():
        print("Deleting existing database...")
        db.delete_database()

    db.create_database()
    print("✓ Created database 'pattern_inheritance'")
    print()

    # Set up schema
    schema_mgr = SchemaManager(db)
    schema_mgr.register(
        Person,
        Student,
        Employee,
        Organization,
        University,
        Company,
        Membership,
        Enrollment,
        Employment,
    )
    schema_mgr.sync_schema()
    print("✓ Schema synchronized")
    print()

    # Run demonstrations
    demonstrate_abstract_definition(db)
    demonstrate_concrete_instances(db)
    demonstrate_polymorphic_queries(db)
    demonstrate_attribute_ownership(db)
    demonstrate_abstract_roles(db)
    demonstrate_filtering_subtypes(db)
    show_inheritance_summary()

    # Clean up
    print("=" * 80)
    print("Demonstration complete!")
    print("=" * 80)
    print()

    delete_db = input("Delete 'pattern_inheritance' database? [y/N]: ").strip().lower()
    if delete_db in ("y", "yes"):
        db.delete_database()
        print("✓ Database deleted")
    else:
        print("Database 'pattern_inheritance' preserved for exploration")

    db.close()


if __name__ == "__main__":
    main()

"""Tests for CRUD operations (EntityManager and RelationManager)."""

from typing import ClassVar

import pytest

from type_bridge import (
    Boolean,
    Card,
    Double,
    Entity,
    EntityFlags,
    Flag,
    Integer,
    Key,
    Relation,
    RelationFlags,
    Role,
    String,
    Unique,
)
from type_bridge.session import Database


# Test Attribute Types
class Name(String):
    """Name attribute."""
    pass


class Email(String):
    """Email attribute."""
    pass


class Age(Integer):
    """Age attribute."""
    pass


class Score(Double):
    """Score attribute."""
    pass


class Active(Boolean):
    """Active status attribute."""
    pass


class Tag(String):
    """Tag attribute."""
    pass


class Industry(String):
    """Industry attribute."""
    pass


class Position(String):
    """Position attribute."""
    pass


class Salary(Integer):
    """Salary attribute."""
    pass


# Test Entity Types
class Person(Entity):
    """Person entity for testing."""
    flags = EntityFlags(type_name="person")

    name: Name = Flag(Key)
    email: Email = Flag(Unique)
    age: Age | None
    score: Score


class Company(Entity):
    """Company entity with multi-value attributes."""
    flags = EntityFlags(type_name="company")

    name: Name = Flag(Key)
    industry: list[Industry] = Flag(Card(1, 5))


class User(Entity):
    """User entity with various cardinality options."""
    flags = EntityFlags(type_name="user")

    name: Name = Flag(Key)
    tags: list[Tag] = Flag(Card(min=2))  # At least 2 tags
    active: Active


# Test Relation Types
class Employment(Relation):
    """Employment relation for testing."""
    flags = RelationFlags(type_name="employment")

    employee: ClassVar[Role] = Role("employee", Person)
    employer: ClassVar[Role] = Role("employer", Company)

    position: Position
    salary: Salary | None = None


# Fixtures
@pytest.fixture(scope="function")
def db():
    """Create a test database connection with cleanup."""
    database = Database(address="localhost:1729", database="test_crud")
    database.connect()

    # Delete database if it exists (cleanup from previous runs)
    if database.database_exists():
        database.delete_database()

    # Create fresh database
    database.create_database()

    yield database

    # Cleanup after test
    try:
        database.delete_database()
    except Exception:
        pass  # Ignore cleanup errors
    finally:
        database.close()


@pytest.fixture(scope="function")
def db_with_schema(db):
    """Database with schema defined and cleanup between tests."""
    # Define schema
    schema_query = """
    define

    # Attributes
    attribute name, value string;
    attribute email, value string;
    attribute age, value integer;
    attribute score, value double;
    attribute active, value boolean;
    attribute tag, value string;
    attribute industry, value string;
    attribute position, value string;
    attribute salary, value integer;

    # Entities
    entity person,
        owns name @key,
        owns email @unique,
        owns age @card(0..1),
        owns score;

    entity company,
        owns name @key,
        owns industry @card(1..5);

    entity user,
        owns name @key,
        owns tag @card(2..),
        owns active;

    # Relations
    relation employment,
        relates employee,
        relates employer,
        owns position,
        owns salary @card(0..1);

    # Role players
    person plays employment:employee;
    company plays employment:employer;
    """

    db.execute_query(schema_query, "schema")

    yield db

    # Note: Database cleanup is handled by the db fixture


class TestEntityManagerCreate:
    """Tests for EntityManager.insert() method."""

    def test_create_basic_entity(self, db_with_schema):
        """Test creating entity with basic attributes."""
        # Create a person using the new manager() class method
        person = Person.manager(db_with_schema).insert(
            name="Alice Johnson",
            email="alice@example.com",
            age=30,
            score=95.5
        )

        # Verify instance was created correctly
        assert person.name.value == "Alice Johnson" if hasattr(person.name, 'value') else person.name == "Alice Johnson"
        assert person.email.value == "alice@example.com" if hasattr(person.email, 'value') else person.email == "alice@example.com"
        assert person.age.value == 30 if hasattr(person.age, 'value') else person.age == 30
        assert person.score.value == 95.5 if hasattr(person.score, 'value') else person.score == 95.5

    def test_create_with_optional_none(self, db_with_schema):
        """Test creating entity with optional field as None."""
        # Create person without age
        person = Person.manager(db_with_schema).insert(
            name="Bob Smith",
            email="bob@example.com",
            age=None,
            score=87.3
        )

        assert person.age is None

    def test_create_with_key_attribute(self, db_with_schema):
        """Test creating entity with @key attribute."""
        person = Person.manager(db_with_schema).insert(
            name="Charlie Brown",
            email="charlie@example.com",
            age=25,
            score=90.0
        )

        # Key attribute should be set
        assert person.name.value == "Charlie Brown" if hasattr(person.name, 'value') else person.name == "Charlie Brown"

    def test_create_with_unique_attribute(self, db_with_schema):
        """Test creating entity with @unique attribute."""
        person = Person.manager(db_with_schema).insert(
            name="Diana Prince",
            email="diana@example.com",
            age=28,
            score=98.5
        )

        # Unique attribute should be set
        assert person.email.value == "diana@example.com" if hasattr(person.email, 'value') else person.email == "diana@example.com"


class TestEntityManagerCreateWithCardinality:
    """Tests for EntityManager.insert() with various cardinality constraints."""

    def test_create_with_multi_value_range(self, db_with_schema):
        """Test creating entity with @card(1..5) constraint."""
        company = Company.manager(db_with_schema).insert(
            name="TechCorp",
            industry=["Technology", "Software", "AI"]
        )

        assert len(company.industry) == 3

    def test_create_with_min_cardinality(self, db_with_schema):
        """Test creating entity with @card(2..) constraint."""
        user = User.manager(db_with_schema).insert(
            name="user1",
            tags=["python", "rust", "typescript"],
            active=True
        )

        assert len(user.tags) >= 2


class TestRelationManagerCreate:
    """Tests for RelationManager.insert() method."""

    def test_create_relation_basic(self, db_with_schema):
        """Test creating a basic relation with role players."""
        # First create entities using the new manager syntax
        person = Person.manager(db_with_schema).insert(
            name="Alice Johnson",
            email="alice@example.com",
            age=30,
            score=95.5
        )

        company = Company.manager(db_with_schema).insert(
            name="TechCorp",
            industry=["Technology"]
        )

        # Create employment relation using the new manager syntax
        employment = Employment.manager(db_with_schema).insert(
            role_players={
                "employee": person,
                "employer": company
            },
            attributes={
                "position": "Software Engineer",
                "salary": 100000
            }
        )

        # Verify relation was created with correct attributes
        assert employment.position.value == "Software Engineer" if hasattr(employment.position, 'value') else employment.position == "Software Engineer"
        assert employment.salary.value == 100000 if hasattr(employment.salary, 'value') else employment.salary == 100000

    def test_create_relation_without_optional_attributes(self, db_with_schema):
        """Test creating relation without optional attributes."""
        # Create entities first using the new manager syntax
        person = Person.manager(db_with_schema).insert(
            name="Bob Smith",
            email="bob@example.com",
            age=28,
            score=87.3
        )

        company = Company.manager(db_with_schema).insert(
            name="StartupCo",
            industry=["Startup", "Technology"]
        )

        # Create employment without salary using the new manager syntax
        employment = Employment.manager(db_with_schema).insert(
            role_players={
                "employee": person,
                "employer": company
            },
            attributes={
                "position": "Junior Developer"
            }
        )

        # Verify relation was created with only position
        assert employment.position.value == "Junior Developer" if hasattr(employment.position, 'value') else employment.position == "Junior Developer"
        assert employment.salary is None


class TestPydanticValidation:
    """Tests for Pydantic validation in create operations."""

    def test_create_with_type_coercion(self, db_with_schema):
        """Test that Pydantic coerces types correctly."""
        # Pass string age (should be coerced to int)
        person = Person.manager(db_with_schema).insert(
            name="Test User",
            email="test@example.com",
            age="35",  # String instead of int
            score=90.0
        )

        # Age should be coerced to int
        age_value = person.age.value if hasattr(person.age, 'value') else person.age
        assert isinstance(age_value, int)
        assert age_value == 35

    def test_create_with_attribute_instances(self, db_with_schema):
        """Test creating with Attribute instances (fully type-safe)."""
        # Pass Attribute instances
        person = Person.manager(db_with_schema).insert(
            name=Name("Alice"),
            email=Email("alice@test.com"),
            age=Age(30),
            score=Score(95.5)
        )

        assert person.name.value == "Alice" if hasattr(person.name, 'value') else person.name == "Alice"


class TestQueryGeneration:
    """Tests to verify correct TypeQL query generation."""

    def test_entity_insert_query_generation(self):
        """Test that Entity generates correct insert query."""
        person = Person(
            name=Name("Alice"),
            email=Email("alice@example.com"),
            age=Age(30),
            score=Score(95.5)
        )

        query = person.to_insert_query()

        # Verify query structure
        assert "$e isa person" in query
        assert 'has name "Alice"' in query
        assert 'has email "alice@example.com"' in query
        assert 'has age 30' in query
        assert 'has score 95.5' in query

    def test_entity_with_list_insert_query(self):
        """Test insert query generation for multi-value attributes."""
        company = Company(
            name=Name("TechCorp"),
            industry=[Industry("Technology"), Industry("Software")]
        )

        query = company.to_insert_query()

        assert "$e isa company" in query
        assert 'has name "TechCorp"' in query
        assert 'has industry "Technology"' in query
        assert 'has industry "Software"' in query


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

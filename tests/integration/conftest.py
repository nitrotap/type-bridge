"""Pytest fixtures for integration tests."""

import pytest

from type_bridge import Credentials, Database, TypeDB

# Test database configuration
TEST_DB_NAME = "type_bridge_test"
TEST_DB_ADDRESS = "localhost:1729"


@pytest.fixture(scope="session")
def typedb_driver():
    """Create a TypeDB driver connection for the test session.

    Yields:
        TypeDB driver instance

    Raises:
        ConnectionError: If TypeDB server is not running
    """
    try:
        driver = TypeDB.core_driver(
            address=TEST_DB_ADDRESS,
            credentials=Credentials(username="admin", password="password", tls_enabled=False),
        )
        yield driver
        driver.close()
    except Exception as e:
        pytest.skip(f"TypeDB server not available at {TEST_DB_ADDRESS}: {e}")


@pytest.fixture(scope="session")
def test_database(typedb_driver):
    """Create a test database for the session and clean it up after.

    Args:
        typedb_driver: TypeDB driver fixture

    Yields:
        Database name (str)
    """
    # Create database if it doesn't exist
    if typedb_driver.databases.contains(TEST_DB_NAME):
        typedb_driver.databases.get(TEST_DB_NAME).delete()

    typedb_driver.databases.create(TEST_DB_NAME)

    yield TEST_DB_NAME

    # Cleanup: Delete test database after all tests
    if typedb_driver.databases.contains(TEST_DB_NAME):
        typedb_driver.databases.get(TEST_DB_NAME).delete()


@pytest.fixture(scope="function")
def db(test_database):
    """Create a Database instance for each test function.

    Args:
        test_database: Test database name fixture

    Yields:
        Database instance
    """
    database = Database(address=TEST_DB_ADDRESS, database=test_database)
    database.connect()
    yield database
    database.close()


@pytest.fixture(scope="function")
def clean_db(typedb_driver, test_database):
    """Provide a clean database for each test by wiping all data.

    This fixture ensures each test starts with an empty database by:
    1. Deleting the existing test database
    2. Recreating it fresh

    Args:
        typedb_driver: TypeDB driver fixture
        test_database: Test database name

    Yields:
        Database instance with clean state
    """
    # Delete and recreate database for clean state
    if typedb_driver.databases.contains(test_database):
        typedb_driver.databases.get(test_database).delete()
    typedb_driver.databases.create(test_database)

    database = Database(address=TEST_DB_ADDRESS, database=test_database)
    database.connect()
    yield database
    database.close()


@pytest.fixture(scope="function")
def db_with_schema(clean_db):
    """Provide a database with a basic schema already defined.

    This fixture is useful for tests that need a schema but don't test schema creation.

    Args:
        clean_db: Clean database fixture

    Yields:
        Database instance with basic schema
    """
    from type_bridge import (
        Entity,
        EntityFlags,
        Flag,
        Integer,
        Key,
        Relation,
        RelationFlags,
        Role,
        SchemaManager,
        String,
    )

    # Define basic test schema
    class Name(String):
        pass

    class Age(Integer):
        pass

    class Person(Entity):
        flags = EntityFlags(type_name="person")
        name: Name = Flag(Key)
        age: Age | None

    class Company(Entity):
        flags = EntityFlags(type_name="company")
        name: Name = Flag(Key)

    class Position(String):
        pass

    class Employment(Relation):
        flags = RelationFlags(type_name="employment")
        employee: Role[Person] = Role("employee", Person)
        employer: Role[Company] = Role("employer", Company)
        position: Position

    # Create schema
    schema_manager = SchemaManager(clean_db)
    schema_manager.register(Person, Company, Employment)
    schema_manager.sync_schema(force=True)

    yield clean_db

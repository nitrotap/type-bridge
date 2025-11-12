"""Test insert query generation for all attribute types.

This test module provides comprehensive coverage of insert query generation
for all attribute types (String, Integer, Double, Boolean, DateTime) in
various configurations.
"""

from datetime import UTC, datetime

from type_bridge import (
    Boolean,
    Card,
    DateTime,
    Double,
    Entity,
    EntityFlags,
    Flag,
    Integer,
    Key,
    String,
)


def test_boolean_insert_query():
    """Test insert query generation with Boolean attributes."""

    class IsActive(Boolean):
        pass

    class User(Entity):
        flags = EntityFlags(type_name="user")
        is_active: IsActive

    # Test with True value
    user_active = User(is_active=IsActive(True))
    query_true = user_active.to_insert_query()

    assert "$e isa user" in query_true
    assert "has IsActive true" in query_true
    assert "has IsActive false" not in query_true

    # Test with False value
    user_inactive = User(is_active=IsActive(False))
    query_false = user_inactive.to_insert_query()

    assert "$e isa user" in query_false
    assert "has IsActive false" in query_false
    assert "has IsActive true" not in query_false


def test_double_insert_query():
    """Test insert query generation with Double attributes."""

    class Score(Double):
        pass

    class TestResult(Entity):
        flags = EntityFlags(type_name="test-result")
        score: Score

    # Test with float value
    result = TestResult(score=Score(95.5))
    query = result.to_insert_query()

    assert "$e isa test-result" in query
    assert "has Score 95.5" in query


def test_datetime_insert_query():
    """Test insert query generation with DateTime attributes."""

    class CreatedAt(DateTime):
        pass

    class Event(Entity):
        flags = EntityFlags(type_name="event")
        created_at: CreatedAt

    # Test with naive datetime
    dt_naive = datetime(2024, 1, 15, 10, 30, 45, 123456)
    event_naive = Event(created_at=CreatedAt(dt_naive))
    query_naive = event_naive.to_insert_query()

    assert "$e isa event" in query_naive
    assert "has CreatedAt 2024-01-15T10:30:45.123456" in query_naive
    # Ensure datetime is NOT quoted (should be datetime literal, not string)
    assert '"2024-01-15T10:30:45.123456"' not in query_naive

    # Test with timezone-aware datetime
    dt_aware = datetime(2024, 1, 15, 10, 30, 45, 123456, tzinfo=UTC)
    event_aware = Event(created_at=CreatedAt(dt_aware))
    query_aware = event_aware.to_insert_query()

    assert "$e isa event" in query_aware
    assert "has CreatedAt 2024-01-15T10:30:45.123456+00:00" in query_aware
    # Ensure datetime is NOT quoted
    assert '"2024-01-15T10:30:45.123456+00:00"' not in query_aware


def test_all_attribute_types_insert_query():
    """Test insert query generation with all attribute types in one entity."""

    class Name(String):
        pass

    class Age(Integer):
        pass

    class Salary(Double):
        pass

    class IsActive(Boolean):
        pass

    class HireDate(DateTime):
        pass

    class Employee(Entity):
        flags = EntityFlags(type_name="employee")
        name: Name = Flag(Key)
        age: Age
        salary: Salary
        is_active: IsActive
        hire_date: HireDate

    # Create entity with all attribute types
    hire_dt = datetime(2024, 1, 15, 9, 0, 0)
    employee = Employee(
        name=Name("Alice Smith"),
        age=Age(30),
        salary=Salary(75000.50),
        is_active=IsActive(True),
        hire_date=HireDate(hire_dt),
    )

    query = employee.to_insert_query()

    # Validate entity type
    assert "$e isa employee" in query

    # Validate String attribute (quoted)
    assert 'has Name "Alice Smith"' in query

    # Validate Integer attribute (unquoted number)
    assert "has Age 30" in query

    # Validate Double attribute (unquoted float)
    assert "has Salary 75000.5" in query

    # Validate Boolean attribute (unquoted lowercase)
    assert "has IsActive true" in query

    # Validate DateTime attribute (unquoted ISO 8601)
    assert "has HireDate 2024-01-15T09:00:00" in query


def test_optional_attribute_insert_query():
    """Test that optional attributes with None values are excluded from insert query."""

    class Name(String):
        pass

    class Email(String):
        pass

    class Person(Entity):
        flags = EntityFlags(type_name="person")
        name: Name = Flag(Key)
        email: Email | None

    # Create entity with None optional attribute
    person = Person(name=Name("Bob"), email=None)
    query = person.to_insert_query()

    assert "$e isa person" in query
    assert 'has Name "Bob"' in query
    # Email should NOT appear in query when None
    assert "has Email" not in query


def test_multi_value_double_insert_query():
    """Test insert query generation with multi-value Double attributes."""

    class Score(Double):
        pass

    class Student(Entity):
        flags = EntityFlags(type_name="student")
        scores: list[Score] = Flag(Card(min=1))

    # Create entity with multiple scores
    student = Student(scores=[Score(95.5), Score(87.3), Score(92.0)])
    query = student.to_insert_query()

    assert "$e isa student" in query
    assert "has Score 95.5" in query
    assert "has Score 87.3" in query
    assert "has Score 92.0" in query


def test_multi_value_boolean_insert_query():
    """Test insert query generation with multi-value Boolean attributes."""

    class FeatureFlag(Boolean):
        pass

    class Config(Entity):
        flags = EntityFlags(type_name="config")
        feature_flags: list[FeatureFlag] = Flag(Card(min=1))

    # Create entity with multiple boolean values
    config = Config(feature_flags=[FeatureFlag(True), FeatureFlag(False), FeatureFlag(True)])
    query = config.to_insert_query()

    assert "$e isa config" in query
    # Should have multiple boolean values
    assert query.count("has FeatureFlag true") == 2
    assert query.count("has FeatureFlag false") == 1


def test_multi_value_datetime_insert_query():
    """Test insert query generation with multi-value DateTime attributes."""

    class EventDate(DateTime):
        pass

    class Schedule(Entity):
        flags = EntityFlags(type_name="schedule")
        event_dates: list[EventDate] = Flag(Card(min=1))

    # Create entity with multiple datetime values
    dates = [
        EventDate(datetime(2024, 1, 15, 9, 0, 0)),
        EventDate(datetime(2024, 2, 20, 14, 30, 0)),
        EventDate(datetime(2024, 3, 10, 18, 0, 0)),
    ]
    schedule = Schedule(event_dates=dates)
    query = schedule.to_insert_query()

    assert "$e isa schedule" in query
    assert "has EventDate 2024-01-15T09:00:00" in query
    assert "has EventDate 2024-02-20T14:30:00" in query
    assert "has EventDate 2024-03-10T18:00:00" in query


def test_mixed_optional_and_required_attributes():
    """Test insert query with mix of required and optional attributes."""

    class Name(String):
        pass

    class Age(Integer):
        pass

    class Email(String):
        pass

    class Phone(String):
        pass

    class Person(Entity):
        flags = EntityFlags(type_name="person")
        name: Name = Flag(Key)
        age: Age
        email: Email | None
        phone: Phone | None

    # Create entity with some optional attributes set, some None
    person = Person(name=Name("Charlie"), age=Age(25), email=Email("charlie@example.com"), phone=None)
    query = person.to_insert_query()

    assert "$e isa person" in query
    assert 'has Name "Charlie"' in query
    assert "has Age 25" in query
    assert 'has Email "charlie@example.com"' in query
    # Phone should NOT appear when None
    assert "has Phone" not in query


def test_integer_edge_cases():
    """Test insert query generation with Integer edge cases."""

    class Count(Integer):
        pass

    class Counter(Entity):
        flags = EntityFlags(type_name="counter")
        count: Count

    # Test with zero
    counter_zero = Counter(count=Count(0))
    query_zero = counter_zero.to_insert_query()
    assert "has Count 0" in query_zero

    # Test with negative number
    counter_negative = Counter(count=Count(-42))
    query_negative = counter_negative.to_insert_query()
    assert "has Count -42" in query_negative

    # Test with large number
    counter_large = Counter(count=Count(999999999))
    query_large = counter_large.to_insert_query()
    assert "has Count 999999999" in query_large


def test_double_edge_cases():
    """Test insert query generation with Double edge cases."""

    class Value(Double):
        pass

    class Measurement(Entity):
        flags = EntityFlags(type_name="measurement")
        value: Value

    # Test with zero
    measurement_zero = Measurement(value=Value(0.0))
    query_zero = measurement_zero.to_insert_query()
    assert "has Value 0.0" in query_zero

    # Test with negative float
    measurement_negative = Measurement(value=Value(-3.14))
    query_negative = measurement_negative.to_insert_query()
    assert "has Value -3.14" in query_negative

    # Test with scientific notation value
    measurement_small = Measurement(value=Value(0.000001))
    query_small = measurement_small.to_insert_query()
    # Python will format this in scientific notation or decimal
    assert "has Value" in query_small


def test_string_with_special_characters():
    """Test insert query generation with String containing special characters."""

    class Description(String):
        pass

    class Item(Entity):
        flags = EntityFlags(type_name="item")
        description: Description

    # Test with quotes in string
    item = Item(description=Description('A "quoted" string'))
    query = item.to_insert_query()

    assert "$e isa item" in query
    # String should be properly quoted
    assert "has Description" in query
    assert '"' in query


def test_empty_string_insert_query():
    """Test insert query generation with empty string."""

    class Name(String):
        pass

    class Tag(Entity):
        flags = EntityFlags(type_name="tag")
        name: Name

    # Test with empty string
    tag = Tag(name=Name(""))
    query = tag.to_insert_query()

    assert "$e isa tag" in query
    assert 'has Name ""' in query

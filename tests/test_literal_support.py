"""Tests for Literal type support with type checkers."""

from typing import Literal

from type_bridge import Entity, EntityFlags, Integer, String


def test_literal_type_annotation_for_type_safety():
    """Test that Literal types work with type checkers for static type safety."""

    class Status(String):
        pass

    # This syntax provides type-checker safety:
    # The type checker will warn if you try to pass an invalid literal value
    class Task(Entity):
        flags = EntityFlags(type_name="task")
        status: Literal["pending", "active", "completed"] | Status

    # At runtime, these all work (Pydantic sees Status which accepts any string)
    task1 = Task(status="pending")
    assert task1.status == "pending"

    task2 = Task(status="active")
    assert task2.status == "active"

    task3 = Task(status="completed")
    assert task3.status == "completed"

    # Runtime accepts any string (type checker would flag this as error)
    task4 = Task(status="invalid")
    assert task4.status == "invalid"


def test_long_literal_for_type_safety():
    """Test Integer attribute with Literal types for type-checker safety."""

    class Priority(Integer):
        pass

    class Task(Entity):
        flags = EntityFlags(type_name="task")
        priority: Literal[1, 2, 3] | Priority

    # Valid literal values work
    task1 = Task(priority=1)
    assert task1.priority == 1

    task2 = Task(priority=2)
    assert task2.priority == 2

    task3 = Task(priority=3)
    assert task3.priority == 3

    # Runtime accepts any int (type checker would flag this)
    task4 = Task(priority=999)
    assert task4.priority == 999


def test_literal_with_multiple_attributes():
    """Test entity with multiple Literal attributes for type safety."""

    class Status(String):
        pass

    class Priority(Integer):
        pass

    class Task(Entity):
        flags = EntityFlags(type_name="task")
        status: Literal["todo", "in_progress", "done"] | Status
        priority: Literal[1, 2, 3, 4, 5] | Priority

    # Valid instance
    task = Task(status="in_progress", priority=3)
    assert task.status == "in_progress"
    assert task.priority == 3

    # Runtime accepts values outside Literal (type checker would flag)
    task2 = Task(status="custom_status", priority=100)
    assert task2.status == "custom_status"
    assert task2.priority == 100


def test_literal_schema_generation():
    """Test that Literal attributes generate correct schema."""

    class Status(String):
        pass

    class Task(Entity):
        flags = EntityFlags(type_name="task")
        status: Literal["pending", "active"] | Status

    # Schema generation should still work
    schema = Task.to_schema_definition()
    assert "entity task" in schema
    assert "owns status" in schema


def test_literal_insert_query():
    """Test that Literal attributes work in insert queries."""

    class Status(String):
        pass

    class Task(Entity):
        flags = EntityFlags(type_name="task")
        status: Literal["pending", "active", "completed"] | Status

    task = Task(status="active")
    query = task.to_insert_query()

    assert "$e isa task" in query
    assert 'has status "active"' in query


def test_literal_json_serialization():
    """Test JSON serialization with Literal types."""

    class Status(String):
        pass

    class Task(Entity):
        flags = EntityFlags(type_name="task")
        status: Literal["pending", "active"] | Status

    task = Task(status="pending")

    # Serialize to dict
    task_dict = task.model_dump()
    assert task_dict == {"status": "pending"}

    # Serialize to JSON
    task_json = task.model_dump_json()
    assert '"status":"pending"' in task_json


def test_literal_json_deserialization():
    """Test JSON deserialization with Literal types."""

    class Status(String):
        pass

    class Task(Entity):
        flags = EntityFlags(type_name="task")
        status: Literal["pending", "active"] | Status

    # Deserialize from JSON with valid value
    json_data = '{"status": "active"}'
    task = Task.model_validate_json(json_data)
    assert task.status == "active"

    # Also works with values outside Literal at runtime
    other_json = '{"status": "custom"}'
    task2 = Task.model_validate_json(other_json)
    assert task2.status == "custom"


def test_literal_provides_type_checker_hints():
    """Test that Literal types provide hints to type checkers."""

    class Role(String):
        pass

    class User(Entity):
        flags = EntityFlags(type_name="user")
        # Type checkers will see this and provide autocomplete/warnings
        role: Literal["admin", "user", "guest"] | Role

    # Runtime accepts all these
    admin = User(role="admin")
    assert admin.role == "admin"

    # Type checker would flag "superadmin" as invalid, but runtime accepts it
    superadmin = User(role="superadmin")
    assert superadmin.role == "superadmin"

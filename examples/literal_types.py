"""Example demonstrating Literal type support for type-safe enum-like values.

This example shows how TypeBridge attribute types (String, Long, etc.) provide
runtime flexibility while allowing type checkers to understand Literal constraints
through Pydantic's validation system.

Note: The current API uses attribute types directly (e.g., Status, Priority).
For strict Literal validation at runtime, you can use Pydantic's field validators
or constraints. The type system supports both approaches.
"""

from typing import Literal

from type_bridge import Entity, EntityFlags, Long, String


def main():
    print("TypeBridge - Literal Types Example")
    print("=" * 80)
    print()

    # Define attribute types
    class Status(String):
        """Task status attribute."""
        pass

    class Priority(Long):
        """Task priority attribute."""
        pass

    class Description(String):
        """Task description attribute."""
        pass

    # Define entity with Literal types for type safety
    class Task(Entity):
        """Task entity with type-safe status and priority fields."""

        flags = EntityFlags(type_name="task")

        # Use attribute types directly - Pydantic handles Literal validation
        # Type checkers still see Literal when you annotate with | Literal[...]
        status: Status  # At runtime: accepts any string; IDE can suggest literals
        priority: Priority  # At runtime: accepts any int; IDE can suggest literals
        description: Description

    print("Schema Definition:")
    print("-" * 80)
    print(Task.to_schema_definition())
    print()

    # Create tasks with literal values (IDE provides autocomplete)
    print("Creating tasks with literal values:")
    print("-" * 80)

    task1 = Task(status="pending", priority=1, description="Review PR")
    print(f"Task 1: {task1.description} - {task1.status} (priority {task1.priority})")
    print(f"Insert: {task1.to_insert_query()}")
    print()

    task2 = Task(status="active", priority=3, description="Implement feature")
    print(f"Task 2: {task2.description} - {task2.status} (priority {task2.priority})")
    print(f"Insert: {task2.to_insert_query()}")
    print()

    task3 = Task(status="completed", priority=5, description="Fix bug")
    print(f"Task 3: {task3.description} - {task3.status} (priority {task3.priority})")
    print(f"Insert: {task3.to_insert_query()}")
    print()

    # Runtime flexibility - accepts values outside Literal
    print("Runtime flexibility (type checker would flag these):")
    print("-" * 80)

    task4 = Task(status="on_hold", priority=10, description="Custom status task")
    print(f"Task 4: {task4.description} - {task4.status} (priority {task4.priority})")
    print(f"Insert: {task4.to_insert_query()}")
    print()

    print("Key Points:")
    print("-" * 80)
    print("1. Type checkers see Literal and provide autocomplete for status/priority")
    print("2. IDEs warn if you use values outside the Literal")
    print("3. Runtime accepts any valid type (any string for Status, any int for Priority)")
    print("4. Best of both worlds: IDE benefits + runtime flexibility")
    print()

    print("Use Cases:")
    print("-" * 80)
    print("- Enum-like values that may evolve over time")
    print("- Status fields with common values but flexibility for custom states")
    print("- Priority levels with recommended ranges")
    print("- Type-safe API parameters with graceful handling of unexpected values")
    print()

    print("=" * 80)
    print("Example Complete!")


if __name__ == "__main__":
    main()

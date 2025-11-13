"""Role descriptor for TypeDB relation role players."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema

from type_bridge.validation import ReservedWordError, validate_type_name as validate_reserved_word

if TYPE_CHECKING:
    from type_bridge.models.entity import Entity


class Role[T: "Entity"]:
    """Descriptor for relation role players with type safety.

    Generic type T represents the entity type that can play this role.

    Example:
        class Employment(Relation):
            employee: Role[Person] = Role("employee", Person)
            employer: Role[Company] = Role("employer", Company)
    """

    def __init__(self, role_name: str, player_type: type[T]):
        """Initialize a role.

        Args:
            role_name: The name of the role in TypeDB
            player_type: The entity type that can play this role

        Raises:
            ReservedWordError: If role_name is a TypeQL reserved word
        """
        # Validate role name doesn't conflict with TypeQL reserved words
        validate_reserved_word(role_name, "role")

        self.role_name = role_name
        self.player_entity_type = player_type
        # Get type name from the entity class
        self.player_type = player_type.get_type_name()
        self.attr_name: str | None = None

    def __set_name__(self, owner: type, name: str) -> None:
        """Called when role is assigned to a class."""
        self.attr_name = name

    def __get__(self, obj: Any, objtype: type | None = None) -> T | Role[T]:
        """Get role player from instance."""
        if obj is None:
            return self
        return obj.__dict__.get(self.attr_name)

    def __set__(self, obj: Any, value: T) -> None:
        """Set role player on instance."""
        obj.__dict__[self.attr_name] = value

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        """Define how Pydantic should validate Role fields.

        Accepts either a Role instance or the entity type T.
        """
        from pydantic_core import core_schema

        # Extract the entity type from Role[T]
        entity_type = Any
        if hasattr(source_type, "__args__") and source_type.__args__:
            entity_type = source_type.__args__[0]

        # Create a schema that accepts the entity type
        python_schema = core_schema.is_instance_schema(entity_type)

        return core_schema.no_info_after_validator_function(
            lambda x: x,  # Just pass through the entity instance
            python_schema,
        )

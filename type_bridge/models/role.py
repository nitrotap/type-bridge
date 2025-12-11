"""Role descriptor for TypeDB relation role players."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, overload

from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema

from type_bridge.validation import validate_type_name as validate_reserved_word

if TYPE_CHECKING:
    from type_bridge.fields.role import RoleRef
    from type_bridge.models.entity import Entity


class Role[T: "Entity"]:
    """Descriptor for relation role players with type safety.

    Generic type T represents the entity type that can play this role.

    Example:
        class Employment(Relation):
            employee: Role[Person] = Role("employee", Person)
            employer: Role[Company] = Role("employer", Company)
    """

    def __init__(self, role_name: str, player_type: type[T], *additional_player_types: type[T]):
        """Initialize a role.

        Args:
            role_name: The name of the role in TypeDB
            player_type: The entity type that can play this role
            additional_player_types: Optional additional entity types allowed to play this role

        Raises:
            ReservedWordError: If role_name is a TypeQL reserved word
        """
        # Validate role name doesn't conflict with TypeQL reserved words
        validate_reserved_word(role_name, "role")

        self.role_name = role_name
        unique_types: list[type[T]] = []
        for typ in (player_type, *additional_player_types):
            if typ not in unique_types:
                unique_types.append(typ)

        if not unique_types:
            # Should be impossible because player_type is required, but keeps type checkers happy
            raise ValueError("Role requires at least one player type")

        self.player_entity_types: tuple[type[T], ...] = tuple(unique_types)
        first_entity_type = unique_types[0]
        self.player_entity_type = first_entity_type
        # Get type name from the entity class(es)
        self.player_types = tuple(pt.get_type_name() for pt in self.player_entity_types)
        self.player_type = first_entity_type.get_type_name()
        self.attr_name: str | None = None

    def __set_name__(self, owner: type, name: str) -> None:
        """Called when role is assigned to a class."""
        self.attr_name = name

    @overload
    def __get__(self, obj: None, objtype: type) -> RoleRef[T]:
        """Get RoleRef when accessed from class (for query building)."""
        ...

    @overload
    def __get__(self, obj: Any, objtype: type) -> T:
        """Get role player entity when accessed from instance."""
        ...

    def __get__(self, obj: Any, objtype: type) -> T | RoleRef[T]:
        """Get role player from instance or RoleRef from class.

        When accessed from the class (obj is None), returns RoleRef for
        type-safe query building (e.g., Employment.employee.age.gt(Age(30))).
        When accessed from an instance, returns the entity playing the role.
        """
        if obj is None:
            from type_bridge.fields.role import RoleRef

            return RoleRef(
                role_name=self.role_name,
                player_types=self.player_entity_types,
            )
        return obj.__dict__.get(self.attr_name)

    def __set__(self, obj: Any, value: T) -> None:
        """Set role player on instance."""
        if not isinstance(value, self.player_entity_types):
            allowed = ", ".join(pt.__name__ for pt in self.player_entity_types)
            raise TypeError(
                f"Role '{self.role_name}' expects types ({allowed}), got {type(value).__name__}"
            )
        obj.__dict__[self.attr_name] = value

    @classmethod
    def multi(
        cls, role_name: str, player_type: type[T], *additional_player_types: type[T]
    ) -> Role[T]:
        """Define a role playable by multiple entity types."""
        if len((player_type, *additional_player_types)) < 2:
            raise ValueError("Role.multi requires at least two player types")
        return cls(role_name, player_type, *additional_player_types)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        """Define how Pydantic should validate Role fields.

        Accepts either a Role instance or the entity type T.
        """
        from pydantic_core import core_schema

        # Extract the entity type(s) from Role[T]
        entity_types: tuple[type[Any], ...] | tuple[Any, ...]
        if hasattr(source_type, "__args__") and source_type.__args__:
            # Role[Document | Email] -> args = (Document, Email)
            entity_types = tuple(source_type.__args__)
        else:
            entity_types = (Any,)

        # Create a schema that accepts any of the entity types
        if len(entity_types) == 1:
            python_schema = core_schema.is_instance_schema(entity_types[0])
        else:
            python_schema = core_schema.is_instance_schema(entity_types)

        return core_schema.no_info_after_validator_function(
            lambda x: x,  # Just pass through the entity instance
            python_schema,
        )

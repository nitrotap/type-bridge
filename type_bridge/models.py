"""Simplified model classes for TypeDB entities using Attribute ownership model."""

from typing import Any, ClassVar, get_type_hints

from type_bridge.attribute import Attribute


class Entity:
    """Base class for TypeDB entities.

    Entities own attributes defined as Attribute subclasses.

    Example:
        class Name(String):
            pass

        class Age(Long):
            pass

        class Person(Entity):
            __type_name__ = "person"

            name: Name  # Type annotation declares ownership
            age: Age
    """

    # TypeDB metadata (class-level)
    __type_name__: ClassVar[str | None] = None
    __abstract__: ClassVar[bool] = False
    __supertype__: ClassVar[str | None] = None
    __owned_attrs__: ClassVar[dict[str, type[Attribute]]] = {}

    def __init_subclass__(cls) -> None:
        """Called when Entity subclass is created."""
        super().__init_subclass__()

        # Extract owned attributes from type hints
        owned_attrs = {}
        try:
            hints = get_type_hints(cls)
        except Exception:
            hints = getattr(cls, '__annotations__', {})

        for field_name, field_type in hints.items():
            if field_name.startswith('_') or field_name.startswith('__'):
                continue

            # Check if it's an Attribute subclass
            try:
                if isinstance(field_type, type) and issubclass(field_type, Attribute):
                    owned_attrs[field_name] = field_type
            except TypeError:
                continue

        cls.__owned_attrs__ = owned_attrs

    def __init__(self, **values: Any):
        """Initialize entity with attribute values.

        Args:
            **values: Attribute values as keyword arguments
        """
        self._iid: str | None = None
        self._values: dict[str, Any] = {}

        # Set attribute values
        for key, value in values.items():
            if key in self.__owned_attrs__:
                self._values[key] = value
            else:
                # Allow setting other attributes too (for flexibility)
                self._values[key] = value

    def __getattr__(self, name: str) -> Any:
        """Get attribute value."""
        if name.startswith('_'):
            return object.__getattribute__(self, name)
        if name in self._values:
            return self._values[name]
        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        """Set attribute value."""
        if name.startswith('_'):
            object.__setattr__(self, name, value)
        else:
            if not hasattr(self, '_values'):
                object.__setattr__(self, '_values', {})
            self._values[name] = value

    @classmethod
    def get_type_name(cls) -> str:
        """Get the TypeDB type name for this entity."""
        return cls.__type_name__ or cls.__name__.lower()

    @classmethod
    def get_owned_attributes(cls) -> dict[str, type[Attribute]]:
        """Get attributes owned by this entity.

        Returns:
            Dictionary mapping field names to Attribute classes
        """
        return cls.__owned_attrs__.copy()

    @classmethod
    def to_schema_definition(cls) -> str:
        """Generate TypeQL schema definition for this entity.

        Returns:
            TypeQL schema definition string
        """
        type_name = cls.get_type_name()
        lines = []

        # Define entity type
        if cls.__supertype__:
            entity_def = f"{type_name} sub {cls.__supertype__}"
        else:
            entity_def = f"{type_name} sub entity"

        if cls.__abstract__:
            entity_def += ", abstract"

        lines.append(entity_def)

        # Add attribute ownerships
        for field_name, attr_class in cls.__owned_attrs__.items():
            attr_name = attr_class.get_attribute_name()
            ownership = f"    owns {attr_name}"
            if attr_class.is_key():
                ownership += " @key"
            lines.append(ownership)

        lines.append(";")
        return ",\n".join(lines)

    def to_insert_query(self, var: str = "$e") -> str:
        """Generate TypeQL insert query for this instance.

        Args:
            var: Variable name to use

        Returns:
            TypeQL insert pattern
        """
        type_name = self.get_type_name()
        parts = [f"{var} isa {type_name}"]

        for field_name, attr_class in self.__owned_attrs__.items():
            value = self._values.get(field_name)
            if value is not None:
                attr_name = attr_class.get_attribute_name()
                parts.append(f"has {attr_name} {self._format_value(value)}")

        return ", ".join(parts)

    @staticmethod
    def _format_value(value: Any) -> str:
        """Format a Python value for TypeQL."""
        if isinstance(value, str):
            return f'"{value}"'
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, (int, float)):
            return str(value)
        else:
            return f'"{str(value)}"'

    def __repr__(self) -> str:
        """String representation of entity."""
        field_strs = []
        for field_name in self.__owned_attrs__:
            value = self._values.get(field_name)
            if value is not None:
                field_strs.append(f"{field_name}={value!r}")
        return f"{self.__class__.__name__}({', '.join(field_strs)})"


class Role:
    """Descriptor for relation role players."""

    def __init__(self, role_name: str, player_type: str | type):
        """Initialize a role.

        Args:
            role_name: The name of the role in TypeDB
            player_type: The type of entity that can play this role
        """
        self.role_name = role_name
        if isinstance(player_type, str):
            self.player_type = player_type
        else:
            # Get type name from the entity class
            self.player_type = player_type.get_type_name()
        self.attr_name: str | None = None

    def __set_name__(self, owner: type, name: str) -> None:
        """Called when role is assigned to a class."""
        self.attr_name = name

    def __get__(self, obj: Any, objtype: type | None = None) -> Any:
        """Get role player from instance."""
        if obj is None:
            return self
        return obj.__dict__.get(self.attr_name)

    def __set__(self, obj: Any, value: Any) -> None:
        """Set role player on instance."""
        obj.__dict__[self.attr_name] = value


class Relation:
    """Base class for TypeDB relations.

    Relations can own attributes and have role players.

    Example:
        class Position(String):
            pass

        class Salary(Long):
            pass

        class Employment(Relation):
            __type_name__ = "employment"

            employee: ClassVar[Role] = Role("employee", Person)
            employer: ClassVar[Role] = Role("employer", Company)

            position: Position  # Type annotation declares ownership
            salary: Salary
    """

    # TypeDB metadata
    __type_name__: ClassVar[str | None] = None
    __abstract__: ClassVar[bool] = False
    __supertype__: ClassVar[str | None] = None
    __owned_attrs__: ClassVar[dict[str, type[Attribute]]] = {}
    _roles: ClassVar[dict[str, Role]] = {}

    def __init_subclass__(cls) -> None:
        """Initialize relation subclass."""
        super().__init_subclass__()

        # Collect roles
        roles = {}
        for key in dir(cls):
            if not key.startswith("_"):
                value = getattr(cls, key, None)
                if isinstance(value, Role):
                    roles[key] = value
        cls._roles = roles

        # Extract owned attributes from type hints
        owned_attrs = {}
        try:
            hints = get_type_hints(cls)
        except Exception:
            hints = getattr(cls, '__annotations__', {})

        for field_name, field_type in hints.items():
            if field_name.startswith('_') or field_name.startswith('__'):
                continue
            if field_name in roles:  # Skip role fields
                continue

            # Check if it's an Attribute subclass
            try:
                if isinstance(field_type, type) and issubclass(field_type, Attribute):
                    owned_attrs[field_name] = field_type
            except TypeError:
                continue

        cls.__owned_attrs__ = owned_attrs

    def __init__(self, **values: Any):
        """Initialize relation with values.

        Args:
            **values: Role players and attribute values
        """
        self._iid: str | None = None
        self._values: dict[str, Any] = {}

        # Set values
        for key, value in values.items():
            if key in self._roles:
                # This is a role player
                setattr(self, key, value)
            else:
                # This is an attribute value
                self._values[key] = value

    def __getattr__(self, name: str) -> Any:
        """Get attribute value."""
        if name.startswith('_'):
            return object.__getattribute__(self, name)
        if name in self._values:
            return self._values[name]
        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        """Set attribute value."""
        if name.startswith('_'):
            object.__setattr__(self, name, value)
        else:
            if not hasattr(self, '_values'):
                object.__setattr__(self, '_values', {})
            self._values[name] = value

    @classmethod
    def get_type_name(cls) -> str:
        """Get the TypeDB type name for this relation."""
        return cls.__type_name__ or cls.__name__.lower()

    @classmethod
    def get_owned_attributes(cls) -> dict[str, type[Attribute]]:
        """Get attributes owned by this relation.

        Returns:
            Dictionary mapping field names to Attribute classes
        """
        return cls.__owned_attrs__.copy()

    @classmethod
    def to_schema_definition(cls) -> str:
        """Generate TypeQL schema definition for this relation.

        Returns:
            TypeQL schema definition string
        """
        type_name = cls.get_type_name()
        lines = []

        # Define relation type
        if cls.__supertype__:
            relation_def = f"{type_name} sub {cls.__supertype__}"
        else:
            relation_def = f"{type_name} sub relation"

        if cls.__abstract__:
            relation_def += ", abstract"

        lines.append(relation_def)

        # Add roles
        for role_name, role in cls._roles.items():
            lines.append(f"    relates {role.role_name}")

        # Add attribute ownerships
        for field_name, attr_class in cls.__owned_attrs__.items():
            attr_name = attr_class.get_attribute_name()
            lines.append(f"    owns {attr_name}")

        lines.append(";")
        return ",\n".join(lines)

    def __repr__(self) -> str:
        """String representation of relation."""
        parts = []
        # Show role players
        for role_name in self._roles:
            player = getattr(self, role_name, None)
            if player is not None:
                parts.append(f"{role_name}={player!r}")
        # Show attributes
        for field_name in self.__owned_attrs__:
            value = self._values.get(field_name)
            if value is not None:
                parts.append(f"{field_name}={value!r}")
        return f"{self.__class__.__name__}({', '.join(parts)})"

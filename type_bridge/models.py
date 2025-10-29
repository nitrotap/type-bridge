"""Simplified model classes for TypeDB entities using Attribute ownership model."""

from typing import Any, ClassVar, get_args, get_origin, get_type_hints

from type_bridge.attribute import Attribute, AttributeFlags, EntityFlags, RelationFlags


class Entity:
    """Base class for TypeDB entities.

    Entities own attributes defined as Attribute subclasses.
    Use EntityFlags to configure type name and abstract status.
    Supertype is determined automatically from Python inheritance.

    Example:
        class Name(String):
            pass

        class Age(Long):
            pass

        class Person(Entity):
            flags = EntityFlags(type_name="person")
            name: Name = Flag(Key, Card(1))
            age: Age

        # Abstract entity
        class AbstractPerson(Entity):
            flags = EntityFlags(abstract=True)
            name: Name

        # Inheritance (Person sub abstract-person)
        class ConcretePerson(AbstractPerson):
            age: Age
    """

    # Internal metadata (class-level)
    _flags: ClassVar[EntityFlags] = EntityFlags()
    _owned_attrs: ClassVar[dict[str, dict[str, Any]]] = {}

    def __init_subclass__(cls) -> None:
        """Called when Entity subclass is created."""
        super().__init_subclass__()

        # Get EntityFlags if defined, otherwise use default
        flags = getattr(cls, 'flags', None)
        if isinstance(flags, EntityFlags):
            cls._flags = flags
        else:
            # Inherit flags from parent if not explicitly set
            for base in cls.__bases__:
                if hasattr(base, '_flags') and base is not Entity:
                    cls._flags = EntityFlags(
                        type_name=None,  # Will default to class name
                        abstract=False
                    )
                    break
            else:
                cls._flags = EntityFlags()

        # Extract owned attributes from type hints
        owned_attrs = {}
        try:
            # Use include_extras=True to preserve Annotated metadata
            hints = get_type_hints(cls, include_extras=True)
        except Exception:
            hints = getattr(cls, '__annotations__', {})

        for field_name, field_type in hints.items():
            if field_name.startswith('_'):
                continue
            if field_name == 'flags':  # Skip the flags field itself
                continue

            # Extract actual type and metadata from Annotated types
            actual_type = field_type
            metadata_flags = None

            # Check if this is an Annotated type
            if get_origin(field_type) is not None:
                # This handles Annotated[Name, AttributeFlags(...)]
                args = get_args(field_type)
                if args:
                    actual_type = args[0]
                    # Look for AttributeFlags in metadata
                    for metadata in args[1:]:
                        if isinstance(metadata, AttributeFlags):
                            metadata_flags = metadata
                            break

            # Get the default value (might be AttributeFlags from Flag())
            default_value = getattr(cls, field_name, None)

            # Check if it's an Attribute subclass
            try:
                if isinstance(actual_type, type) and issubclass(actual_type, Attribute):
                    # Determine flags: prefer Annotated metadata, fallback to default value
                    if metadata_flags is not None:
                        flags = metadata_flags
                    elif isinstance(default_value, AttributeFlags):
                        flags = default_value
                    else:
                        flags = AttributeFlags()

                    owned_attrs[field_name] = {
                        'type': actual_type,
                        'flags': flags
                    }
            except TypeError:
                continue

        cls._owned_attrs = owned_attrs

    def __init__(self, **values: Any):
        """Initialize entity with attribute values.

        Args:
            **values: Attribute values as keyword arguments
        """
        self._iid: str | None = None
        self._values: dict[str, Any] = {}

        # Set attribute values
        for key, value in values.items():
            if key in self._owned_attrs:
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
        return cls._flags.type_name or cls.__name__.lower()

    @classmethod
    def get_supertype(cls) -> str | None:
        """Get the supertype from Python inheritance.

        Returns:
            Type name of the parent Entity class, or None if direct Entity subclass
        """
        for base in cls.__bases__:
            if base is not Entity and issubclass(base, Entity):
                return base.get_type_name()
        return None

    @classmethod
    def is_abstract(cls) -> bool:
        """Check if this is an abstract entity."""
        return cls._flags.abstract

    @classmethod
    def get_owned_attributes(cls) -> dict[str, dict[str, Any]]:
        """Get attributes owned by this entity.

        Returns:
            Dictionary mapping field names to attribute info (type + flags)
        """
        return cls._owned_attrs.copy()

    @classmethod
    def to_schema_definition(cls) -> str:
        """Generate TypeQL schema definition for this entity.

        Returns:
            TypeQL schema definition string
        """
        type_name = cls.get_type_name()
        lines = []

        # Define entity type with supertype from Python inheritance
        supertype = cls.get_supertype()
        if supertype:
            entity_def = f"{type_name} sub {supertype}"
        else:
            entity_def = f"{type_name} sub entity"

        if cls.is_abstract():
            entity_def += ", abstract"

        lines.append(entity_def)

        # Add attribute ownerships
        for field_name, attr_info in cls._owned_attrs.items():
            attr_class = attr_info['type']
            flags = attr_info['flags']
            attr_name = attr_class.get_attribute_name()

            ownership = f"    owns {attr_name}"
            annotations = flags.to_typeql_annotations()
            if annotations:
                ownership += " " + " ".join(annotations)
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

        for field_name, attr_info in self._owned_attrs.items():
            value = self._values.get(field_name)
            if value is not None:
                attr_class = attr_info['type']
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
        for field_name in self._owned_attrs:
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
    Use RelationFlags to configure type name and abstract status.
    Supertype is determined automatically from Python inheritance.

    Example:
        class Position(String):
            pass

        class Salary(Long):
            pass

        class Employment(Relation):
            flags = RelationFlags(type_name="employment")

            employee: ClassVar[Role] = Role("employee", Person)
            employer: ClassVar[Role] = Role("employer", Company)

            position: Position = Flag(Card(1))
            salary: Salary = Flag(Card(0, 1))
    """

    # Internal metadata
    _flags: ClassVar[RelationFlags] = RelationFlags()
    _owned_attrs: ClassVar[dict[str, dict[str, Any]]] = {}
    _roles: ClassVar[dict[str, Role]] = {}

    def __init_subclass__(cls) -> None:
        """Initialize relation subclass."""
        super().__init_subclass__()

        # Get RelationFlags if defined, otherwise use default
        flags = getattr(cls, 'flags', None)
        if isinstance(flags, RelationFlags):
            cls._flags = flags
        else:
            # Inherit flags from parent if not explicitly set
            for base in cls.__bases__:
                if hasattr(base, '_flags') and base is not Relation:
                    cls._flags = RelationFlags(
                        type_name=None,  # Will default to class name
                        abstract=False
                    )
                    break
            else:
                cls._flags = RelationFlags()

        # Collect roles
        roles = {}
        for key in dir(cls):
            if not key.startswith("_") and key != "flags":
                value = getattr(cls, key, None)
                if isinstance(value, Role):
                    roles[key] = value
        cls._roles = roles

        # Extract owned attributes from type hints
        owned_attrs = {}
        try:
            # Use include_extras=True to preserve Annotated metadata
            hints = get_type_hints(cls, include_extras=True)
        except Exception:
            hints = getattr(cls, '__annotations__', {})

        for field_name, field_type in hints.items():
            if field_name.startswith('_'):
                continue
            if field_name == 'flags':  # Skip the flags field itself
                continue
            if field_name in roles:  # Skip role fields
                continue

            # Extract actual type and metadata from Annotated types
            actual_type = field_type
            metadata_flags = None

            # Check if this is an Annotated type
            if get_origin(field_type) is not None:
                # This handles Annotated[Name, AttributeFlags(...)]
                args = get_args(field_type)
                if args:
                    actual_type = args[0]
                    # Look for AttributeFlags in metadata
                    for metadata in args[1:]:
                        if isinstance(metadata, AttributeFlags):
                            metadata_flags = metadata
                            break

            # Get the default value (might be AttributeFlags from Flag())
            default_value = getattr(cls, field_name, None)

            # Check if it's an Attribute subclass
            try:
                if isinstance(actual_type, type) and issubclass(actual_type, Attribute):
                    # Determine flags: prefer Annotated metadata, fallback to default value
                    if metadata_flags is not None:
                        flags = metadata_flags
                    elif isinstance(default_value, AttributeFlags):
                        flags = default_value
                    else:
                        flags = AttributeFlags()

                    owned_attrs[field_name] = {
                        'type': actual_type,
                        'flags': flags
                    }
            except TypeError:
                continue

        cls._owned_attrs = owned_attrs

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
        return cls._flags.type_name or cls.__name__.lower()

    @classmethod
    def get_supertype(cls) -> str | None:
        """Get the supertype from Python inheritance.

        Returns:
            Type name of the parent Relation class, or None if direct Relation subclass
        """
        for base in cls.__bases__:
            if base is not Relation and issubclass(base, Relation):
                return base.get_type_name()
        return None

    @classmethod
    def is_abstract(cls) -> bool:
        """Check if this is an abstract relation."""
        return cls._flags.abstract

    @classmethod
    def get_owned_attributes(cls) -> dict[str, dict[str, Any]]:
        """Get attributes owned by this relation.

        Returns:
            Dictionary mapping field names to attribute info (type + flags)
        """
        return cls._owned_attrs.copy()

    @classmethod
    def to_schema_definition(cls) -> str:
        """Generate TypeQL schema definition for this relation.

        Returns:
            TypeQL schema definition string
        """
        type_name = cls.get_type_name()
        lines = []

        # Define relation type with supertype from Python inheritance
        supertype = cls.get_supertype()
        if supertype:
            relation_def = f"{type_name} sub {supertype}"
        else:
            relation_def = f"{type_name} sub relation"

        if cls.is_abstract():
            relation_def += ", abstract"

        lines.append(relation_def)

        # Add roles
        for role_name, role in cls._roles.items():
            lines.append(f"    relates {role.role_name}")

        # Add attribute ownerships
        for field_name, attr_info in cls._owned_attrs.items():
            attr_class = attr_info['type']
            flags = attr_info['flags']
            attr_name = attr_class.get_attribute_name()

            ownership = f"    owns {attr_name}"
            annotations = flags.to_typeql_annotations()
            if annotations:
                ownership += " " + " ".join(annotations)
            lines.append(ownership)

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
        for field_name in self._owned_attrs:
            value = self._values.get(field_name)
            if value is not None:
                parts.append(f"{field_name}={value!r}")
        return f"{self.__class__.__name__}({', '.join(parts)})"

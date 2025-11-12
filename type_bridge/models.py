"""Simplified model classes for TypeDB entities using Attribute ownership model."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime as datetime_type
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    TypeVar,
    dataclass_transform,
    get_args,
    get_origin,
    get_type_hints,
)

from pydantic import BaseModel, ConfigDict, GetCoreSchemaHandler, model_validator
from pydantic_core import CoreSchema

from type_bridge.attribute import (
    Attribute,
    AttributeFlags,
    Boolean,
    DateTime,
    Double,
    EntityFlags,
    Integer,
    RelationFlags,
    String,
)
from type_bridge.attribute.flags import format_type_name

if TYPE_CHECKING:
    from type_bridge.crud import EntityManager, RelationManager
    from type_bridge.session import Database

# Type variables for self types (use string forward refs to avoid circular import)
E = TypeVar("E", bound="Entity")
R = TypeVar("R", bound="Relation")


@dataclass
class FieldInfo:
    """Information extracted from a field type annotation.

    Attributes:
        attr_type: The Attribute subclass (e.g., Name, Age)
        card_min: Minimum cardinality (None means use default)
        card_max: Maximum cardinality (None means unbounded)
        is_key: Whether this field is marked as @key
        is_unique: Whether this field is marked as @unique
    """

    attr_type: type[Attribute] | None = None
    card_min: int | None = 1
    card_max: int | None = 1
    is_key: bool = False
    is_unique: bool = False


def extract_metadata(field_type: type) -> FieldInfo:
    """Extract attribute type, cardinality, and key/unique metadata from a type annotation.

    Handles:
    - Optional[Name] → FieldInfo(Name, 0, 1, False, False)
    - Key[Name] → FieldInfo(Name, 1, 1, True, False)
    - Unique[Email] → FieldInfo(Email, 1, 1, False, True)
    - Name → FieldInfo(Name, 1, 1, False, False)
    - list[Tag] → FieldInfo(Tag, None, None, False, False) - cardinality set by Flag(Card(...))

    Args:
        field_type: The type annotation from __annotations__

    Returns:
        FieldInfo with extracted metadata
    """
    origin = get_origin(field_type)
    args = get_args(field_type)

    # Default cardinality: exactly one (1,1)
    info = FieldInfo(card_min=1, card_max=1)

    # Handle Union types (Optional[T] or Literal[...] | T)
    from types import UnionType

    if origin is UnionType or str(origin) == "typing.Union":
        # Check if it's Optional (has None in args)
        has_none = type(None) in args or None in args

        if has_none:
            # Optional[T] is Union[T, None]
            for arg in args:
                if arg is not type(None) and arg is not None:
                    # Recursively extract from the non-None type
                    nested_info = extract_metadata(arg)
                    if nested_info.attr_type:
                        # Optional means 0 or 1
                        nested_info.card_min = 0
                        nested_info.card_max = 1
                        return nested_info
        else:
            # Not Optional - might be Literal[...] | AttributeType
            # Look for an Attribute subclass in the union args
            for arg in args:
                try:
                    if isinstance(arg, type) and issubclass(arg, Attribute):
                        # Found the Attribute type - use it
                        info.attr_type = arg
                        info.card_min = 1
                        info.card_max = 1
                        return info
                except TypeError:
                    continue

    # Handle list[Type] annotations
    if origin is list and len(args) >= 1:
        # Extract the attribute type from list[AttributeType]
        list_item_type = args[0]
        try:
            if isinstance(list_item_type, type) and issubclass(list_item_type, Attribute):
                # Found an Attribute type in the list
                info.attr_type = list_item_type
                # Don't set card_min/card_max here - let Flag(Card(...)) handle it
                # or use default multi-value cardinality
                return info
        except TypeError:
            pass

    # Handle Key[T] and Unique[T] type aliases
    elif origin is not None:
        origin_name = str(origin)

        # Check for Key/Unique type aliases
        if "Key" in origin_name and len(args) >= 1:
            info.is_key = True
            info.card_min, info.card_max = 1, 1
            info.attr_type = args[0]
            # Check if attr_type is an Attribute subclass
            try:
                if isinstance(info.attr_type, type) and issubclass(info.attr_type, Attribute):
                    return info
            except TypeError:
                pass
        elif "Unique" in origin_name and len(args) >= 1:
            info.is_unique = True
            info.card_min, info.card_max = 1, 1
            info.attr_type = args[0]
            # Check if attr_type is an Attribute subclass
            try:
                if isinstance(info.attr_type, type) and issubclass(info.attr_type, Attribute):
                    return info
            except TypeError:
                pass

    # Handle plain Attribute types
    else:
        try:
            if isinstance(field_type, type) and issubclass(field_type, Attribute):
                info.attr_type = field_type
                return info
        except TypeError:
            pass

    return info


def _get_base_type_for_attribute(attr_cls: type[Attribute]) -> type | None:
    """Get the base Python type for an Attribute class.

    Args:
        attr_cls: The Attribute subclass (e.g., Name which inherits from String)

    Returns:
        The corresponding base Python type (str, int, float, bool, datetime)
    """
    # Check the MRO (method resolution order) to find the base Attribute type
    for base in attr_cls.__mro__:
        if base is String:
            return str
        elif base is Integer:
            return int
        elif base is Double:
            return float
        elif base is Boolean:
            return bool
        elif base is DateTime:
            return datetime_type
    return None


# TypeDB built-in type names that cannot be used
TYPEDB_BUILTIN_TYPES = {"thing", "entity", "relation", "attribute"}


def _validate_type_name(type_name: str, class_name: str) -> None:
    """Validate that a type name doesn't conflict with TypeDB built-ins.

    Args:
        type_name: The type name to validate
        class_name: The Python class name (for error messages)

    Raises:
        ValueError: If type name conflicts with a TypeDB built-in type
    """
    if type_name.lower() in TYPEDB_BUILTIN_TYPES:
        raise ValueError(
            f"Type name '{type_name}' for class '{class_name}' conflicts with TypeDB built-in type. "
            f"Built-in types are: {', '.join(sorted(TYPEDB_BUILTIN_TYPES))}. "
            f"Please use a different type_name in EntityFlags/RelationFlags or rename your class."
        )


@dataclass
class ModelAttrInfo:
    typ: type[Attribute]
    flags: AttributeFlags


@dataclass_transform(kw_only_default=False, field_specifiers=(AttributeFlags, EntityFlags))
class Entity(BaseModel):
    """Base class for TypeDB entities with Pydantic validation.

    Entities own attributes defined as Attribute subclasses.
    Use EntityFlags to configure type name and abstract status.
    Supertype is determined automatically from Python inheritance.

    This class inherits from Pydantic's BaseModel, providing:
    - Automatic validation of attribute values
    - JSON serialization/deserialization
    - Type checking and coercion
    - Field metadata via Pydantic's Field()

    Example:
        class Name(String):
            pass

        class Age(Integer):
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

    # Pydantic configuration
    model_config = ConfigDict(
        arbitrary_types_allowed=True,  # Allow Attribute subclass types
        validate_assignment=True,  # Validate on attribute assignment
        extra="allow",  # Allow extra fields for flexibility
        ignored_types=(EntityFlags,),  # Ignore EntityFlags type for flags field
        revalidate_instances="always",  # Revalidate on model_copy
    )

    # Internal metadata (class-level)
    _flags: ClassVar[EntityFlags] = EntityFlags()
    _owned_attrs: ClassVar[dict[str, ModelAttrInfo]] = {}
    _iid: str | None = None  # TypeDB internal ID

    def __init_subclass__(cls) -> None:
        """Called when Entity subclass is created."""
        super().__init_subclass__()

        # Get EntityFlags if defined, otherwise create new default flags
        # Check if flags is defined directly on this class (not inherited)
        if "flags" in cls.__dict__ and isinstance(cls.__dict__["flags"], EntityFlags):
            # Explicitly set flags on this class
            cls._flags = cls.__dict__["flags"]
        else:
            # No explicit flags on this class - create new default flags
            # This ensures each subclass gets its own flags instance
            cls._flags = EntityFlags()

        # Validate type name doesn't conflict with TypeDB built-ins
        # (skip validation for base classes that won't appear in schema)
        if not cls._flags.base:
            type_name = cls._flags.name or format_type_name(cls.__name__, cls._flags.case)
            _validate_type_name(type_name, cls.__name__)

        # Extract owned attributes from type hints
        owned_attrs: dict[str, ModelAttrInfo] = {}
        try:
            # Use include_extras=True to preserve Annotated metadata
            hints = get_type_hints(cls, include_extras=True)
        except Exception:
            hints: dict[str, Any] = getattr(cls, "__annotations__", {})

        # Rewrite annotations to add base types for type checker support
        new_annotations = {}

        for field_name, field_type in hints.items():
            if field_name.startswith("_"):
                new_annotations[field_name] = field_type
                continue
            if field_name == "flags":  # Skip the flags field itself
                new_annotations[field_name] = field_type
                continue

            # Get the default value (should be AttributeFlags from Flag())
            default_value = getattr(cls, field_name, None)

            # Extract attribute type and cardinality/key/unique metadata
            field_info = extract_metadata(field_type)

            # Check if field type is a list annotation
            field_origin = get_origin(field_type)
            is_list_type = field_origin is list

            # If we found an Attribute type, add it to owned attributes
            if field_info.attr_type is not None:
                # Validate: list[Type] must have Flag(Card(...))
                if is_list_type and not isinstance(default_value, AttributeFlags):
                    raise TypeError(
                        f"Field '{field_name}' in {cls.__name__}: "
                        f"list[Type] annotations must use Flag(Card(...)) to specify cardinality. "
                        f"Example: {field_name}: list[{field_info.attr_type.__name__}] = Flag(Card(min=1))"
                    )

                # Get flags from default value or create new flags
                if isinstance(default_value, AttributeFlags):
                    flags = default_value

                    # Validate: Flag(Card(...)) should only be used with list[Type]
                    if flags.has_explicit_card and not is_list_type:
                        raise TypeError(
                            f"Field '{field_name}' in {cls.__name__}: "
                            f"Flag(Card(...)) can only be used with list[Type] annotations. "
                            f"For optional single values, use Optional[{field_info.attr_type.__name__}] instead."
                        )

                    # Validate: list[Type] must have Flag(Card(...))
                    if is_list_type and not flags.has_explicit_card:
                        raise TypeError(
                            f"Field '{field_name}' in {cls.__name__}: "
                            f"list[Type] annotations must use Flag(Card(...)) to specify cardinality. "
                            f"Example: {field_name}: list[{field_info.attr_type.__name__}] = Flag(Card(min=1))"
                        )

                    # Merge with cardinality from type annotation if not already set
                    if flags.card_min is None and flags.card_max is None:
                        flags.card_min = field_info.card_min
                        flags.card_max = field_info.card_max
                    # Set is_key and is_unique from type annotation if found
                    if field_info.is_key:
                        flags.is_key = True
                    if field_info.is_unique:
                        flags.is_unique = True
                else:
                    # Create flags from type annotation metadata
                    flags = AttributeFlags(
                        is_key=field_info.is_key,
                        is_unique=field_info.is_unique,
                        card_min=field_info.card_min,
                        card_max=field_info.card_max,
                    )

                owned_attrs[field_name] = ModelAttrInfo(typ=field_info.attr_type, flags=flags)

                # Keep annotation as-is - no need for unions since validators always return Attribute instances
                # - name: Name → stays as Name
                # - age: Age | None → stays as Age | None
                # - tags: list[Tag] → stays as list[Tag]
                new_annotations[field_name] = field_type
            else:
                new_annotations[field_name] = field_type

        # Update class annotations for Pydantic's benefit
        cls.__annotations__ = new_annotations
        cls._owned_attrs = owned_attrs

    @model_validator(mode="wrap")
    @classmethod
    def _wrap_raw_values(cls, values, handler):
        """Ensure all attribute fields are wrapped in Attribute instances.

        This catches edge cases like default values and model_copy that bypass validators.
        Uses 'wrap' mode to intercept all validation paths including model_copy.
        """
        # First, let Pydantic do its validation
        instance = handler(values)

        # Then wrap any raw values
        owned_attrs = cls.get_owned_attributes()
        for field_name, attr_info in owned_attrs.items():
            value = getattr(instance, field_name, None)
            if value is None:
                continue

            attr_class = attr_info.typ

            # Check if it's a list (multi-value attribute)
            if isinstance(value, list):
                wrapped_list = []
                for item in value:
                    if not isinstance(item, attr_class):
                        # Wrap raw value
                        wrapped_list.append(attr_class(item))
                    else:
                        wrapped_list.append(item)
                # Use object.__setattr__ to bypass validate_assignment and avoid recursion
                object.__setattr__(instance, field_name, wrapped_list)
            else:
                # Single value
                if not isinstance(value, attr_class):
                    # Wrap raw value
                    # Use object.__setattr__ to bypass validate_assignment and avoid recursion
                    object.__setattr__(instance, field_name, attr_class(value))

        return instance

    def model_copy(self, *, update: Mapping[str, Any] | None = None, deep: bool = False):
        """Override model_copy to ensure raw values are wrapped in Attribute instances.

        Pydantic's model_copy bypasses validators even with revalidate_instances='always',
        so we override it to force proper validation.
        """
        # Call parent model_copy
        copied = super().model_copy(update=update, deep=deep)

        # Force wrap any raw values in the update dict
        if update:
            owned_attrs = self.__class__.get_owned_attributes()
            for field_name, new_value in update.items():
                if field_name not in owned_attrs:
                    continue

                attr_info = owned_attrs[field_name]
                attr_class = attr_info.typ

                # Check if it's a list (multi-value attribute)
                if isinstance(new_value, list):
                    wrapped_list = []
                    for item in new_value:
                        if not isinstance(item, attr_class):
                            wrapped_list.append(attr_class(item))
                        else:
                            wrapped_list.append(item)
                    object.__setattr__(copied, field_name, wrapped_list)
                else:
                    # Single value
                    if not isinstance(new_value, attr_class):
                        object.__setattr__(copied, field_name, attr_class(new_value))

        return copied

    @classmethod
    def get_type_name(cls) -> str:
        """Get the TypeDB type name for this entity.

        If name is explicitly set in TypeFlags, it is used as-is.
        Otherwise, the class name is formatted according to the case parameter.
        """
        if cls._flags.name:
            return cls._flags.name
        return format_type_name(cls.__name__, cls._flags.case)

    @classmethod
    def get_supertype(cls) -> str | None:
        """Get the supertype from Python inheritance, skipping base classes.

        Base classes (with base=True) are Python-only and don't appear in TypeDB schema.
        This method skips them when determining the TypeDB supertype.

        Returns:
            Type name of the parent Entity class, or None if direct Entity subclass
        """
        for base in cls.__bases__:
            if base is not Entity and issubclass(base, Entity):
                # Skip base classes - they don't appear in TypeDB schema
                if base.is_base():
                    # Recursively find the first non-base parent
                    return base.get_supertype()
                return base.get_type_name()
        return None

    @classmethod
    def is_abstract(cls) -> bool:
        """Check if this is an abstract entity."""
        return cls._flags.abstract

    @classmethod
    def is_base(cls) -> bool:
        """Check if this is a Python base class (not in TypeDB schema)."""
        return cls._flags.base

    @classmethod
    def get_owned_attributes(cls) -> dict[str, ModelAttrInfo]:
        """Get attributes owned by this entity.

        Returns:
            Dictionary mapping field names to ModelAttrInfo (typ + flags)
        """
        return cls._owned_attrs.copy()

    @classmethod
    def manager(cls: type[E], db: Any) -> EntityManager[E]:
        """Create an EntityManager for this entity type.

        Args:
            db: Database connection

        Returns:
            EntityManager instance for this entity type with proper type information

        Example:
            from type_bridge import Database

            db = Database()
            db.connect()

            # Create typed entity instance
            person = Person(name=Name("Alice"), age=Age(30))

            # Insert using manager - with full type safety!
            Person.manager(db).insert(person)
            # person is inferred as Person type by type checkers
        """
        from type_bridge.crud import EntityManager

        return EntityManager(db, cls)

    def insert(self: E, db: Database) -> E:
        """Insert this entity instance into the database.

        Args:
            db: Database connection

        Returns:
            Self for chaining

        Example:
            person = Person(name=Name("Alice"), age=Age(30))
            person.insert(db)
        """
        query = f"insert {self.to_insert_query()};"
        with db.transaction("write") as tx:
            tx.execute(query)
            tx.commit()
        return self

    @classmethod
    def to_schema_definition(cls) -> str | None:
        """Generate TypeQL schema definition for this entity.

        Returns:
            TypeQL schema definition string, or None if this is a base class
        """
        # Base classes don't appear in TypeDB schema
        if cls.is_base():
            return None

        type_name = cls.get_type_name()
        lines = []

        # Define entity type with supertype from Python inheritance
        supertype = cls.get_supertype()
        if supertype:
            entity_def = f"entity {type_name} sub {supertype}"
        else:
            entity_def = f"entity {type_name}"

        if cls.is_abstract():
            entity_def += ", abstract"

        lines.append(entity_def)

        # Add attribute ownerships
        for _field_name, attr_info in cls._owned_attrs.items():
            attr_class = attr_info.typ
            flags = attr_info.flags
            attr_name = attr_class.get_attribute_name()

            ownership = f"    owns {attr_name}"
            annotations = flags.to_typeql_annotations()
            if annotations:
                ownership += " " + " ".join(annotations)
            lines.append(ownership)

        # Join with commas, but end with semicolon (no comma before semicolon)
        return ",\n".join(lines) + ";"

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
            # Use Pydantic's getattr to get field value
            value = getattr(self, field_name, None)
            if value is not None:
                attr_class = attr_info.typ
                attr_name = attr_class.get_attribute_name()

                # Handle lists (multi-value attributes)
                if isinstance(value, list):
                    for item in value:
                        parts.append(f"has {attr_name} {self._format_value(item)}")
                else:
                    parts.append(f"has {attr_name} {self._format_value(value)}")

        return ", ".join(parts)

    @staticmethod
    def _format_value(value: Any) -> str:
        """Format a Python value for TypeQL."""
        # Extract value from Attribute instances
        if isinstance(value, Attribute):
            value = value.value

        if isinstance(value, str):
            return f'"{value}"'
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, (int, float)):
            return str(value)
        else:
            return f'"{str(value)}"'

    def __repr__(self) -> str:
        """Developer-friendly string representation of entity."""
        field_strs = []
        for field_name in self._owned_attrs:
            value = getattr(self, field_name, None)
            if value is not None:
                field_strs.append(f"{field_name}={value!r}")
        return f"{self.__class__.__name__}({', '.join(field_strs)})"

    def __str__(self) -> str:
        """User-friendly string representation of entity."""
        # Extract key attributes first
        key_parts = []
        other_parts = []

        for field_name, attr_info in self._owned_attrs.items():
            value = getattr(self, field_name, None)
            if value is None:
                continue

            # Extract actual value from Attribute instance
            if hasattr(value, "value"):
                display_value = value.value
            else:
                display_value = value

            # Format the field
            field_str = f"{field_name}={display_value}"

            # Separate key attributes
            if attr_info.flags.is_key:
                key_parts.append(field_str)
            else:
                other_parts.append(field_str)

        # Show key attributes first, then others
        all_parts = key_parts + other_parts

        if all_parts:
            return f"{self.get_type_name()}({', '.join(all_parts)})"
        else:
            return f"{self.get_type_name()}()"


class Role[T: Entity]:
    """Descriptor for relation role players with type safety.

    Generic type T represents the entity type that can play this role.
    """

    def __init__(self, role_name: str, player_type: type[T]):
        """Initialize a role.

        Args:
            role_name: The name of the role in TypeDB
            player_type: The entity type that can play this role
        """
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


@dataclass_transform(kw_only_default=False, field_specifiers=(AttributeFlags, RelationFlags))
class Relation(BaseModel):
    """Base class for TypeDB relations with Pydantic validation.

    Relations can own attributes and have role players.
    Use RelationFlags to configure type name and abstract status.
    Supertype is determined automatically from Python inheritance.

    This class inherits from Pydantic's BaseModel, providing:
    - Automatic validation of attribute values
    - JSON serialization/deserialization
    - Type checking and coercion
    - Field metadata via Pydantic's Field()

    Example:
        class Position(String):
            pass

        class Salary(Integer):
            pass

        class Employment(Relation):
            flags = RelationFlags(type_name="employment")

            employee: Role[Person] = Role("employee", Person)
            employer: Role[Company] = Role("employer", Company)

            position: Position
            salary: Salary | None
    """

    # Pydantic configuration
    model_config = ConfigDict(
        arbitrary_types_allowed=True,  # Allow Attribute subclass types and Role
        validate_assignment=True,  # Validate on attribute assignment
        extra="allow",  # Allow extra fields for flexibility
        ignored_types=(RelationFlags, Role),  # Ignore RelationFlags and Role types
        revalidate_instances="always",  # Revalidate on model_copy
    )

    # Internal metadata
    _flags: ClassVar[RelationFlags] = RelationFlags()
    _owned_attrs: ClassVar[dict[str, ModelAttrInfo]] = {}
    _roles: ClassVar[dict[str, Role]] = {}
    _iid: str | None = None  # TypeDB internal ID

    def __init_subclass__(cls) -> None:
        """Initialize relation subclass."""
        super().__init_subclass__()

        # Get RelationFlags if defined, otherwise create new default flags
        # Check if flags is defined directly on this class (not inherited)
        if "flags" in cls.__dict__ and isinstance(cls.__dict__["flags"], RelationFlags):
            # Explicitly set flags on this class
            cls._flags = cls.__dict__["flags"]
        else:
            # No explicit flags on this class - create new default flags
            # This ensures each subclass gets its own flags instance
            cls._flags = RelationFlags()

        # Validate type name doesn't conflict with TypeDB built-ins
        # (skip validation for base classes that won't appear in schema)
        if not cls._flags.base:
            type_name = cls._flags.name or format_type_name(cls.__name__, cls._flags.case)
            _validate_type_name(type_name, cls.__name__)

        # Collect roles from type hints
        roles = {}

        # Check annotations for Role[T] fields
        annotations = getattr(cls, "__annotations__", {})
        for key, hint in annotations.items():
            if not key.startswith("_") and key != "flags":
                # Check if it's a Role[T] type
                origin = get_origin(hint)
                if origin is Role:
                    # It's Role[T]
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
            hints = getattr(cls, "__annotations__", {})

        # Rewrite annotations to add base types for type checker support
        new_annotations = {}

        for field_name, field_type in hints.items():
            if field_name.startswith("_"):
                new_annotations[field_name] = field_type
                continue
            if field_name == "flags":  # Skip the flags field itself
                new_annotations[field_name] = field_type
                continue
            if field_name in roles:  # Skip role fields
                new_annotations[field_name] = field_type
                continue

            # Get the default value (should be AttributeFlags from Flag())
            default_value = getattr(cls, field_name, None)

            # Extract attribute type and cardinality/key/unique metadata
            field_info = extract_metadata(field_type)

            # Check if field type is a list annotation
            field_origin = get_origin(field_type)
            is_list_type = field_origin is list

            # If we found an Attribute type, add it to owned attributes
            if field_info.attr_type is not None:
                # Validate: list[Type] must have Flag(Card(...))
                if is_list_type and not isinstance(default_value, AttributeFlags):
                    raise TypeError(
                        f"Field '{field_name}' in {cls.__name__}: "
                        f"list[Type] annotations must use Flag(Card(...)) to specify cardinality. "
                        f"Example: {field_name}: list[{field_info.attr_type.__name__}] = Flag(Card(min=1))"
                    )

                # Get flags from default value or create new flags
                if isinstance(default_value, AttributeFlags):
                    flags = default_value

                    # Validate: Flag(Card(...)) should only be used with list[Type]
                    if flags.has_explicit_card and not is_list_type:
                        raise TypeError(
                            f"Field '{field_name}' in {cls.__name__}: "
                            f"Flag(Card(...)) can only be used with list[Type] annotations. "
                            f"For optional single values, use Optional[{field_info.attr_type.__name__}] instead."
                        )

                    # Validate: list[Type] must have Flag(Card(...))
                    if is_list_type and not flags.has_explicit_card:
                        raise TypeError(
                            f"Field '{field_name}' in {cls.__name__}: "
                            f"list[Type] annotations must use Flag(Card(...)) to specify cardinality. "
                            f"Example: {field_name}: list[{field_info.attr_type.__name__}] = Flag(Card(min=1))"
                        )

                    # Merge with cardinality from type annotation if not already set
                    if flags.card_min is None and flags.card_max is None:
                        flags.card_min = field_info.card_min
                        flags.card_max = field_info.card_max
                    # Set is_key and is_unique from type annotation if found
                    if field_info.is_key:
                        flags.is_key = True
                    if field_info.is_unique:
                        flags.is_unique = True
                else:
                    # Create flags from type annotation metadata
                    flags = AttributeFlags(
                        is_key=field_info.is_key,
                        is_unique=field_info.is_unique,
                        card_min=field_info.card_min,
                        card_max=field_info.card_max,
                    )

                owned_attrs[field_name] = ModelAttrInfo(typ=field_info.attr_type, flags=flags)

                # Keep annotation as-is - no need for unions since validators always return Attribute instances
                # - position: Position → stays as Position
                # - salary: Salary | None → stays as Salary | None
                # - tags: list[Tag] → stays as list[Tag]
                new_annotations[field_name] = field_type
            else:
                new_annotations[field_name] = field_type

        # Update class annotations for Pydantic's benefit
        cls.__annotations__ = new_annotations
        cls._owned_attrs = owned_attrs

    @model_validator(mode="wrap")
    @classmethod
    def _wrap_raw_values(cls, values, handler):
        """Ensure all attribute fields are wrapped in Attribute instances.

        This catches edge cases like default values and model_copy that bypass validators.
        Uses 'wrap' mode to intercept all validation paths including model_copy.
        """
        # First, let Pydantic do its validation
        instance = handler(values)

        # Then wrap any raw values
        owned_attrs = cls.get_owned_attributes()
        for field_name, attr_info in owned_attrs.items():
            value = getattr(instance, field_name, None)
            if value is None:
                continue

            attr_class = attr_info.typ

            # Check if it's a list (multi-value attribute)
            if isinstance(value, list):
                wrapped_list = []
                for item in value:
                    if not isinstance(item, attr_class):
                        # Wrap raw value
                        wrapped_list.append(attr_class(item))
                    else:
                        wrapped_list.append(item)
                # Use object.__setattr__ to bypass validate_assignment and avoid recursion
                object.__setattr__(instance, field_name, wrapped_list)
            else:
                # Single value
                if not isinstance(value, attr_class):
                    # Wrap raw value
                    # Use object.__setattr__ to bypass validate_assignment and avoid recursion
                    object.__setattr__(instance, field_name, attr_class(value))

        return instance

    def model_copy(self, *, update: Mapping[str, Any] | None = None, deep: bool = False):
        """Override model_copy to ensure raw values are wrapped in Attribute instances.

        Pydantic's model_copy bypasses validators even with revalidate_instances='always',
        so we override it to force proper validation.
        """
        # Call parent model_copy
        copied = super().model_copy(update=update, deep=deep)

        # Force wrap any raw values in the update dict
        if update:
            owned_attrs = self.__class__.get_owned_attributes()
            for field_name, new_value in update.items():
                if field_name not in owned_attrs:
                    continue

                attr_info = owned_attrs[field_name]
                attr_class = attr_info.typ

                # Check if it's a list (multi-value attribute)
                if isinstance(new_value, list):
                    wrapped_list = []
                    for item in new_value:
                        if not isinstance(item, attr_class):
                            wrapped_list.append(attr_class(item))
                        else:
                            wrapped_list.append(item)
                    object.__setattr__(copied, field_name, wrapped_list)
                else:
                    # Single value
                    if not isinstance(new_value, attr_class):
                        object.__setattr__(copied, field_name, attr_class(new_value))

        return copied

    @classmethod
    def get_type_name(cls) -> str:
        """Get the TypeDB type name for this relation.

        If name is explicitly set in TypeFlags, it is used as-is.
        Otherwise, the class name is formatted according to the case parameter.
        """
        if cls._flags.name:
            return cls._flags.name
        return format_type_name(cls.__name__, cls._flags.case)

    @classmethod
    def get_supertype(cls) -> str | None:
        """Get the supertype from Python inheritance, skipping base classes.

        Base classes (with base=True) are Python-only and don't appear in TypeDB schema.
        This method skips them when determining the TypeDB supertype.

        Returns:
            Type name of the parent Relation class, or None if direct Relation subclass
        """
        for base in cls.__bases__:
            if base is not Relation and issubclass(base, Relation):
                # Skip base classes - they don't appear in TypeDB schema
                if base.is_base():
                    # Recursively find the first non-base parent
                    return base.get_supertype()
                return base.get_type_name()
        return None

    @classmethod
    def is_abstract(cls) -> bool:
        """Check if this is an abstract relation."""
        return cls._flags.abstract

    @classmethod
    def is_base(cls) -> bool:
        """Check if this is a Python base class (not in TypeDB schema)."""
        return cls._flags.base

    @classmethod
    def manager(cls: type[R], db: Any) -> RelationManager[R]:
        """Create a RelationManager for this relation type.

        Args:
            db: Database connection

        Returns:
            RelationManager instance for this relation type with proper type information

        Example:
            from type_bridge import Database

            db = Database()
            db.connect()

            # Create typed relation instance
            employment = Employment(
                employee=person,
                employer=company,
                position=Position("Engineer")
            )

            # Insert using manager - with full type safety!
            Employment.manager(db).insert(employment)
            # employment is inferred as Employment type by type checkers
        """
        from type_bridge.crud import RelationManager

        return RelationManager(db, cls)

    def to_insert_query(self, var: str = "$r") -> str:
        """Generate TypeQL insert query for this relation instance.

        Args:
            var: Variable name to use

        Returns:
            TypeQL insert pattern for the relation

        Example:
            >>> employment = Employment(employee=alice, employer=tech_corp, position="Engineer")
            >>> employment.to_insert_query()
            '$r (employee: $alice, employer: $tech_corp) isa employment, has position "Engineer"'
        """
        type_name = self.get_type_name()

        # Build role players
        role_parts = []
        for role_name, role in self.__class__._roles.items():
            # Get the entity from the instance
            entity = self.__dict__.get(role_name)
            if entity is not None:
                # Use the entity's variable or IID
                if hasattr(entity, "_iid") and entity._iid:
                    # Use existing entity's IID
                    role_parts.append(f"{role.role_name}: ${role_name}")
                else:
                    # New entity - use a variable
                    role_parts.append(f"{role.role_name}: ${role_name}")

        # Start with relation pattern
        relation_pattern = f"{var} ({', '.join(role_parts)}) isa {type_name}"
        parts = [relation_pattern]

        # Add attribute ownerships
        for field_name, attr_info in self._owned_attrs.items():
            value = getattr(self, field_name, None)
            if value is not None:
                attr_class = attr_info.typ
                attr_name = attr_class.get_attribute_name()

                # Handle lists (multi-value attributes)
                if isinstance(value, list):
                    for item in value:
                        parts.append(f"has {attr_name} {self._format_value(item)}")
                else:
                    parts.append(f"has {attr_name} {self._format_value(value)}")

        return ", ".join(parts)

    @staticmethod
    def _format_value(value: Any) -> str:
        """Format a Python value for TypeQL."""
        # Extract value from Attribute instances
        if isinstance(value, Attribute):
            value = value.value

        if isinstance(value, str):
            return f'"{value}"'
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, datetime_type):
            return f'"{value.isoformat()}"'
        else:
            return str(value)

    def insert(self: R, db: Database) -> R:
        """Insert this relation instance into the database.

        Args:
            db: Database connection

        Returns:
            Self for chaining

        Example:
            employment = Employment(
                position=Position("Engineer"),
                salary=Salary(100000),
                start_date=StartDate(datetime(2020, 1, 1)),
                active=Active(True),
                employee=person,
                employer=company
            )
            employment.insert(db)
        """
        # Use manager to insert
        manager = self.__class__.manager(db)
        manager.insert(self)
        return self

    @classmethod
    def get_owned_attributes(cls) -> dict[str, ModelAttrInfo]:
        """Get attributes owned by this relation.

        Returns:
            Dictionary mapping field names to ModelAttrInfo (typ + flags)
        """
        return cls._owned_attrs.copy()

    @classmethod
    def to_schema_definition(cls) -> str | None:
        """Generate TypeQL schema definition for this relation.

        Returns:
            TypeQL schema definition string, or None if this is a base class
        """
        # Base classes don't appear in TypeDB schema
        if cls.is_base():
            return None

        type_name = cls.get_type_name()
        lines = []

        # Define relation type with supertype from Python inheritance
        supertype = cls.get_supertype()
        if supertype:
            relation_def = f"relation {type_name} sub {supertype}"
        else:
            relation_def = f"relation {type_name}"

        if cls.is_abstract():
            relation_def += ", abstract"

        lines.append(relation_def)

        # Add roles
        for _role_name, role in cls._roles.items():
            lines.append(f"    relates {role.role_name}")

        # Add attribute ownerships
        for _field_name, attr_info in cls._owned_attrs.items():
            attr_class = attr_info.typ
            flags = attr_info.flags
            attr_name = attr_class.get_attribute_name()

            ownership = f"    owns {attr_name}"
            annotations = flags.to_typeql_annotations()
            if annotations:
                ownership += " " + " ".join(annotations)
            lines.append(ownership)

        # Join with commas, but end with semicolon (no comma before semicolon)
        return ",\n".join(lines) + ";"

    def __repr__(self) -> str:
        """Developer-friendly string representation of relation."""
        parts = []
        # Show role players
        for role_name in self._roles:
            player = getattr(self, role_name, None)
            if player is not None:
                parts.append(f"{role_name}={player!r}")
        # Show attributes
        for field_name in self._owned_attrs:
            value = getattr(self, field_name, None)
            if value is not None:
                parts.append(f"{field_name}={value!r}")
        return f"{self.__class__.__name__}({', '.join(parts)})"

    def __str__(self) -> str:
        """User-friendly string representation of relation."""
        parts = []

        # Show role players first (more important)
        role_parts = []
        for role_name, role in self._roles.items():
            player = getattr(self, role_name, None)
            # Only show role players that are actual entity instances (have _owned_attrs)
            if player is not None and hasattr(player, "_owned_attrs"):
                # Get a simple representation of the player (their key attribute)
                player_str = None
                for field_name, attr_info in player._owned_attrs.items():
                    if attr_info.flags.is_key:
                        key_value = getattr(player, field_name, None)
                        if key_value is not None:
                            if hasattr(key_value, "value"):
                                player_str = str(key_value.value)
                            else:
                                player_str = str(key_value)
                            break

                if player_str:
                    role_parts.append(f"{role_name}={player_str}")

        if role_parts:
            parts.append("(" + ", ".join(role_parts) + ")")

        # Show attributes
        attr_parts = []
        for field_name, attr_info in self._owned_attrs.items():
            value = getattr(self, field_name, None)
            if value is None:
                continue

            # Extract actual value from Attribute instance
            if hasattr(value, "value"):
                display_value = value.value
            else:
                display_value = value

            attr_parts.append(f"{field_name}={display_value}")

        if attr_parts:
            parts.append("[" + ", ".join(attr_parts) + "]")

        if parts:
            return f"{self.get_type_name()}{' '.join(parts)}"
        else:
            return f"{self.get_type_name()}()"

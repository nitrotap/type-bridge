"""Entity class for TypeDB entities."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar, dataclass_transform, get_origin, get_type_hints

from pydantic import ConfigDict
from pydantic._internal._model_construction import ModelMetaclass

from type_bridge.attribute import AttributeFlags, TypeFlags
from type_bridge.models.base import TypeDBType
from type_bridge.models.utils import ModelAttrInfo, extract_metadata

if TYPE_CHECKING:
    from type_bridge.crud import EntityManager
    from type_bridge.session import Database

# Type variable for self type
E = TypeVar("E", bound="Entity")


class EntityMeta(ModelMetaclass):
    """
    Metaclass for Entity that enables class-level field access for query building.

    Intercepts class-level attribute access to return FieldRef instances
    for defined fields, enabling syntax like Person.age.gt(Age(30)).
    """

    def __new__(
        mcs, name: str, bases: tuple[type, ...], namespace: dict[str, Any], **kwargs: Any
    ) -> type:
        """
        Create a new Entity class.

        Removes any non-default field values from namespace before Pydantic processes it.
        This prevents Pydantic from capturing spurious defaults.
        """
        import warnings

        # Now call parent __new__ (ModelMetaclass)
        # The smart __getattribute__ below will prevent FieldRef from being
        # captured as defaults during Pydantic's field collection
        # Suppress Pydantic's field shadowing warnings - field shadowing is intentional
        # in TypeBridge when child entities override parent attributes
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore", message=".*shadows an attribute.*", category=UserWarning
            )
            return super().__new__(mcs, name, bases, namespace, **kwargs)

    def __getattribute__(cls, name: str) -> Any:
        """
        Intercept class-level attribute access.

        For owned attributes AFTER initialization is complete, return FieldRef instances.
        During Pydantic initialization, return the actual descriptor.
        """
        # Check if this is a field and if we should return FieldRef
        try:
            owned_attrs = super().__getattribute__("_owned_attrs")
            pydantic_complete = super().__getattribute__("__pydantic_complete__")

            # Only return FieldRef if:
            # 1. Field is in owned_attrs (it's one of our fields)
            # 2. Pydantic setup is complete (__pydantic_complete__ is True)
            if name in owned_attrs and pydantic_complete:
                from type_bridge.fields import FieldDescriptor

                attr_info = owned_attrs[name]
                descriptor = FieldDescriptor(field_name=name, attr_type=attr_info.typ)
                return descriptor.__get__(None, cls)
        except AttributeError:
            # _owned_attrs or __pydantic_complete__ not defined yet
            pass

        # For all other cases, use normal access
        return super().__getattribute__(name)


@dataclass_transform(kw_only_default=True, field_specifiers=(AttributeFlags,))
class Entity(TypeDBType, metaclass=EntityMeta):
    """Base class for TypeDB entities with Pydantic validation.

    Entities own attributes defined as Attribute subclasses.
    Use TypeFlags to configure type name and abstract status.
    Supertype is determined automatically from Python inheritance.

    This class inherits from TypeDBType and Pydantic's BaseModel, providing:
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
            flags = TypeFlags(name="person")
            name: Name = Flag(Key)
            age: Age

        # Abstract entity
        class AbstractPerson(Entity):
            flags = TypeFlags(abstract=True)
            name: Name

        # Inheritance (Person sub abstract-person)
        class ConcretePerson(AbstractPerson):
            age: Age
    """

    # Pydantic configuration (extends TypeDBType config)
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        extra="allow",
        ignored_types=(TypeFlags,),
        revalidate_instances="always",
    )

    def __init_subclass__(cls) -> None:
        """Called when Entity subclass is created."""
        super().__init_subclass__()

        # Extract owned attributes from type hints
        owned_attrs: dict[str, ModelAttrInfo] = {}

        # Get direct annotations from this class
        direct_annotations = set(getattr(cls, "__annotations__", {}).keys())

        # Also include annotations from base=True parent classes
        # (they don't appear in TypeDB schema, so child must own their attributes)
        # Stop when we hit a non-base Entity class (it already handles its base=True parents)
        for base in cls.__mro__[1:]:  # Skip cls itself
            if base is Entity or not issubclass(base, Entity):
                continue
            if hasattr(base, "_flags") and base._flags.base:
                base_annotations = getattr(base, "__annotations__", {})
                direct_annotations.update(base_annotations.keys())
            else:
                # Stop at first non-base Entity class
                break

        try:
            # Use include_extras=True to preserve Annotated metadata
            all_hints = get_type_hints(cls, include_extras=True)
            # Filter to only include direct annotations and base=True parent annotations
            hints = {k: v for k, v in all_hints.items() if k in direct_annotations}
        except Exception:
            hints: dict[str, Any] = {
                k: v
                for k, v in getattr(cls, "__annotations__", {}).items()
                if k in direct_annotations
            }

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

        # Set explicit None defaults for optional fields (with | None in annotation)
        # Pydantic doesn't auto-default these in our metaclass setup
        from pydantic import Field

        from type_bridge.attribute import Attribute

        for field_name, attr_info in owned_attrs.items():
            # Check if there's already an explicit default value in __dict__
            # (avoid triggering __getattribute__ which might return FieldRef)
            existing_default = cls.__dict__.get(field_name, None)

            # Check if this is an optional field (card_min=0) without an explicit default
            if attr_info.flags.card_min == 0 and not attr_info.flags.has_explicit_card:
                # Only set Field(default=None) if there's no explicit Attribute instance default
                if not isinstance(existing_default, Attribute):
                    # This is an optional single-value field (Type | None) without explicit default
                    # Set explicit None default using Pydantic Field
                    type.__setattr__(cls, field_name, Field(default=None))

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
        # TypeDB 3.x syntax: entity name @abstract, sub parent,
        supertype = cls.get_supertype()
        is_abstract = cls.is_abstract()

        entity_def = f"entity {type_name}"
        if is_abstract:
            entity_def += " @abstract"
        if supertype:
            entity_def += f", sub {supertype}"

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

        # Use get_all_attributes to include inherited attributes
        for field_name, attr_info in self.get_all_attributes().items():
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

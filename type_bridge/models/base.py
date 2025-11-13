"""Abstract base class for TypeDB entities and relations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from datetime import date as date_type
from datetime import datetime as datetime_type
from datetime import timedelta
from typing import Any, ClassVar, dataclass_transform

from pydantic import BaseModel, ConfigDict, model_validator

from type_bridge.attribute import Attribute, AttributeFlags, EntityFlags, RelationFlags, TypeFlags
from type_bridge.attribute.flags import format_type_name
from type_bridge.models.utils import ModelAttrInfo, validate_type_name


@dataclass_transform(kw_only_default=False, field_specifiers=(AttributeFlags, TypeFlags))
class TypeDBType(BaseModel, ABC):
    """Abstract base class for TypeDB entities and relations.

    This class provides common functionality for both Entity and Relation types,
    including type name management, abstract/base flags, and attribute ownership.

    Subclasses must implement:
    - get_supertype(): Get parent type in TypeDB hierarchy
    - to_schema_definition(): Generate TypeQL schema definition
    - to_insert_query(): Generate TypeQL insert query for instances
    """

    # Pydantic configuration (inherited by Entity and Relation)
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        extra="allow",
        revalidate_instances="always",
    )

    # Internal metadata (class-level)
    _flags: ClassVar[TypeFlags] = TypeFlags()
    _owned_attrs: ClassVar[dict[str, ModelAttrInfo]] = {}
    _iid: str | None = None  # TypeDB internal ID

    def __init_subclass__(cls) -> None:
        """Called when a TypeDBType subclass is created."""
        super().__init_subclass__()

        # Get TypeFlags if defined, otherwise create new default flags
        # Check if flags is defined directly on this class (not inherited)
        if "flags" in cls.__dict__ and isinstance(cls.__dict__["flags"], (TypeFlags, EntityFlags, RelationFlags)):
            # Explicitly set flags on this class
            cls._flags = cls.__dict__["flags"]
        else:
            # No explicit flags on this class - create new default flags
            # This ensures each subclass gets its own flags instance
            cls._flags = TypeFlags()

        # Validate type name doesn't conflict with TypeDB built-ins
        # Skip validation for:
        # 1. Base classes that won't appear in schema (base=True)
        # 2. The abstract base Entity and Relation classes themselves
        is_base_entity_or_relation = (
            cls.__name__ in ("Entity", "Relation")
            and cls.__module__ in ("type_bridge.models", "type_bridge.models.entity", "type_bridge.models.relation")
        )
        if not cls._flags.base and not is_base_entity_or_relation:
            type_name = cls._flags.name or format_type_name(cls.__name__, cls._flags.case)
            validate_type_name(type_name, cls.__name__)

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
        """Get the TypeDB type name for this type.

        If name is explicitly set in TypeFlags, it is used as-is.
        Otherwise, the class name is formatted according to the case parameter.
        """
        if cls._flags.name:
            return cls._flags.name
        return format_type_name(cls.__name__, cls._flags.case)

    @classmethod
    @abstractmethod
    def get_supertype(cls) -> str | None:
        """Get the supertype from Python inheritance, skipping base classes.

        Base classes (with base=True) are Python-only and don't appear in TypeDB schema.
        This method skips them when determining the TypeDB supertype.

        Returns:
            Type name of the parent class, or None if direct subclass
        """
        ...

    @classmethod
    def is_abstract(cls) -> bool:
        """Check if this is an abstract type."""
        return cls._flags.abstract

    @classmethod
    def is_base(cls) -> bool:
        """Check if this is a Python base class (not in TypeDB schema)."""
        return cls._flags.base

    @classmethod
    def get_owned_attributes(cls) -> dict[str, ModelAttrInfo]:
        """Get attributes owned by this type.

        Returns:
            Dictionary mapping field names to ModelAttrInfo (typ + flags)
        """
        return cls._owned_attrs.copy()

    @classmethod
    @abstractmethod
    def to_schema_definition(cls) -> str | None:
        """Generate TypeQL schema definition for this type.

        Returns:
            TypeQL schema definition string, or None if this is a base class
        """
        ...

    @abstractmethod
    def to_insert_query(self, var: str) -> str:
        """Generate TypeQL insert query for this instance.

        Args:
            var: Variable name to use

        Returns:
            TypeQL insert pattern
        """
        ...

    @staticmethod
    def _format_value(value: Any) -> str:
        """Format a Python value for TypeQL."""
        from decimal import Decimal as DecimalType

        import isodate
        from isodate import Duration as IsodateDuration

        # Extract value from Attribute instances
        if isinstance(value, Attribute):
            value = value.value

        if isinstance(value, str):
            return f'"{value}"'
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, DecimalType):
            # TypeDB decimal literals require 'dec' suffix
            return f"{value}dec"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, (IsodateDuration, timedelta)):
            # TypeDB duration literals are unquoted ISO 8601 duration strings
            return isodate.duration_isoformat(value)
        elif isinstance(value, datetime_type):
            # TypeDB datetime literals are unquoted ISO 8601 strings
            return value.isoformat()
        elif isinstance(value, date_type):
            # TypeDB date literals are unquoted ISO 8601 date strings (YYYY-MM-DD)
            return value.isoformat()
        else:
            return str(value)

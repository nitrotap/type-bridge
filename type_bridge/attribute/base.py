"""Base Attribute class for TypeDB attribute types."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar

from type_bridge.validation import validate_type_name as validate_reserved_word

if TYPE_CHECKING:
    from type_bridge.attribute.flags import TypeNameCase
    from type_bridge.expressions import AggregateExpr, ComparisonExpr

# TypeDB built-in type names that cannot be used for attributes
TYPEDB_BUILTIN_TYPES = {"thing", "entity", "relation", "attribute"}


def _validate_attribute_name(attr_name: str, class_name: str) -> None:
    """Validate that an attribute name doesn't conflict with TypeDB built-ins or TypeQL keywords.

    Args:
        attr_name: The attribute name to validate
        class_name: The Python class name (for error messages)

    Raises:
        ValueError: If attribute name conflicts with a TypeDB built-in type
        ReservedWordError: If attribute name is a TypeQL reserved word
    """
    # First check TypeDB built-in types (thing, entity, relation, attribute)
    if attr_name.lower() in TYPEDB_BUILTIN_TYPES:
        raise ValueError(
            f"Attribute name '{attr_name}' for class '{class_name}' conflicts with TypeDB built-in type. "
            f"Built-in types are: {', '.join(sorted(TYPEDB_BUILTIN_TYPES))}. "
            f"Please rename your attribute class to avoid this conflict."
        )

    # Then check TypeQL reserved words
    # This will raise ReservedWordError if attr_name is reserved
    validate_reserved_word(attr_name, "attribute")


class Attribute(ABC):
    """Base class for TypeDB attributes.

    Attributes in TypeDB are value types that can be owned by entities and relations.

    Attribute instances can store values, allowing type-safe construction:
        Name("Alice")  # Creates Name instance with value "Alice"
        Age(30)        # Creates Age instance with value 30

    Type name formatting:
        You can control how the class name is converted to TypeDB attribute name
        using the 'case' class variable or 'attr_name' for explicit control.

    Example:
        class Name(String):
            pass  # TypeDB attribute: "Name" (default CLASS_NAME)

        class PersonName(String):
            case = TypeNameCase.SNAKE_CASE  # TypeDB attribute: "person_name"

        class PersonName(String):
            attr_name = "full_name"  # Explicit override

        class Age(Integer):
            pass

        class Person(Entity):
            name: Name
            age: Age

        # Direct instantiation with wrapped types (best practice):
        person = Person(name=Name("Alice"), age=Age(30))
    """

    # Class-level metadata
    value_type: ClassVar[str]  # TypeDB value type (string, integer, double, boolean, datetime)
    abstract: ClassVar[bool] = False
    attr_name: ClassVar[str | None] = None  # Explicit attribute name (optional)
    case: ClassVar["TypeNameCase | None"] = (
        None  # Case formatting option (optional, defaults to CLASS_NAME)
    )

    # Instance-level configuration (set via __init_subclass__)
    _attr_name: str | None = None
    _is_key: bool = False
    _supertype: str | None = None

    # Instance-level value storage
    _value: Any = None

    @abstractmethod
    def __init__(self, value: Any = None):
        """Initialize attribute with a value.

        Args:
            value: The value to store in this attribute instance
        """
        self._value = value

    def __init_subclass__(cls, **kwargs):
        """Called when a subclass is created."""
        super().__init_subclass__(**kwargs)

        # Import here to avoid circular dependency
        from type_bridge.attribute.flags import AttributeFlags, TypeNameCase, format_type_name

        # Determine the attribute name for this subclass
        # Priority: flags.name > attr_name > flags.case > class.case > default CLASS_NAME
        flags = getattr(cls, "flags", None)
        if isinstance(flags, AttributeFlags) and flags.name is not None:
            # flags.name has highest priority
            computed_name = flags.name
        elif cls.attr_name is not None:
            # Explicit attr_name takes precedence over formatting
            computed_name = cls.attr_name
        else:
            # Determine case formatting
            # Priority: flags.case > class.case > default CLASS_NAME
            if isinstance(flags, AttributeFlags) and flags.case is not None:
                case = flags.case
            elif cls.case is not None:
                case = cls.case
            else:
                case = TypeNameCase.CLASS_NAME

            # Apply case formatting to class name
            computed_name = format_type_name(cls.__name__, case)

        # Always set the attribute name for each new subclass (don't inherit from parent)
        # This ensures Name(String) gets _attr_name="name", not "string"
        cls._attr_name = computed_name

        # Skip validation for built-in attribute types (Boolean, Integer, String, etc.)
        # These are framework-provided and intentionally use TypeQL reserved words
        is_builtin = cls.__module__.startswith("type_bridge.attribute")

        # Validate attribute name doesn't conflict with TypeDB built-ins
        # Only validate user-defined attribute types, not framework built-ins
        if not is_builtin:
            _validate_attribute_name(cls._attr_name, cls.__name__)

    @property
    def value(self) -> Any:
        """Get the stored value."""
        return self._value

    def __str__(self) -> str:
        """String representation returns the stored value."""
        return str(self._value) if self._value is not None else ""

    def __repr__(self) -> str:
        """Repr shows the attribute type and value."""
        cls_name = self.__class__.__name__
        return f"{cls_name}({self._value!r})"

    def __eq__(self, other: object) -> bool:
        """Compare attribute with another attribute instance.

        For strict type safety, Attribute instances do NOT compare equal to raw values.
        To access the raw value, use the `.value` property.

        Examples:
            Age(20) == Age(20)  # True (same type, same value)
            Age(20) == Id(20)   # False (different types!)
            Age(20) == 20       # False (not equal to raw value!)
            Age(20).value == 20 # True (access raw value explicitly)
        """
        if isinstance(other, Attribute):
            # Compare two attribute instances: both type and value must match
            return type(self) is type(other) and self._value == other._value
        # Do not compare with non-Attribute objects (strict type safety)
        return False

    def __hash__(self) -> int:
        """Make attribute hashable based on its type and value."""
        return hash((type(self), self._value))

    @classmethod
    def get_attribute_name(cls) -> str:
        """Get the TypeDB attribute name.

        If attr_name is explicitly set, it is used as-is.
        Otherwise, the class name is formatted according to the case parameter.
        Default case is CLASS_NAME (preserves class name as-is).
        """
        return cls._attr_name or cls.__name__

    @classmethod
    def get_value_type(cls) -> str:
        """Get the TypeDB value type."""
        return cls.value_type

    @classmethod
    def is_key(cls) -> bool:
        """Check if this attribute is a key."""
        return cls._is_key

    @classmethod
    def is_abstract(cls) -> bool:
        """Check if this attribute is abstract."""
        return cls.abstract

    @classmethod
    def get_supertype(cls) -> str | None:
        """Get the supertype if this attribute extends another."""
        return cls._supertype

    @classmethod
    def to_schema_definition(cls) -> str:
        """Generate TypeQL schema definition for this attribute.

        Returns:
            TypeQL schema definition string
        """
        attr_name = cls.get_attribute_name()
        value_type = cls.get_value_type()

        # Check if this is a subtype
        if cls._supertype:
            definition = f"attribute {attr_name} sub {cls._supertype}, value {value_type}"
        else:
            definition = f"attribute {attr_name}, value {value_type}"

        if cls.abstract:
            definition += ", abstract"

        return definition + ";"

    # ========================================================================
    # Query Expression Class Methods (Type-Safe API)
    # ========================================================================

    @classmethod
    def gt(cls, value: "Attribute") -> "ComparisonExpr":
        """Create greater-than comparison expression.

        Args:
            value: Value to compare against

        Returns:
            ComparisonExpr for attr > value

        Example:
            Age.gt(Age(30))  # age > 30
        """
        from type_bridge.expressions import ComparisonExpr

        return ComparisonExpr(attr_type=cls, operator=">", value=value)

    @classmethod
    def lt(cls, value: "Attribute") -> "ComparisonExpr":
        """Create less-than comparison expression.

        Args:
            value: Value to compare against

        Returns:
            ComparisonExpr for attr < value

        Example:
            Age.lt(Age(30))  # age < 30
        """
        from type_bridge.expressions import ComparisonExpr

        return ComparisonExpr(attr_type=cls, operator="<", value=value)

    @classmethod
    def gte(cls, value: "Attribute") -> "ComparisonExpr":
        """Create greater-than-or-equal comparison expression.

        Args:
            value: Value to compare against

        Returns:
            ComparisonExpr for attr >= value

        Example:
            Salary.gte(Salary(80000.0))  # salary >= 80000
        """
        from type_bridge.expressions import ComparisonExpr

        return ComparisonExpr(attr_type=cls, operator=">=", value=value)

    @classmethod
    def lte(cls, value: "Attribute") -> "ComparisonExpr":
        """Create less-than-or-equal comparison expression.

        Args:
            value: Value to compare against

        Returns:
            ComparisonExpr for attr <= value

        Example:
            Age.lte(Age(65))  # age <= 65
        """
        from type_bridge.expressions import ComparisonExpr

        return ComparisonExpr(attr_type=cls, operator="<=", value=value)

    @classmethod
    def eq(cls, value: "Attribute") -> "ComparisonExpr":
        """Create equality comparison expression.

        Args:
            value: Value to compare against

        Returns:
            ComparisonExpr for attr == value

        Example:
            Status.eq(Status("active"))  # status == "active"
        """
        from type_bridge.expressions import ComparisonExpr

        return ComparisonExpr(attr_type=cls, operator="==", value=value)

    @classmethod
    def neq(cls, value: "Attribute") -> "ComparisonExpr":
        """Create not-equal comparison expression.

        Args:
            value: Value to compare against

        Returns:
            ComparisonExpr for attr != value

        Example:
            Status.neq(Status("deleted"))  # status != "deleted"
        """
        from type_bridge.expressions import ComparisonExpr

        return ComparisonExpr(attr_type=cls, operator="!=", value=value)

    @classmethod
    def sum(cls) -> "AggregateExpr":
        """Create sum aggregation expression.

        Returns:
            AggregateExpr for sum(attr)

        Example:
            Salary.sum()  # sum of all salaries
        """
        from type_bridge.expressions import AggregateExpr

        return AggregateExpr(attr_type=cls, function="sum")

    @classmethod
    def avg(cls) -> "AggregateExpr":
        """Create average (mean) aggregation expression.

        Note:
            Automatically converts to TypeQL 'mean' function.
            TypeDB 3.x uses 'mean' instead of 'avg'.

        Returns:
            AggregateExpr for mean(attr)

        Example:
            Age.avg()  # Generates TypeQL: mean($age)
        """
        from type_bridge.expressions import AggregateExpr

        return AggregateExpr(attr_type=cls, function="mean")

    @classmethod
    def max(cls) -> "AggregateExpr":
        """Create maximum aggregation expression.

        Returns:
            AggregateExpr for max(attr)

        Example:
            Score.max()  # maximum score
        """
        from type_bridge.expressions import AggregateExpr

        return AggregateExpr(attr_type=cls, function="max")

    @classmethod
    def min(cls) -> "AggregateExpr":
        """Create minimum aggregation expression.

        Returns:
            AggregateExpr for min(attr)

        Example:
            Price.min()  # minimum price
        """
        from type_bridge.expressions import AggregateExpr

        return AggregateExpr(attr_type=cls, function="min")

    @classmethod
    def median(cls) -> "AggregateExpr":
        """Create median aggregation expression.

        Returns:
            AggregateExpr for median(attr)

        Example:
            Salary.median()  # median salary
        """
        from type_bridge.expressions import AggregateExpr

        return AggregateExpr(attr_type=cls, function="median")

    @classmethod
    def std(cls) -> "AggregateExpr":
        """Create standard deviation aggregation expression.

        Returns:
            AggregateExpr for std(attr)

        Example:
            Score.std()  # standard deviation of scores
        """
        from type_bridge.expressions import AggregateExpr

        return AggregateExpr(attr_type=cls, function="std")

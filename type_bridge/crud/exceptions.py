"""CRUD operation exceptions for TypeBridge.

This module provides exception classes for CRUD operations to provide
clear and consistent error handling across entity and relation operations.
"""


class NotFoundError(LookupError):
    """Base class for not-found errors in CRUD operations.

    Raised when an entity or relation that was expected to exist
    cannot be found in the database.
    """

    pass


class EntityNotFoundError(NotFoundError):
    """Raised when an entity does not exist in the database.

    This exception is raised during delete or update operations
    when the target entity cannot be found using its @key attributes
    or matched attributes.

    Example:
        try:
            manager.delete(nonexistent_entity)
        except EntityNotFoundError:
            print("Entity was already deleted or never existed")
    """

    pass


class RelationNotFoundError(NotFoundError):
    """Raised when a relation does not exist in the database.

    This exception is raised during delete or update operations
    when the target relation cannot be found using its role players'
    @key attributes.

    Example:
        try:
            manager.delete(nonexistent_relation)
        except RelationNotFoundError:
            print("Relation was already deleted or never existed")
    """

    pass


class NotUniqueError(ValueError):
    """Raised when an operation requires exactly one match but finds multiple.

    This exception is raised when attempting to delete an entity without
    @key attributes and multiple matching records are found. Use
    filter().delete() for bulk deletion instead.

    Example:
        try:
            manager.delete(keyless_entity)
        except NotUniqueError:
            print("Multiple entities matched - use filter().delete() for bulk deletion")
    """

    pass

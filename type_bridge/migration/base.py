"""Migration base class for TypeDB schema migrations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from type_bridge.migration.operations import Operation
    from type_bridge.models import Entity, Relation


@dataclass
class MigrationDependency:
    """Reference to another migration.

    Example:
        dep = MigrationDependency("myapp", "0001_initial")
        str(dep)  # "myapp.0001_initial"
    """

    app_label: str
    migration_name: str

    def __str__(self) -> str:
        return f"{self.app_label}.{self.migration_name}"


class Migration:
    """Base class for migration scripts.

    Migrations define schema changes that can be applied to a TypeDB database.
    They can be either model-based (for initial migrations) or operation-based
    (for incremental changes).

    Model-based Migration Example:
        class InitialMigration(Migration):
            dependencies = []
            models = [Person, Company, Employment]

    Operation-based Migration Example:
        class AddPhoneMigration(Migration):
            dependencies = [("myapp", "0001_initial")]
            operations = [
                ops.AddAttribute(Phone),
                ops.AddOwnership(Person, Phone, optional=True),
            ]

    Attributes:
        name: Migration name (auto-populated from filename)
        app_label: Application label (auto-populated from directory)
        dependencies: List of (app_label, migration_name) tuples
        models: List of Entity/Relation classes for initial migrations
        operations: List of Operation instances for incremental migrations
        reversible: Whether the migration can be rolled back
    """

    # Migration identification (set by loader)
    name: str = ""
    app_label: str = ""

    # Dependencies (migrations that must run first)
    dependencies: ClassVar[list[tuple[str, str]]] = []

    # For initial migrations: declare models
    models: ClassVar[list[type[Entity | Relation]]] = []

    # For incremental migrations: declare operations
    operations: ClassVar[list[Operation]] = []

    # Reversibility flag
    reversible: ClassVar[bool] = True

    def get_dependencies(self) -> list[MigrationDependency]:
        """Get dependencies as MigrationDependency objects.

        Returns:
            List of MigrationDependency instances
        """
        return [MigrationDependency(app, name) for app, name in self.dependencies]

    def describe(self) -> str:
        """Generate a human-readable description of this migration.

        Returns:
            Description string
        """
        if self.models:
            model_names = [m.__name__ for m in self.models]
            return f"Initial migration with models: {', '.join(model_names)}"
        elif self.operations:
            op_count = len(self.operations)
            return f"Migration with {op_count} operation(s)"
        else:
            return "Empty migration"

    def __repr__(self) -> str:
        return f"<Migration {self.app_label}.{self.name}>"

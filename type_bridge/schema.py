"""Schema management utilities for TypeDB."""

from type_bridge.models import Entity, Relation
from type_bridge.session import Database


class SchemaManager:
    """Manager for database schema operations."""

    db: Database
    registered_models: list[type[Entity | Relation]]

    def __init__(self, db: Database):
        """Initialize schema manager.

        Args:
            db: Database connection
        """
        self.db = db
        self.registered_models = []

    def register(self, *models: type) -> None:
        """Register model classes for schema management.

        Args:
            models: Model classes to register
        """
        for model in models:
            if model not in self.registered_models:
                self.registered_models.append(model)

    def generate_schema(self) -> str:
        """Generate complete TypeQL schema definition.

        Returns:
            TypeQL schema definition string
        """
        lines = []

        # Separate entities and relations
        entities = []
        relations = []
        attribute_classes = set()

        for model in self.registered_models:
            if issubclass(model, Entity) and model is not Entity:
                entities.append(model)
            elif issubclass(model, Relation) and model is not Relation:
                relations.append(model)

            # Collect all attribute classes owned by this model
            owned_attrs = model.get_owned_attributes()
            for field_name, attr_info in owned_attrs.items():
                attribute_classes.add(attr_info.typ)

        # Define attributes first
        lines.append("define")
        lines.append("")

        # Sort attributes by name for consistent output
        sorted_attrs = sorted(attribute_classes, key=lambda x: x.get_attribute_name())
        for attr_class in sorted_attrs:
            lines.append(attr_class.to_schema_definition())

        lines.append("")

        # Define entities
        for entity_model in entities:
            lines.append(entity_model.to_schema_definition())
            lines.append("")

        # Define relations
        for relation_model in relations:
            lines.append(relation_model.to_schema_definition())

            # Add role player definitions
            for role_name, role in relation_model._roles.items():
                player_type = role.player_type
                lines.append(
                    f"{player_type} plays {relation_model.get_type_name()}:{role.role_name};"
                )
            lines.append("")

        return "\n".join(lines)

    def sync_schema(self, force: bool = False) -> None:
        """Synchronize database schema with registered models.

        Args:
            force: If True, recreate database from scratch
        """
        if force:
            # Delete and recreate database
            if self.db.database_exists():
                self.db.delete_database()
            self.db.create_database()

        # Ensure database exists
        if not self.db.database_exists():
            self.db.create_database()

        # Generate and apply schema
        schema = self.generate_schema()

        with self.db.transaction("schema") as tx:
            tx.execute(schema)
            tx.commit()

    def drop_schema(self) -> None:
        """Drop all schema definitions."""
        if self.db.database_exists():
            self.db.delete_database()

    def introspect_schema(self) -> dict[str, list[str]]:
        """Introspect current database schema.

        Returns:
            Dictionary of schema information
        """
        # Query to get all types
        query = """
        match
        $x sub thing;
        fetch
        $x: label;
        """

        with self.db.transaction("read") as tx:
            results = tx.execute(query)

        schema_info = {"entities": [], "relations": [], "attributes": []}

        for result in results:
            # Parse result to categorize types
            # This is a simplified implementation
            pass

        return schema_info


class MigrationManager:
    """Manager for schema migrations."""

    def __init__(self, db: Database):
        """Initialize migration manager.

        Args:
            db: Database connection
        """
        self.db = db
        self.migrations: list[tuple[str, str]] = []

    def add_migration(self, name: str, schema: str) -> None:
        """Add a migration.

        Args:
            name: Migration name
            schema: TypeQL schema definition
        """
        self.migrations.append((name, schema))

    def apply_migrations(self) -> None:
        """Apply all pending migrations."""
        for name, schema in self.migrations:
            print(f"Applying migration: {name}")

            with self.db.transaction("schema") as tx:
                tx.execute(schema)
                tx.commit()

            print(f"Migration {name} applied successfully")

    def create_attribute_migration(self, attr_name: str, value_type: str) -> str:
        """Create a migration to add an attribute.

        Args:
            attr_name: Attribute name
            value_type: Value type

        Returns:
            TypeQL migration
        """
        return f"define\nattribute {attr_name}, value {value_type};"

    def create_entity_migration(self, entity_name: str, attributes: list[str]) -> str:
        """Create a migration to add an entity.

        Args:
            entity_name: Entity name
            attributes: List of attribute names

        Returns:
            TypeQL migration
        """
        lines = ["define", f"entity {entity_name}"]
        for attr in attributes:
            lines.append(f"    owns {attr}")
        lines.append(";")
        return "\n".join(lines)

    def create_relation_migration(
        self, relation_name: str, roles: list[tuple[str, str]], attributes: list[str] | None = None
    ) -> str:
        """Create a migration to add a relation.

        Args:
            relation_name: Relation name
            roles: List of (role_name, player_type) tuples
            attributes: Optional list of attribute names

        Returns:
            TypeQL migration
        """
        lines = ["define", f"relation {relation_name}"]

        for role_name, _ in roles:
            lines.append(f"    relates {role_name}")

        if attributes:
            for attr in attributes:
                lines.append(f"    owns {attr}")

        lines.append(";")
        lines.append("")

        # Add role player definitions
        for role_name, player_type in roles:
            lines.append(f"{player_type} plays {relation_name}:{role_name};")

        return "\n".join(lines)

"""Schema manager for TypeDB schema operations."""

from type_bridge.models import Entity, Relation
from type_bridge.schema.exceptions import SchemaConflictError
from type_bridge.schema.info import SchemaInfo
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

    def collect_schema_info(self) -> SchemaInfo:
        """Collect schema information from registered models.

        Returns:
            SchemaInfo with entities, relations, and attributes
        """
        schema_info = SchemaInfo()

        for model in self.registered_models:
            if issubclass(model, Entity) and model is not Entity:
                schema_info.entities.append(model)
            elif issubclass(model, Relation) and model is not Relation:
                schema_info.relations.append(model)

            # Collect all attribute classes owned by this model
            owned_attrs = model.get_owned_attributes()
            for field_name, attr_info in owned_attrs.items():
                schema_info.attribute_classes.add(attr_info.typ)

        return schema_info

    def generate_schema(self) -> str:
        """Generate complete TypeQL schema definition.

        Returns:
            TypeQL schema definition string
        """
        # Collect schema information and generate TypeQL
        schema_info = self.collect_schema_info()
        return schema_info.to_typeql()

    def has_existing_schema(self) -> bool:
        """Check if database has existing schema defined.

        Returns:
            True if database exists and has custom schema beyond built-in types
        """
        if not self.db.database_exists():
            return False

        # Check if any of the registered types already exist in the schema
        # This is the most reliable way in TypeDB 3.x
        for model in self.registered_models:
            if issubclass(model, Entity) and model is not Entity:
                type_name = model.get_type_name()
                if self._type_exists(type_name, "entity"):
                    return True
            elif issubclass(model, Relation) and model is not Relation:
                type_name = model.get_type_name()
                if self._type_exists(type_name, "relation"):
                    return True

        return False

    def introspect_current_schema_info(self) -> SchemaInfo | None:
        """Introspect current database schema and build SchemaInfo.

        Note: This is a best-effort attempt. It cannot perfectly reconstruct
        Python class hierarchies from TypeDB schema.

        Returns:
            SchemaInfo with current schema, or None if database doesn't exist
        """
        if not self.db.database_exists():
            return None

        # For now, we return None and rely on has_existing_schema()
        # Full reconstruction would require complex TypeDB schema introspection
        return None

    def verify_compatibility(self, old_schema_info: SchemaInfo) -> None:
        """Verify that new schema is compatible with old schema.

        Checks for breaking changes (removed or modified types/attributes)
        and raises SchemaConflictError if found.

        Args:
            old_schema_info: The previous schema to compare against

        Raises:
            SchemaConflictError: If breaking changes are detected
        """
        new_schema_info = self.collect_schema_info()
        diff = old_schema_info.compare(new_schema_info)

        # Check for breaking changes
        has_breaking_changes = bool(
            diff.removed_entities
            or diff.removed_relations
            or diff.removed_attributes
            or diff.modified_entities
            or diff.modified_relations
        )

        if has_breaking_changes:
            raise SchemaConflictError(diff)

    def sync_schema(self, force: bool = False) -> None:
        """Synchronize database schema with registered models.

        Automatically checks for existing schema in the database and raises
        SchemaConflictError if schema already exists and might conflict.

        Args:
            force: If True, recreate database from scratch, ignoring conflicts

        Raises:
            SchemaConflictError: If database has existing schema and force=False
        """
        # Check for existing schema before making changes
        if not force and self.has_existing_schema():
            # In TypeDB 3.x, schema introspection is limited without instances
            # For safety, we treat any attempt to redefine existing types as a potential conflict
            existing_types = []
            for model in self.registered_models:
                if issubclass(model, Entity) and model is not Entity:
                    type_name = model.get_type_name()
                    if self._type_exists(type_name, "entity"):
                        existing_types.append(f"entity '{type_name}'")
                elif issubclass(model, Relation) and model is not Relation:
                    type_name = model.get_type_name()
                    if self._type_exists(type_name, "relation"):
                        existing_types.append(f"relation '{type_name}'")

            if existing_types:
                from type_bridge.schema.diff import SchemaDiff

                types_str = ", ".join(existing_types)
                raise SchemaConflictError(
                    SchemaDiff(),
                    message=(
                        f"Schema conflict detected! The following types already exist in the database: {types_str}\n"
                        "\n"
                        "Redefining existing types may cause:\n"
                        "  - Data loss if attributes or roles are removed\n"
                        "  - Schema conflicts if types are modified\n"
                        "  - Undefined behavior if ownership changes\n"
                        "\n"
                        "Resolution options:\n"
                        "1. Use sync_schema(force=True) to recreate database from scratch (⚠️  DATA LOSS)\n"
                        "2. Manually drop the existing database first\n"
                        "3. Use MigrationManager for incremental schema changes\n"
                        "4. Ensure no conflicting types exist before syncing\n"
                    ),
                )

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

    def _check_schema_conflicts(self) -> str:
        """Check if registered models conflict with existing database schema.

        Returns:
            String describing conflicts, or empty string if no conflicts
        """
        conflicts = []

        # Check each registered entity
        for model in self.registered_models:
            if issubclass(model, Entity) and model is not Entity:
                type_name = model.get_type_name()
                # Check if this entity type exists in database
                if self._type_exists(type_name, "entity"):
                    # Get attributes owned in database
                    db_attrs = self._get_owned_attributes(type_name, "entity")
                    # Get attributes from model
                    model_attrs = {
                        attr_info.typ.get_attribute_name()
                        for attr_info in model.get_owned_attributes().values()
                    }
                    # Check for removed attributes
                    removed = db_attrs - model_attrs
                    if removed:
                        conflicts.append(
                            f"  Entity '{type_name}': Removed attributes: {', '.join(sorted(removed))}"
                        )

            elif issubclass(model, Relation) and model is not Relation:
                type_name = model.get_type_name()
                # Check if this relation type exists in database
                if self._type_exists(type_name, "relation"):
                    # Get attributes owned in database
                    db_attrs = self._get_owned_attributes(type_name, "relation")
                    # Get attributes from model
                    model_attrs = {
                        attr_info.typ.get_attribute_name()
                        for attr_info in model.get_owned_attributes().values()
                    }
                    # Check for removed attributes
                    removed = db_attrs - model_attrs
                    if removed:
                        conflicts.append(
                            f"  Relation '{type_name}': Removed attributes: {', '.join(sorted(removed))}"
                        )

        return "\n".join(conflicts)

    def _type_exists(self, type_name: str, category: str) -> bool:
        """Check if a type exists in the database schema.

        Args:
            type_name: Name of the type to check
            category: Category of type ("entity" or "relation")

        Returns:
            True if type exists in schema, False otherwise
        """
        # Try to match any instance of this type
        query = f"""
        match
        $t isa {type_name};
        fetch {{
          $t.*
        }};
        """

        try:
            with self.db.transaction("read") as tx:
                # If type exists, query will succeed (even with 0 results)
                # If type doesn't exist, query will raise an error
                list(tx.execute(query))
                return True
        except Exception:
            # Type doesn't exist in schema
            return False

    def _get_owned_attributes(self, type_name: str, category: str) -> set[str]:
        """Get attributes owned by a type in the database schema.

        Args:
            type_name: Name of the type
            category: Category of type ("entity" or "relation")

        Returns:
            Set of attribute type names owned by this type
        """
        # First, try to query existing instances
        query = f"""
        match
        $t isa {type_name};
        fetch {{
          $t.*
        }};
        """

        try:
            with self.db.transaction("read") as tx:
                results = list(tx.execute(query))

                # Extract attribute types from the first result
                if results:
                    first_result = results[0]
                    # The result keys (excluding 't') are the attribute type names
                    attrs = set()
                    for key in first_result.keys():
                        if key != "t":
                            attrs.add(key)
                    return attrs

            # No instances exist - try to create a temporary one to introspect schema
            # Insert a minimal instance with default/null values for all required attributes
            # This is needed for conflict detection when no data exists yet
            insert_query = f"""
            insert
            $t isa {type_name};
            """

            with self.db.transaction("write") as tx:
                tx.execute(insert_query)
                tx.commit()

            # Now query the temporary instance
            with self.db.transaction("read") as tx:
                results = list(tx.execute(query))
                attrs = set()
                if results:
                    first_result = results[0]
                    for key in first_result.keys():
                        if key != "t":
                            attrs.add(key)

                # Delete the temporary instance
                delete_query = f"""
                match
                $t isa {type_name};
                delete
                $t;
                """
                with self.db.transaction("write") as tx2:
                    tx2.execute(delete_query)
                    tx2.commit()

                return attrs

        except Exception:
            # If query fails or we can't create temporary instance, return empty set
            return set()

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

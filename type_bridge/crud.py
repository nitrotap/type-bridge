"""CRUD operations for TypeDB entities and relations."""

from typing import Any, TypeVar

from type_bridge.models import Entity, Relation
from type_bridge.query import Query, QueryBuilder
from type_bridge.session import Database

T = TypeVar("T", bound=Entity)
R = TypeVar("R", bound=Relation)


class EntityManager:
    """Manager for entity CRUD operations."""

    def __init__(self, db: Database, model_class: type[T]):
        """Initialize entity manager.

        Args:
            db: Database connection
            model_class: Entity model class
        """
        self.db = db
        self.model_class = model_class

    def create(self, **attributes) -> T:
        """Create and insert a new entity.

        Args:
            attributes: Entity attributes

        Returns:
            Created entity instance
        """
        instance = self.model_class(**attributes)
        query = QueryBuilder.insert_entity(instance)

        with self.db.transaction("write") as tx:
            tx.execute(query.build())
            tx.commit()

        return instance

    def get(self, **filters) -> list[T]:
        """Get entities matching filters.

        Args:
            filters: Attribute filters

        Returns:
            List of matching entities
        """
        query = QueryBuilder.match_entity(self.model_class, **filters)
        query.fetch("$e")

        with self.db.transaction("read") as tx:
            results = tx.execute(query.build())

        # Convert results to entity instances
        entities = []
        for result in results:
            # Extract attributes from result
            attrs = self._extract_attributes(result)
            entity = self.model_class(**attrs)
            entities.append(entity)

        return entities

    def filter(self, **filters) -> "EntityQuery[T]":
        """Create a query for filtering entities.

        Args:
            filters: Attribute filters

        Returns:
            EntityQuery for chaining
        """
        return EntityQuery(self.db, self.model_class, filters)

    def all(self) -> list[T]:
        """Get all entities of this type.

        Returns:
            List of all entities
        """
        return self.get()

    def delete(self, **filters) -> int:
        """Delete entities matching filters.

        Args:
            filters: Attribute filters

        Returns:
            Number of entities deleted
        """
        # First match the entities
        query = Query()
        pattern_parts = [f"$e isa {self.model_class.get_type_name()}"]

        for attr_name, attr_value in filters.items():
            formatted_value = self._format_value(attr_value)
            pattern_parts.append(f"has {attr_name} {formatted_value}")

        pattern = ", ".join(pattern_parts)
        query.match(pattern)
        query.delete("$e")

        with self.db.transaction("write") as tx:
            results = tx.execute(query.build())
            tx.commit()

        return len(results) if results else 0

    def _extract_attributes(self, result: dict[str, Any]) -> dict[str, Any]:
        """Extract attributes from query result.

        Args:
            result: Query result dictionary

        Returns:
            Dictionary of attributes
        """
        attrs = {}
        # Extract attributes from owned attribute classes
        owned_attrs = self.model_class.get_owned_attributes()
        for field_name, attr_class in owned_attrs.items():
            attr_name = attr_class.get_attribute_name()
            if attr_name in result:
                attrs[field_name] = result[attr_name]
        return attrs

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


class EntityQuery:
    """Chainable query for entities."""

    def __init__(self, db: Database, model_class: type[T], filters: dict[str, Any]):
        """Initialize entity query.

        Args:
            db: Database connection
            model_class: Entity model class
            filters: Attribute filters
        """
        self.db = db
        self.model_class = model_class
        self.filters = filters
        self._limit_value: int | None = None
        self._offset_value: int | None = None

    def limit(self, limit: int) -> "EntityQuery[T]":
        """Limit number of results.

        Args:
            limit: Maximum number of results

        Returns:
            Self for chaining
        """
        self._limit_value = limit
        return self

    def offset(self, offset: int) -> "EntityQuery[T]":
        """Skip number of results.

        Args:
            offset: Number of results to skip

        Returns:
            Self for chaining
        """
        self._offset_value = offset
        return self

    def execute(self) -> list[T]:
        """Execute the query.

        Returns:
            List of matching entities
        """
        query = QueryBuilder.match_entity(self.model_class, **self.filters)
        query.fetch("$e")

        if self._limit_value is not None:
            query.limit(self._limit_value)
        if self._offset_value is not None:
            query.offset(self._offset_value)

        with self.db.transaction("read") as tx:
            results = tx.execute(query.build())

        # Convert results to entity instances
        entities = []
        for result in results:
            # Extract attributes from result
            owned_attrs = self.model_class.get_owned_attributes()
            attrs = {}
            for field_name, attr_class in owned_attrs.items():
                attr_name = attr_class.get_attribute_name()
                if attr_name in result:
                    attrs[field_name] = result[attr_name]
            entity = self.model_class(**attrs)
            entities.append(entity)

        return entities

    def first(self) -> T | None:
        """Get first matching entity.

        Returns:
            First entity or None
        """
        results = self.limit(1).execute()
        return results[0] if results else None

    def count(self) -> int:
        """Count matching entities.

        Returns:
            Number of matching entities
        """
        return len(self.execute())


class RelationManager:
    """Manager for relation CRUD operations."""

    def __init__(self, db: Database, model_class: type[R]):
        """Initialize relation manager.

        Args:
            db: Database connection
            model_class: Relation model class
        """
        self.db = db
        self.model_class = model_class

    def create(self, role_players: dict[str, Any], attributes: dict[str, Any] | None = None) -> R:
        """Create and insert a new relation.

        Args:
            role_players: Dictionary mapping role names to player entities (Entity instances)
            attributes: Optional dictionary of relation attributes

        Returns:
            Created relation instance

        Example:
            employment_manager = RelationManager(db, Employment)
            employment = employment_manager.create(
                role_players={"employee": person, "employer": company},
                attributes={"position": "Engineer", "salary": 100000}
            )
        """
        # Build the query
        query = Query()

        # First, we need to match the role players by their key attributes
        match_clauses = []
        role_var_map = {}

        for role_attr_name, player_entity in role_players.items():
            # Get the role from the model class
            role = self.model_class._roles.get(role_attr_name)
            if not role:
                raise ValueError(f"Unknown role: {role_attr_name}")

            # Create a variable for this player
            player_var = f"$player_{role_attr_name}"
            role_var_map[role_attr_name] = (player_var, role.role_name)

            # Match the player by their key attributes
            player_type = player_entity.get_type_name()
            owned_attrs = player_entity.get_owned_attributes()

            # Find key attributes to match
            match_parts = [f"{player_var} isa {player_type}"]
            for field_name, attr_class in owned_attrs.items():
                if attr_class.is_key():
                    value = player_entity._values.get(field_name)
                    if value is not None:
                        attr_name = attr_class.get_attribute_name()
                        formatted_value = self._format_value(value)
                        match_parts.append(f"has {attr_name} {formatted_value}")

            match_clauses.append(", ".join(match_parts))

        # Add all match clauses
        for match_clause in match_clauses:
            query.match(match_clause)

        # Build insert clause for the relation
        relation_parts = [f"$r ({', '.join([f'{role_name}: {var}' for var, role_name in role_var_map.values()])}) isa {self.model_class.get_type_name()}"]

        # Add attributes if provided
        if attributes:
            for attr_name, attr_value in attributes.items():
                formatted_value = self._format_value(attr_value)
                relation_parts.append(f"has {attr_name} {formatted_value}")

        query.insert(", ".join(relation_parts))

        # Execute the query
        with self.db.transaction("write") as tx:
            tx.execute(query.build())
            tx.commit()

        # Create and return instance
        instance_kwargs = {**role_players}
        if attributes:
            instance_kwargs.update(attributes)

        return self.model_class(**instance_kwargs)

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

    def get(self, **role_players) -> list[R]:
        """Get relations matching role players.

        Args:
            role_players: Role player filters

        Returns:
            List of matching relations
        """
        query = QueryBuilder.match_relation(self.model_class, role_players=role_players)
        query.fetch("$r")

        with self.db.transaction("read") as tx:
            results = tx.execute(query.build())

        # Convert results to relation instances
        relations = []
        for result in results:
            relation = self.model_class()
            relations.append(relation)

        return relations

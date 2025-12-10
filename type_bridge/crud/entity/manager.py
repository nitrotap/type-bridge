"""Entity CRUD operations manager."""

import re
from typing import TYPE_CHECKING, Any

from typedb.driver import TransactionType

from type_bridge.attribute.string import String
from type_bridge.expressions import AttributeExistsExpr, Expression
from type_bridge.models import Entity
from type_bridge.query import QueryBuilder
from type_bridge.session import Connection, ConnectionExecutor

from ..base import E
from ..exceptions import EntityNotFoundError, NotUniqueError
from ..utils import format_value, is_multi_value_attribute

if TYPE_CHECKING:
    from .group_by import GroupByQuery
    from .query import EntityQuery


class EntityManager[E: Entity]:
    """Manager for entity CRUD operations.

    Type-safe manager that preserves entity type information.
    """

    def __init__(
        self,
        connection: Connection,
        model_class: type[E],
    ):
        """Initialize entity manager.

        Args:
            connection: Database, Transaction, or TransactionContext
            model_class: Entity model class
        """
        self._connection = connection
        self._executor = ConnectionExecutor(connection)
        self.model_class = model_class

    def insert(self, entity: E) -> E:
        """Insert an entity instance into the database.

        Args:
            entity: Entity instance to insert

        Returns:
            The inserted entity instance

        Example:
            # Create typed entity instance with wrapped attributes
            person = Person(
                name=Name("Alice"),
                age=Age(30),
                email=Email("alice@example.com")
            )
            Person.manager(db).insert(person)
        """
        query = QueryBuilder.insert_entity(entity)

        self._execute(query.build(), TransactionType.WRITE)

        return entity

    def put(self, entity: E) -> E:
        """Put an entity instance into the database (insert if not exists).

        Uses TypeQL's PUT clause to ensure idempotent insertion. If the entity
        already exists (matching all attributes), no changes are made. If it doesn't
        exist, it's inserted.

        Args:
            entity: Entity instance to put

        Returns:
            The entity instance

        Example:
            # Create typed entity instance
            person = Person(
                name=Name("Alice"),
                age=Age(30),
                email=Email("alice@example.com")
            )
            # First call inserts, subsequent calls are idempotent
            Person.manager(db).put(person)
            Person.manager(db).put(person)  # No duplicate created
        """
        # Build PUT query similar to insert, but use "put" instead of "insert"
        pattern = entity.to_insert_query("$e")
        query = f"put\n{pattern};"

        self._execute(query, TransactionType.WRITE)

        return entity

    def put_many(self, entities: list[E]) -> list[E]:
        """Put multiple entities into the database (insert if not exists).

        Uses TypeQL's PUT clause with all-or-nothing semantics:
        - If ALL entities match existing data, nothing is inserted
        - If ANY entity doesn't match, ALL entities in the pattern are inserted

        This means if one entity already exists, attempting to put it with new entities
        may cause a key constraint violation.

        Args:
            entities: List of entity instances to put

        Returns:
            List of entity instances

        Example:
            persons = [
                Person(name="Alice", email="alice@example.com"),
                Person(name="Bob", email="bob@example.com"),
            ]
            # First call inserts all, subsequent identical calls are idempotent
            Person.manager(db).put_many(persons)
        """
        if not entities:
            return []

        # Build a single TypeQL PUT query with multiple patterns
        put_patterns = []
        for i, entity in enumerate(entities):
            # Use unique variable names for each entity
            var = f"$e{i}"
            pattern = entity.to_insert_query(var)
            put_patterns.append(pattern)

        # Combine all patterns into a single put query
        query = "put\n" + ";\n".join(put_patterns) + ";"

        self._execute(query, TransactionType.WRITE)

        return entities

    def update_many(self, entities: list[E]) -> list[E]:
        """Update multiple entities within a single transaction.

        Uses an existing transaction when supplied, otherwise opens one write
        transaction and reuses it for all updates to avoid N separate commits.

        Args:
            entities: Entity instances to update

        Returns:
            The list of updated entities
        """
        if not entities:
            return []

        if self._executor.has_transaction:
            for entity in entities:
                self.update(entity)
            return entities

        assert self._executor.database is not None
        with self._executor.database.transaction(TransactionType.WRITE) as tx_ctx:
            temp_manager = EntityManager(tx_ctx, self.model_class)
            for entity in entities:
                temp_manager.update(entity)

        return entities

    def insert_many(self, entities: list[E]) -> list[E]:
        """Insert multiple entities into the database in a single transaction.

        More efficient than calling insert() multiple times.

        Args:
            entities: List of entity instances to insert

        Returns:
            List of inserted entity instances

        Example:
            persons = [
                Person(name="Alice", email="alice@example.com"),
                Person(name="Bob", email="bob@example.com"),
                Person(name="Charlie", email="charlie@example.com"),
            ]
            Person.manager(db).insert_many(persons)
        """
        if not entities:
            return []

        # Build a single TypeQL query with multiple insert patterns
        insert_patterns = []
        for i, entity in enumerate(entities):
            # Use unique variable names for each entity
            var = f"$e{i}"
            pattern = entity.to_insert_query(var)
            insert_patterns.append(pattern)

        # Combine all patterns into a single insert query
        query = "insert\n" + ";\n".join(insert_patterns) + ";"

        self._execute(query, TransactionType.WRITE)

        return entities

    def get(self, **filters) -> list[E]:
        """Get entities matching filters.

        Args:
            filters: Attribute filters

        Returns:
            List of matching entities
        """
        query = QueryBuilder.match_entity(self.model_class, **filters)
        query.fetch("$e")  # Fetch all attributes with $e.*

        results = self._execute(query.build(), TransactionType.READ)

        # Convert results to entity instances
        entities = []
        for result in results:
            # Extract attributes from result
            attrs = self._extract_attributes(result)
            entity = self.model_class(**attrs)
            entities.append(entity)

        return entities

    def filter(self, *expressions: Any, **filters: Any) -> "EntityQuery[E]":
        """Create a query for filtering entities.

        Supports both expression-based and dictionary-based filtering.

        Args:
            *expressions: Expression objects (Age.gt(Age(30)), etc.)
            **filters: Attribute filters (exact match) - age=30, name="Alice"

        Returns:
            EntityQuery for chaining

        Examples:
            # Expression-based (advanced filtering)
            manager.filter(Age.gt(Age(30)))
            manager.filter(Age.gt(Age(18)), Age.lt(Age(65)))

            # Dictionary-based (exact match - legacy)
            manager.filter(age=30, name="Alice")

            # Mixed
            manager.filter(Age.gt(Age(30)), status="active")

        Raises:
            ValueError: If expression references attribute type not owned by entity
        """
        # Import here to avoid circular dependency
        from .query import EntityQuery

        base_filters: dict[str, Any] = {}
        lookup_expressions: list[Any] = []

        if filters:
            base_filters, lookup_expressions = self._parse_lookup_filters(filters)

        # Validate expressions reference owned attribute types (including inherited)
        if expressions:
            owned_attrs = self.model_class.get_all_attributes()
            owned_attr_types = {attr_info.typ for attr_info in owned_attrs.values()}

            for expr in expressions:
                # Get attribute types from expression
                expr_attr_types = expr.get_attribute_types()

                # Check if all attribute types are owned by entity
                for attr_type in expr_attr_types:
                    if attr_type not in owned_attr_types:
                        raise ValueError(
                            f"{self.model_class.__name__} does not own attribute type {attr_type.__name__}. "
                            f"Available attribute types: {', '.join(t.__name__ for t in owned_attr_types)}"
                        )

        query = EntityQuery(
            self._connection,
            self.model_class,
            base_filters if base_filters else None,
        )
        if expressions:
            query._expressions.extend(expressions)
        if lookup_expressions:
            query._expressions.extend(lookup_expressions)
        return query

    def group_by(self, *fields: Any) -> "GroupByQuery[E]":
        """Create a group-by query for aggregating by field values.

        Args:
            *fields: Field references to group by (Person.city, Person.department, etc.)

        Returns:
            GroupByQuery for aggregation

        Example:
            # Group by single field
            result = manager.group_by(Person.city).aggregate(Person.age.avg())

            # Group by multiple fields
            result = manager.group_by(Person.city, Person.department).aggregate(
                Person.salary.avg()
            )
        """
        # Import here to avoid circular dependency
        from .group_by import GroupByQuery

        return GroupByQuery(self._connection, self.model_class, {}, [], fields)

    def _parse_lookup_filters(self, filters: dict[str, Any]) -> tuple[dict[str, Any], list[Any]]:
        """Parse Django-style lookup filters into base filters and expressions."""

        owned_attrs = self.model_class.get_all_attributes()
        base_filters: dict[str, Any] = {}
        expressions: list[Any] = []

        for raw_key, raw_value in filters.items():
            if "__" not in raw_key:
                if raw_key not in owned_attrs:
                    raise ValueError(
                        f"Unknown filter field '{raw_key}' for {self.model_class.__name__}"
                    )
                if "__" in raw_key:
                    raise ValueError(
                        "Attribute names cannot contain '__' when using lookup filters"
                    )
                base_filters[raw_key] = raw_value
                continue

            field_name, lookup = raw_key.split("__", 1)
            if field_name not in owned_attrs:
                raise ValueError(
                    f"Unknown filter field '{field_name}' for {self.model_class.__name__}"
                )
            if "__" in field_name:
                raise ValueError("Attribute names cannot contain '__' when using lookup filters")

            attr_info = owned_attrs[field_name]
            attr_type = attr_info.typ

            # Normalize raw_value into Attribute instance for comparison/string ops
            def _wrap(value: Any):
                if isinstance(value, attr_type):
                    return value
                return attr_type(value)

            if lookup in ("exact", "eq"):
                base_filters[field_name] = raw_value
                continue

            if lookup in ("gt", "gte", "lt", "lte"):
                if not hasattr(attr_type, lookup):
                    raise ValueError(f"Lookup '{lookup}' not supported for {attr_type.__name__}")
                wrapped = _wrap(raw_value)
                expressions.append(getattr(attr_type, lookup)(wrapped))
                continue

            if lookup == "in":
                if not isinstance(raw_value, (list, tuple, set)):
                    raise ValueError("__in lookup requires an iterable of values")
                values = list(raw_value)
                if not values:
                    raise ValueError("__in lookup requires a non-empty iterable")
                eq_exprs = [attr_type.eq(_wrap(v)) for v in values]
                # Fold into OR chain
                expr: Expression = eq_exprs[0]
                for e in eq_exprs[1:]:
                    expr = expr.or_(e)
                expressions.append(expr)
                continue

            if lookup == "isnull":
                if not isinstance(raw_value, bool):
                    raise ValueError("__isnull lookup expects a boolean")
                expressions.append(AttributeExistsExpr(attr_type, present=not raw_value))
                continue

            if lookup in ("contains", "startswith", "endswith", "regex"):
                if not issubclass(attr_type, String):
                    raise ValueError(
                        f"String lookup '{lookup}' requires a String attribute (got {attr_type.__name__})"
                    )
                # Normalize to raw string
                raw_str = raw_value.value if hasattr(raw_value, "value") else str(raw_value)

                if lookup == "contains":
                    expressions.append(attr_type.contains(attr_type(raw_str)))
                elif lookup == "regex":
                    expressions.append(attr_type.regex(attr_type(raw_str)))
                elif lookup == "startswith":
                    pattern = f"^{re.escape(raw_str)}.*"
                    expressions.append(attr_type.regex(attr_type(pattern)))
                elif lookup == "endswith":
                    pattern = f".*{re.escape(raw_str)}$"
                    expressions.append(attr_type.regex(attr_type(pattern)))
                continue

            raise ValueError(f"Unsupported lookup operator '{lookup}'")

        return base_filters, expressions

    def all(self) -> list[E]:
        """Get all entities of this type.

        Returns:
            List of all entities
        """
        return self.get()

    def delete(self, entity: E) -> E:
        """Delete an entity instance from the database.

        Uses @key attributes to identify the entity (same as update).
        If no @key attributes exist, matches by ALL attributes and only
        deletes if exactly 1 match is found.

        Args:
            entity: Entity instance to delete (must have key attributes set,
                    or match exactly one record if no keys)

        Returns:
            The deleted entity instance

        Raises:
            ValueError: If key attribute value is None
            EntityNotFoundError: If entity does not exist in database
            NotUniqueError: If no @key and multiple matches found

        Example:
            alice = Person(name=Name("Alice"), age=Age(30))
            person_manager.insert(alice)

            # Delete using the instance
            deleted = person_manager.delete(alice)
        """
        owned_attrs = self.model_class.get_all_attributes()

        # Extract key attributes from entity for matching (same pattern as update)
        match_filters: dict[str, Any] = {}
        for field_name, attr_info in owned_attrs.items():
            if attr_info.flags.is_key:
                key_value = getattr(entity, field_name, None)
                if key_value is None:
                    msg = f"Key attribute '{field_name}' is required for delete"
                    raise ValueError(msg)
                # Extract value from Attribute instance if needed
                if hasattr(key_value, "value"):
                    key_value = key_value.value
                attr_name = attr_info.typ.get_attribute_name()
                match_filters[attr_name] = key_value

        # Fallback: no @key attributes - match by ALL attributes
        if not match_filters:
            all_filters: dict[str, Any] = {}
            filter_kwargs: dict[str, Any] = {}
            for field_name, attr_info in owned_attrs.items():
                value = getattr(entity, field_name, None)
                if value is not None:
                    # Store field_name -> attribute value for filter()
                    filter_kwargs[field_name] = value
                    # Store attr_name -> raw value for TypeQL query
                    if hasattr(value, "value"):
                        value = value.value
                    attr_name = attr_info.typ.get_attribute_name()
                    all_filters[attr_name] = value

            # Count matches first - only delete if exactly 1
            # Use existing filter().count() mechanism
            count = self.filter(**filter_kwargs).count()

            if count == 0:
                raise EntityNotFoundError(
                    f"Cannot delete: entity '{self.model_class.get_type_name()}' "
                    "not found with given attributes."
                )
            if count > 1:
                raise NotUniqueError(
                    f"Cannot delete: found {count} matches. "
                    "Entity without @key must match exactly 1 record. "
                    "Use filter().delete() for bulk deletion."
                )
            match_filters = all_filters
        else:
            # For keyed entities, check existence before delete
            filter_kwargs: dict[str, Any] = {}
            for field_name, attr_info in owned_attrs.items():
                if attr_info.flags.is_key:
                    value = getattr(entity, field_name, None)
                    if value is not None:
                        filter_kwargs[field_name] = value

            count = self.filter(**filter_kwargs).count()
            if count == 0:
                raise EntityNotFoundError(
                    f"Cannot delete: entity '{self.model_class.get_type_name()}' "
                    "not found with given key attributes."
                )

        # Build TypeQL: match $e isa type, has key value; delete $e;
        parts = [f"$e isa {self.model_class.get_type_name()}"]
        for attr_name, attr_value in match_filters.items():
            parts.append(f"has {attr_name} {format_value(attr_value)}")

        query_str = f"match\n{', '.join(parts)};\ndelete\n$e;"
        self._execute(query_str, TransactionType.WRITE)

        return entity

    def delete_many(self, entities: list[E]) -> list[E]:
        """Delete multiple entities within a single transaction.

        Uses an existing transaction when supplied, otherwise opens one write
        transaction and reuses it for all deletes to avoid N separate commits.

        Args:
            entities: Entity instances to delete

        Returns:
            The list of deleted entities

        Raises:
            ValueError: If any entity has no @key attributes and doesn't match exactly 1 record
            ValueError: If any key attribute value is None
        """
        if not entities:
            return []

        if self._executor.has_transaction:
            for entity in entities:
                self.delete(entity)
            return entities

        assert self._executor.database is not None
        with self._executor.database.transaction(TransactionType.WRITE) as tx_ctx:
            temp_manager = EntityManager(tx_ctx, self.model_class)
            for entity in entities:
                temp_manager.delete(entity)

        return entities

    def update(self, entity: E) -> E:
        """Update an entity in the database based on its current state.

        Reads all attribute values from the entity instance and persists them to the database.
        Uses key attributes to identify the entity.

        For single-value attributes (@card(0..1) or @card(1..1)), uses TypeQL update clause.
        For multi-value attributes (e.g., @card(0..5), @card(2..)), deletes old values
        and inserts new ones.

        Args:
            entity: The entity instance to update (must have key attributes set)

        Returns:
            The same entity instance

        Example:
            # Fetch entity
            alice = person_manager.get(name="Alice")[0]

            # Modify attributes directly
            alice.age = 31
            alice.tags = ["python", "typedb", "ai"]

            # Update in database
            person_manager.update(alice)
        """
        # Get all attributes (including inherited) to determine cardinality
        owned_attrs = self.model_class.get_all_attributes()

        # Extract key attributes from entity for matching
        match_filters = {}
        for field_name, attr_info in owned_attrs.items():
            if attr_info.flags.is_key:
                key_value = getattr(entity, field_name, None)
                if key_value is None:
                    msg = f"Key attribute '{field_name}' is required for update"
                    raise ValueError(msg)
                # Extract value from Attribute instance if needed
                if hasattr(key_value, "value"):
                    key_value = key_value.value
                attr_name = attr_info.typ.get_attribute_name()
                match_filters[attr_name] = key_value

        if not match_filters:
            msg = "Entity must have at least one @key attribute to be updated"
            raise ValueError(msg)

        # Separate single-value and multi-value updates from entity state
        single_value_updates = {}
        single_value_deletes = set()  # Track single-value attributes to delete
        multi_value_updates = {}

        for field_name, attr_info in owned_attrs.items():
            # Skip key attributes (they're used for matching)
            if attr_info.flags.is_key:
                continue

            attr_class = attr_info.typ
            attr_name = attr_class.get_attribute_name()
            flags = attr_info.flags

            # Get current value from entity
            current_value = getattr(entity, field_name, None)

            # Extract raw values from Attribute instances
            if current_value is not None:
                if isinstance(current_value, list):
                    # Multi-value: extract value from each Attribute in list
                    raw_values = []
                    for item in current_value:
                        if hasattr(item, "value"):
                            raw_values.append(item.value)
                        else:
                            raw_values.append(item)
                    current_value = raw_values
                elif hasattr(current_value, "value"):
                    # Single-value: extract value from Attribute
                    current_value = current_value.value

            # Determine if multi-value
            is_multi_value = is_multi_value_attribute(flags)

            if is_multi_value:
                # Multi-value: store as list (even if empty)
                if current_value is None:
                    current_value = []
                multi_value_updates[attr_name] = current_value
            else:
                # Single-value: handle updates and deletions
                if current_value is not None:
                    single_value_updates[attr_name] = current_value
                else:
                    # Check if attribute is optional (card_min == 0)
                    if flags.card_min == 0:
                        # Optional attribute set to None - needs to be deleted
                        single_value_deletes.add(attr_name)

        # Build TypeQL query
        query_parts = []

        # Match clause using key attributes
        match_statements = []
        entity_match_parts = [f"$e isa {self.model_class.get_type_name()}"]
        for attr_name, attr_value in match_filters.items():
            formatted_value = format_value(attr_value)
            entity_match_parts.append(f"has {attr_name} {formatted_value}")
        match_statements.append(", ".join(entity_match_parts) + ";")

        # Add match statements to bind multi-value attributes for deletion with optional guards
        if multi_value_updates:
            for attr_name, values in multi_value_updates.items():
                keep_literals = [format_value(v) for v in dict.fromkeys(values)]
                guard_lines = [
                    f"not {{ ${attr_name} == {literal}; }};" for literal in keep_literals
                ]
                try_block = "\n".join(
                    [
                        "try {",
                        f"  $e has {attr_name} ${attr_name};",
                        *[f"  {g}" for g in guard_lines],
                        "};",
                    ]
                )
                match_statements.append(try_block)

        # Add match statements to bind single-value attributes for deletion
        if single_value_deletes:
            for attr_name in single_value_deletes:
                match_statements.append(f"try {{ $e has {attr_name} ${attr_name}; }};")

        match_clause = "\n".join(match_statements)
        query_parts.append(f"match\n{match_clause}")

        # Delete clause (for multi-value and single-value deletions)
        delete_parts = []
        if multi_value_updates:
            for attr_name in multi_value_updates:
                delete_parts.append(f"try {{ ${attr_name} of $e; }};")
        if single_value_deletes:
            for attr_name in single_value_deletes:
                delete_parts.append(f"try {{ ${attr_name} of $e; }};")
        if delete_parts:
            delete_clause = "\n".join(delete_parts)
            query_parts.append(f"delete\n{delete_clause}")

        # Insert clause (for multi-value attributes with values)
        insert_parts = []
        for attr_name, values in multi_value_updates.items():
            for value in values:
                formatted_value = format_value(value)
                insert_parts.append(f"$e has {attr_name} {formatted_value};")
        if insert_parts:
            insert_clause = "\n".join(insert_parts)
            query_parts.append(f"insert\n{insert_clause}")

        # Update clause (for single-value attributes)
        if single_value_updates:
            update_parts = []
            for attr_name, value in single_value_updates.items():
                formatted_value = format_value(value)
                update_parts.append(f"$e has {attr_name} {formatted_value};")
            update_clause = "\n".join(update_parts)
            query_parts.append(f"update\n{update_clause}")

        # Combine and execute
        full_query = "\n".join(query_parts)

        self._execute(full_query, TransactionType.WRITE)

        return entity

    def _extract_attributes(self, result: dict[str, Any]) -> dict[str, Any]:
        """Extract attributes from query result.

        Args:
            result: Query result dictionary

        Returns:
            Dictionary of attributes
        """
        attrs = {}
        # Extract attributes from all attribute classes (including inherited)
        all_attrs = self.model_class.get_all_attributes()
        for field_name, attr_info in all_attrs.items():
            attr_class = attr_info.typ
            attr_name = attr_class.get_attribute_name()
            if attr_name in result:
                attrs[field_name] = result[attr_name]
            else:
                # For multi-value attributes, use empty list; for optional, use None
                is_multi_value = is_multi_value_attribute(attr_info.flags)
                attrs[field_name] = [] if is_multi_value else None
        return attrs

    def _execute(self, query: str, tx_type: TransactionType) -> list[dict[str, Any]]:
        """Execute a query using existing transaction if provided."""
        return self._executor.execute(query, tx_type)

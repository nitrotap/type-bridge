"""Chainable query operations for entities."""

import re
from typing import TYPE_CHECKING, Any

from type_bridge.models import Entity
from type_bridge.query import Query, QueryBuilder
from type_bridge.session import Database

from ..base import E
from ..utils import format_value, is_multi_value_attribute

if TYPE_CHECKING:
    from .group_by import GroupByQuery


class EntityQuery[E: Entity]:
    """Chainable query for entities.

    Type-safe query builder that preserves entity type information.
    Supports both dictionary filters (exact match) and expression-based filters.
    """

    def __init__(self, db: Database, model_class: type[E], filters: dict[str, Any] | None = None):
        """Initialize entity query.

        Args:
            db: Database connection
            model_class: Entity model class
            filters: Attribute filters (exact match) - optional, defaults to empty dict
        """
        self.db = db
        self.model_class = model_class
        self.filters = filters or {}
        self._expressions: list[Any] = []  # Store Expression objects
        self._limit_value: int | None = None
        self._offset_value: int | None = None

    def filter(self, *expressions: Any) -> "EntityQuery[E]":
        """Add expression-based filters to the query.

        Args:
            *expressions: Expression objects (ComparisonExpr, StringExpr, etc.)

        Returns:
            Self for chaining

        Example:
            query = Person.manager(db).filter(
                Age.gt(Age(30)),
                Name.contains(Name("Alice"))
            )

        Raises:
            ValueError: If expression references attribute type not owned by entity
        """
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

        self._expressions.extend(expressions)
        return self

    def limit(self, limit: int) -> "EntityQuery[E]":
        """Limit number of results.

        Args:
            limit: Maximum number of results

        Returns:
            Self for chaining
        """
        self._limit_value = limit
        return self

    def offset(self, offset: int) -> "EntityQuery[E]":
        """Skip number of results.

        Args:
            offset: Number of results to skip

        Returns:
            Self for chaining
        """
        self._offset_value = offset
        return self

    def execute(self) -> list[E]:
        """Execute the query.

        Returns:
            List of matching entities
        """
        query = QueryBuilder.match_entity(self.model_class, **self.filters)

        # Apply expression-based filters
        for expr in self._expressions:
            # Generate TypeQL pattern from expression
            pattern = expr.to_typeql("$e")
            query.match(pattern)

        query.fetch("$e")  # Fetch all attributes with $e.*

        # TypeDB 3.x requires sorting for pagination to work reliably
        # Always add sorting when using limit or offset to ensure consistent pagination
        if self._limit_value is not None or self._offset_value is not None:
            owned_attrs = self.model_class.get_all_attributes()
            sort_attr = None

            # Try to find a key attribute first (keys are always present and unique)
            for field_name, attr_info in owned_attrs.items():
                if attr_info.flags.is_key:
                    sort_attr = attr_info.typ.get_attribute_name()
                    break

            # If no key found, try to find any required attribute
            if sort_attr is None:
                for field_name, attr_info in owned_attrs.items():
                    if attr_info.flags.card_min is not None and attr_info.flags.card_min >= 1:
                        sort_attr = attr_info.typ.get_attribute_name()
                        break

            # Add sort clause with attribute variable
            if sort_attr:
                # Add attribute to match pattern
                query.match(f"$e has {sort_attr} $sort_attr")
                query.sort("$sort_attr", "asc")

        if self._limit_value is not None:
            query.limit(self._limit_value)
        if self._offset_value is not None:
            query.offset(self._offset_value)

        with self.db.transaction("read") as tx:
            results = tx.execute(query.build())

        # Convert results to entity instances
        entities = []
        owned_attrs = self.model_class.get_all_attributes()
        for result in results:
            # Extract attributes from result
            attrs = {}
            for field_name, attr_info in owned_attrs.items():
                attr_class = attr_info.typ
                attr_name = attr_class.get_attribute_name()
                if attr_name in result:
                    attrs[field_name] = result[attr_name]
                else:
                    # For list fields (has_explicit_card), default to empty list
                    # For other optional fields, explicitly set to None
                    if attr_info.flags.has_explicit_card:
                        attrs[field_name] = []
                    else:
                        attrs[field_name] = None
            entity = self.model_class(**attrs)
            entities.append(entity)

        return entities

    def first(self) -> E | None:
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

    def delete(self) -> int:
        """Delete all entities matching the current filters.

        Builds and executes a delete query based on the current filter state.
        Uses a single transaction for atomic deletion.

        Returns:
            Number of entities deleted

        Example:
            # Delete all persons over 65
            count = Person.manager(db).filter(Age.gt(Age(65))).delete()
            print(f"Deleted {count} persons")

            # Delete with multiple filters
            count = Person.manager(db).filter(
                Age.lt(Age(18)),
                Status.eq(Status("inactive"))
            ).delete()
        """
        # Build match clause
        query = Query()
        pattern_parts = [f"$e isa {self.model_class.get_type_name()}"]

        # Add dictionary-based filters (exact match)
        owned_attrs = self.model_class.get_owned_attributes()
        for field_name, field_value in self.filters.items():
            if field_name in owned_attrs:
                attr_info = owned_attrs[field_name]
                attr_name = attr_info.typ.get_attribute_name()
                formatted_value = format_value(field_value)
                pattern_parts.append(f"has {attr_name} {formatted_value}")

        # Combine base pattern
        pattern = ", ".join(pattern_parts)
        query.match(pattern)

        # Add expression-based filters
        for expr in self._expressions:
            expr_pattern = expr.to_typeql("$e")
            query.match(expr_pattern)

        # Add delete clause
        query.delete("$e")

        # Execute in single transaction
        with self.db.transaction("write") as tx:
            results = tx.execute(query.build())
            tx.commit()

        return len(results) if results else 0

    def update_with(self, func: Any) -> list[E]:
        """Update entities by applying a function to each matching entity.

        Fetches all matching entities, applies the provided function to each one,
        then saves all updates in a single transaction. If the function raises an
        error on any entity, stops immediately and raises the error.

        Args:
            func: Callable that takes an entity and modifies it in-place.
                  Can be a lambda or regular function.

        Returns:
            List of updated entities

        Example:
            # Increment age for all persons over 30
            updated = Person.manager(db).filter(Age.gt(Age(30))).update_with(
                lambda person: setattr(person, 'age', Age(person.age.value + 1))
            )

            # Complex update with function
            def promote(person):
                person.status = Status("promoted")
                if person.salary:
                    person.salary = Salary(int(person.salary.value * 1.1))

            promoted = Person.manager(db).filter(
                Department.eq(Department("Engineering"))
            ).update_with(promote)

        Raises:
            Any exception raised by the function during processing
        """
        # Fetch all matching entities
        entities = self.execute()

        # Return empty list if no matches
        if not entities:
            return []

        # Apply function to each entity (stop and raise if error)
        for entity in entities:
            func(entity)

        # Update all entities in a single transaction
        with self.db.transaction("write") as tx:
            for entity in entities:
                # Build update query for this entity
                query_str = self._build_update_query(entity)
                tx.execute(query_str)
            tx.commit()

        return entities

    def _build_update_query(self, entity: E) -> str:
        """Build update query for a single entity.

        Args:
            entity: Entity instance to update

        Returns:
            TypeQL update query string
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
                # Single-value: skip None values for optional attributes
                if current_value is not None:
                    single_value_updates[attr_name] = current_value

        # Build TypeQL query
        query_parts = []

        # Match clause using key attributes
        match_statements = []
        entity_match_parts = [f"$e isa {self.model_class.get_type_name()}"]
        for attr_name, attr_value in match_filters.items():
            formatted_value = format_value(attr_value)
            entity_match_parts.append(f"has {attr_name} {formatted_value}")
        match_statements.append(", ".join(entity_match_parts) + ";")

        # Add match statements to bind multi-value attributes for deletion
        if multi_value_updates:
            for attr_name in multi_value_updates:
                match_statements.append(f"$e has {attr_name} ${attr_name};")

        match_clause = "\n".join(match_statements)
        query_parts.append(f"match\n{match_clause}")

        # Delete clause (for multi-value attributes)
        if multi_value_updates:
            delete_parts = []
            for attr_name in multi_value_updates:
                delete_parts.append(f"${attr_name} of $e;")
            delete_clause = "\n".join(delete_parts)
            query_parts.append(f"delete\n{delete_clause}")

        # Insert clause (for multi-value attributes)
        if multi_value_updates:
            insert_parts = []
            for attr_name, values in multi_value_updates.items():
                for value in values:
                    formatted_value = format_value(value)
                    insert_parts.append(f"$e has {attr_name} {formatted_value};")
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

        # Combine and return
        return "\n".join(query_parts)

    def aggregate(self, *aggregates: Any) -> dict[str, Any]:
        """Execute aggregation queries.

        Performs database-side aggregations for efficiency.

        Args:
            *aggregates: AggregateExpr objects (Person.age.avg(), Person.score.sum(), etc.)

        Returns:
            Dictionary mapping aggregate keys to results

        Examples:
            # Single aggregation
            result = manager.filter().aggregate(Person.age.avg())
            avg_age = result['avg_age']

            # Multiple aggregations
            result = manager.filter(Person.city.eq(City("NYC"))).aggregate(
                Person.age.avg(),
                Person.score.sum(),
                Person.salary.max()
            )
            avg_age = result['avg_age']
            total_score = result['sum_score']
            max_salary = result['max_salary']
        """
        from type_bridge.expressions import AggregateExpr

        if not aggregates:
            raise ValueError("At least one aggregation expression required")

        # Build base match query with filters
        query = QueryBuilder.match_entity(self.model_class, **self.filters)

        # Apply expression-based filters
        for expr in self._expressions:
            pattern = expr.to_typeql("$e")
            query.match(pattern)

        # Build reduce query with aggregations
        # TypeQL 3.x syntax: reduce $result = function($var);
        # First, we need to bind all the fields being aggregated in the match clause
        reduce_clauses = []
        for agg in aggregates:
            if not isinstance(agg, AggregateExpr):
                raise TypeError(f"Expected AggregateExpr, got {type(agg).__name__}")

            # If this aggregation is on a specific attr_type (not count), add binding pattern
            if agg.attr_type is not None:
                attr_name = agg.attr_type.get_attribute_name()
                attr_var = f"${attr_name.lower()}"
                query.match(f"$e has {attr_name} {attr_var}")

            # Generate reduce clause: $result_var = function($var)
            result_var = f"${agg.get_fetch_key()}"
            reduce_clauses.append(f"{result_var} = {agg.to_typeql('$e')}")

        # Convert match to reduce query
        match_clause = query.build().replace("fetch", "get").split("fetch")[0]
        reduce_query = f"{match_clause}\nreduce {', '.join(reduce_clauses)};"

        with self.db.transaction("read") as tx:
            results = tx.execute(reduce_query)

        # Parse aggregation results
        # TypeDB 3.x reduce operator returns results as formatted strings
        if not results:
            return {}

        result = results[0] if results else {}

        # TypeDB reduce returns results as a formatted string in 'result' key
        # Format: '|  $var_name: Value(type: value)  |'
        output = {}
        if "result" in result:
            result_str = result["result"]
            # Parse variable names and values from the formatted string
            # Pattern: $variable_name: Value(type: actual_value)
            pattern = r"\$([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*Value\([^:]+:\s*([^)]+)\)"
            matches = re.findall(pattern, result_str)

            for var_name, value_str in matches:
                # Try to convert the value to appropriate Python type
                try:
                    # Try float first (covers both int and float)
                    if "." in value_str:
                        value = float(value_str)
                    else:
                        value = int(value_str)
                except ValueError:
                    # Keep as string if conversion fails
                    value = value_str.strip()

                output[var_name] = value

        return output

    def group_by(self, *fields: Any) -> "GroupByQuery[E]":
        """Group entities by field values.

        Args:
            *fields: FieldRef objects to group by

        Returns:
            GroupByQuery for chained aggregations

        Example:
            result = manager.group_by(Person.city).aggregate(Person.age.avg())
        """
        # Import here to avoid circular dependency
        from .group_by import GroupByQuery

        return GroupByQuery(self.db, self.model_class, self.filters, self._expressions, fields)

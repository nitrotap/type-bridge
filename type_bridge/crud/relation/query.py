"""RelationQuery for chainable relation queries."""

from typing import TYPE_CHECKING, Any

from type_bridge.models import Relation
from type_bridge.query import Query
from type_bridge.session import Database

from ..base import R
from ..utils import format_value, is_multi_value_attribute

if TYPE_CHECKING:
    from .group_by import RelationGroupByQuery


class RelationQuery[R: Relation]:
    """Chainable query for relations.

    Type-safe query builder that preserves relation type information.
    Supports both dictionary filters (exact match) and expression-based filters.
    """

    def __init__(self, db: Database, model_class: type[R], filters: dict[str, Any] | None = None):
        """Initialize relation query.

        Args:
            db: Database connection
            model_class: Relation model class
            filters: Attribute and role player filters (exact match) - optional
        """
        self.db = db
        self.model_class = model_class
        self.filters = filters or {}
        self._expressions: list[Any] = []  # Store Expression objects
        self._limit_value: int | None = None
        self._offset_value: int | None = None

    def filter(self, *expressions: Any) -> "RelationQuery[R]":
        """Add expression-based filters to the query.

        Args:
            *expressions: Expression objects (ComparisonExpr, StringExpr, etc.)

        Returns:
            Self for chaining

        Example:
            query = Employment.manager(db).filter(
                Salary.gt(Salary(100000)),
                Position.contains(Position("Engineer"))
            )

        Raises:
            ValueError: If expression references attribute type not owned by relation
        """
        # Validate expressions reference owned attribute types
        if expressions:
            owned_attrs = self.model_class.get_all_attributes()
            owned_attr_types = {attr_info.typ for attr_info in owned_attrs.values()}

            for expr in expressions:
                # Get attribute types from expression
                expr_attr_types = expr.get_attribute_types()

                # Check if all attribute types are owned by relation
                for attr_type in expr_attr_types:
                    if attr_type not in owned_attr_types:
                        raise ValueError(
                            f"{self.model_class.__name__} does not own attribute type {attr_type.__name__}. "
                            f"Available attribute types: {', '.join(t.__name__ for t in owned_attr_types)}"
                        )

        self._expressions.extend(expressions)
        return self

    def limit(self, limit: int) -> "RelationQuery[R]":
        """Limit number of results.

        Note: Requires sorting for stable pagination. A required attribute will be
        automatically selected for sorting.

        Args:
            limit: Maximum number of results

        Returns:
            Self for chaining
        """
        self._limit_value = limit
        return self

    def offset(self, offset: int) -> "RelationQuery[R]":
        """Skip number of results.

        Note: Requires sorting for stable pagination. A required attribute will be
        automatically selected for sorting.

        Args:
            offset: Number of results to skip

        Returns:
            Self for chaining
        """
        self._offset_value = offset
        return self

    def execute(self) -> list[R]:
        """Execute the query.

        Returns:
            List of matching relations
        """

        # Get all attributes (including inherited)
        all_attrs = self.model_class.get_all_attributes()

        # Separate attribute filters from role player filters
        attr_filters = {}
        role_player_filters = {}

        for key, value in self.filters.items():
            if key in self.model_class._roles:
                # This is a role player filter
                role_player_filters[key] = value
            elif key in all_attrs:
                # This is an attribute filter
                attr_filters[key] = value
            else:
                raise ValueError(f"Unknown filter: {key}")

        # Build match clause with inline role players
        role_parts = []
        role_info = {}  # role_name -> (var, entity_class)
        for role_name, role in self.model_class._roles.items():
            role_var = f"${role_name}"
            role_parts.append(f"{role.role_name}: {role_var}")
            role_info[role_name] = (role_var, role.player_entity_type)

        roles_str = ", ".join(role_parts)
        match_clauses = [f"$r isa {self.model_class.get_type_name()} ({roles_str})"]

        # Add dict-based attribute filters
        for field_name, value in attr_filters.items():
            attr_info = all_attrs[field_name]
            attr_name = attr_info.typ.get_attribute_name()
            formatted_value = format_value(value)
            match_clauses.append(f"$r has {attr_name} {formatted_value}")

        # Add role player filter clauses
        for role_name, player_entity in role_player_filters.items():
            role_var = f"${role_name}"
            entity_class = role_info[role_name][1]

            # Match the role player by their key attributes (including inherited)
            player_owned_attrs = entity_class.get_all_attributes()
            for field_name, attr_info in player_owned_attrs.items():
                if attr_info.flags.is_key:
                    key_value = getattr(player_entity, field_name, None)
                    if key_value is not None:
                        attr_name = attr_info.typ.get_attribute_name()
                        # Extract value from Attribute instance if needed
                        if hasattr(key_value, "value"):
                            key_value = key_value.value
                        formatted_value = format_value(key_value)
                        match_clauses.append(f"{role_var} has {attr_name} {formatted_value}")
                        break

        # Apply expression-based filters
        for expr in self._expressions:
            # Generate TypeQL pattern from expression
            pattern = expr.to_typeql("$r")
            match_clauses.append(pattern)

        match_str = ";\n".join(match_clauses) + ";"

        # Build fetch clause with nested structure for role players
        fetch_items = []

        # Add relation attributes (including inherited)
        for field_name, attr_info in all_attrs.items():
            attr_name = attr_info.typ.get_attribute_name()
            # Multi-value attributes need to be wrapped in [] for TypeQL fetch
            if is_multi_value_attribute(attr_info.flags):
                fetch_items.append(f'"{attr_name}": [$r.{attr_name}]')
            else:
                fetch_items.append(f'"{attr_name}": $r.{attr_name}')

        # Add each role player as nested object
        for role_name, (role_var, entity_class) in role_info.items():
            fetch_items.append(f'"{role_name}": {{\n    {role_var}.*\n  }}')

        fetch_body = ",\n  ".join(fetch_items)

        # Add sorting for pagination (required for stable limit/offset)
        sort_clause = ""
        if self._limit_value is not None or self._offset_value is not None:
            # Find a required attribute to sort by (not already filtered)
            sort_attr = None
            already_matched_attrs = set()
            for field_name in attr_filters.keys():
                attr_info = all_attrs[field_name]
                already_matched_attrs.add(attr_info.typ.get_attribute_name())

            # Try to find a required attribute that isn't already matched
            for field_name, attr_info in all_attrs.items():
                attr_name = attr_info.typ.get_attribute_name()
                if attr_name not in already_matched_attrs:
                    if attr_info.flags.is_key or (
                        attr_info.flags.card_min is not None and attr_info.flags.card_min >= 1
                    ):
                        sort_attr = attr_name
                        break

            if sort_attr:
                # Add sort binding to match
                match_str = match_str.rstrip(";")
                match_str += f";\n$r has {sort_attr} $sort_attr;"
                sort_clause = "\nsort $sort_attr;"

        # Add limit/offset clauses
        pagination_clause = ""
        if self._offset_value is not None:
            pagination_clause += f"\noffset {self._offset_value};"
        if self._limit_value is not None:
            pagination_clause += f"\nlimit {self._limit_value};"

        fetch_str = f"fetch {{\n  {fetch_body}\n}};"
        query_str = f"match\n{match_str}{sort_clause}{pagination_clause}\n{fetch_str}"

        with self.db.transaction("read") as tx:
            results = tx.execute(query_str)

        # Convert results to relation instances
        relations = []

        for result in results:
            # Extract relation attributes (including inherited)
            attrs = {}
            for field_name, attr_info in all_attrs.items():
                attr_class = attr_info.typ
                attr_name = attr_class.get_attribute_name()
                if attr_name in result:
                    raw_value = result[attr_name]
                    # Multi-value attributes need explicit conversion from list of raw values
                    if is_multi_value_attribute(attr_info.flags) and isinstance(raw_value, list):
                        # Convert each raw value to Attribute instance
                        attrs[field_name] = [attr_class(v) for v in raw_value]
                    else:
                        # Single value - let Pydantic handle conversion via model constructor
                        attrs[field_name] = raw_value
                else:
                    # For list fields (has_explicit_card), default to empty list
                    # For other optional fields, explicitly set to None
                    if attr_info.flags.has_explicit_card:
                        attrs[field_name] = []
                    else:
                        attrs[field_name] = None

            # Create relation instance
            relation = self.model_class(**attrs)

            # Extract role players from nested objects in result
            for role_name, (role_var, entity_class) in role_info.items():
                if role_name in result and isinstance(result[role_name], dict):
                    player_data = result[role_name]
                    # Extract player attributes (including inherited)
                    player_attrs = {}
                    for field_name, attr_info in entity_class.get_all_attributes().items():
                        attr_class = attr_info.typ
                        attr_name = attr_class.get_attribute_name()
                        if attr_name in player_data:
                            raw_value = player_data[attr_name]
                            # Multi-value attributes need explicit conversion from list of raw values
                            # Use static method to avoid binding issues between EntityQuery/RelationQuery
                            if (
                                hasattr(attr_info.flags, "has_explicit_card")
                                and attr_info.flags.has_explicit_card
                            ):
                                is_multi = True
                            elif (
                                hasattr(attr_info.flags, "card_min")
                                and attr_info.flags.card_min is not None
                            ):
                                is_multi = attr_info.flags.card_min > 1 or (
                                    hasattr(attr_info.flags, "card_max")
                                    and attr_info.flags.card_max is not None
                                    and attr_info.flags.card_max != 1
                                )
                            else:
                                is_multi = False
                            if is_multi and isinstance(raw_value, list):
                                # Convert each raw value to Attribute instance
                                player_attrs[field_name] = [attr_class(v) for v in raw_value]
                            else:
                                # Single value - let Pydantic handle conversion
                                player_attrs[field_name] = raw_value
                        else:
                            # For list fields (has_explicit_card), default to empty list
                            # For other optional fields, explicitly set to None
                            if attr_info.flags.has_explicit_card:
                                player_attrs[field_name] = []
                            else:
                                player_attrs[field_name] = None

                    # Create entity instance and assign to role
                    if any(v is not None for v in player_attrs.values()):
                        player_entity = entity_class(**player_attrs)
                        setattr(relation, role_name, player_entity)

            relations.append(relation)

        return relations

    def first(self) -> R | None:
        """Get first matching relation.

        Returns:
            First relation or None
        """
        results = self.limit(1).execute()
        return results[0] if results else None

    def count(self) -> int:
        """Count matching relations.

        Returns:
            Number of matching relations
        """
        return len(self.execute())

    def delete(self) -> int:
        """Delete all relations matching the current filters.

        Builds and executes a delete query based on the current filter state.
        Uses a single transaction for atomic deletion.

        Returns:
            Number of relations deleted

        Example:
            # Delete all high-salary employments
            count = Employment.manager(db).filter(Salary.gt(Salary(150000))).delete()
            print(f"Deleted {count} employments")

            # Delete with multiple filters
            count = Employment.manager(db).filter(
                Position.eq(Position("Intern")),
                Salary.lt(Salary(30000))
            ).delete()
        """

        # Get all attributes (including inherited)
        all_attrs = self.model_class.get_all_attributes()

        # Separate attribute filters from role player filters
        attr_filters = {}
        role_player_filters = {}

        for key, value in self.filters.items():
            if key in self.model_class._roles:
                # This is a role player filter
                role_player_filters[key] = value
            elif key in all_attrs:
                # This is an attribute filter
                attr_filters[key] = value
            else:
                raise ValueError(f"Unknown filter: {key}")

        # Build match clause with role players
        query = Query()
        role_parts = []
        role_info = {}  # role_name -> (var, entity_class)
        for role_name, role in self.model_class._roles.items():
            role_var = f"${role_name}"
            role_parts.append(f"{role.role_name}: {role_var}")
            role_info[role_name] = (role_var, role.player_entity_type)

        roles_str = ", ".join(role_parts)

        # Build relation match with inline attribute filters
        relation_parts = [f"$r isa {self.model_class.get_type_name()} ({roles_str})"]

        # Add dict-based attribute filters
        for field_name, value in attr_filters.items():
            attr_info = all_attrs[field_name]
            attr_name = attr_info.typ.get_attribute_name()
            formatted_value = format_value(value)
            relation_parts.append(f"has {attr_name} {formatted_value}")

        # Combine relation and attribute filters with commas
        pattern = ", ".join(relation_parts)
        query.match(pattern)

        # Add role player filter clauses
        for role_name, player_entity in role_player_filters.items():
            role_var = f"${role_name}"
            entity_class = role_info[role_name][1]

            # Match the role player by their key attributes (including inherited)
            player_owned_attrs = entity_class.get_all_attributes()
            for field_name, attr_info in player_owned_attrs.items():
                if attr_info.flags.is_key:
                    key_value = getattr(player_entity, field_name, None)
                    if key_value is not None:
                        attr_name = attr_info.typ.get_attribute_name()
                        # Extract value from Attribute instance if needed
                        if hasattr(key_value, "value"):
                            key_value = key_value.value
                        formatted_value = format_value(key_value)
                        query.match(f"{role_var} has {attr_name} {formatted_value}")
                        break

        # Add expression-based filters
        for expr in self._expressions:
            expr_pattern = expr.to_typeql("$r")
            query.match(expr_pattern)

        # Add delete clause
        query.delete("$r")

        # Execute in single transaction
        with self.db.transaction("write") as tx:
            results = tx.execute(query.build())
            tx.commit()

        return len(results) if results else 0

    def update_with(self, func: Any) -> list[R]:
        """Update relations by applying a function to each matching relation.

        Fetches all matching relations, applies the provided function to each one,
        then saves all updates in a single transaction. If the function raises an
        error on any relation, stops immediately and raises the error.

        Args:
            func: Callable that takes a relation and modifies it in-place.
                  Can be a lambda or regular function.

        Returns:
            List of updated relations

        Example:
            # Increase salary for all engineers by 10%
            updated = Employment.manager(db).filter(
                Position.eq(Position("Engineer"))
            ).update_with(
                lambda emp: setattr(emp, 'salary', Salary(int(emp.salary.value * 1.1)))
            )

            # Complex update with function
            def promote(employment):
                employment.position = Position("Senior " + employment.position.value)
                if employment.salary:
                    employment.salary = Salary(int(employment.salary.value * 1.2))

            promoted = Employment.manager(db).filter(
                Position.contains(Position("Engineer"))
            ).update_with(promote)

        Raises:
            Any exception raised by the function during processing
        """
        # Fetch all matching relations
        relations = self.execute()

        # Return empty list if no matches
        if not relations:
            return []

        # Store original attribute values before applying function
        # This is needed to match the relation uniquely in the update query
        owned_attrs = self.model_class.get_all_attributes()
        original_values = []

        for relation in relations:
            original = {}
            for field_name, attr_info in owned_attrs.items():
                current_value = getattr(relation, field_name, None)
                # Store the original value (before function modifies it)
                original[field_name] = current_value
            original_values.append(original)

        # Apply function to each relation (stop and raise if error)
        for relation in relations:
            func(relation)

        # Update all relations in a single transaction
        with self.db.transaction("write") as tx:
            for relation, original in zip(relations, original_values):
                # Build update query for this relation using original values for matching
                query_str = self._build_update_query(relation, original)
                tx.execute(query_str)
            tx.commit()

        return relations

    def _build_update_query(self, relation: R, original_values: dict[str, Any]) -> str:
        """Build update query for a single relation.

        Args:
            relation: Relation instance with NEW values to update to
            original_values: Dict of field_name -> original value (for matching)

        Returns:
            TypeQL update query string
        """
        # Get all attributes (including inherited) to determine cardinality
        owned_attrs = self.model_class.get_all_attributes()

        # Extract role players from relation for matching
        role_players = {}
        roles = self.model_class._roles

        for role_name in roles:
            entity = getattr(relation, role_name, None)
            if entity is None:
                msg = f"Role '{role_name}' is required for update"
                raise ValueError(msg)
            role_players[role_name] = entity

        # Separate single-value and multi-value updates from NEW values
        single_value_updates = {}
        multi_value_updates = {}

        # Also separate original values for matching
        original_single_values = {}
        original_multi_values = {}

        for field_name, attr_info in owned_attrs.items():
            attr_class = attr_info.typ
            attr_name = attr_class.get_attribute_name()
            flags = attr_info.flags

            # Get NEW value from relation
            new_value = getattr(relation, field_name, None)

            # Get ORIGINAL value for matching
            orig_value = original_values.get(field_name)

            # Extract raw values from Attribute instances (for NEW values)
            if new_value is not None:
                if isinstance(new_value, list):
                    raw_values = []
                    for item in new_value:
                        if hasattr(item, "value"):
                            raw_values.append(item.value)
                        else:
                            raw_values.append(item)
                    new_value = raw_values
                elif hasattr(new_value, "value"):
                    new_value = new_value.value

            # Extract raw values from Attribute instances (for ORIGINAL values)
            if orig_value is not None:
                if isinstance(orig_value, list):
                    raw_orig_values = []
                    for item in orig_value:
                        if hasattr(item, "value"):
                            raw_orig_values.append(item.value)
                        else:
                            raw_orig_values.append(item)
                    orig_value = raw_orig_values
                elif hasattr(orig_value, "value"):
                    orig_value = orig_value.value

            # Determine if multi-value
            if is_multi_value_attribute(flags):
                # Multi-value: store as list (even if empty)
                if new_value is None:
                    new_value = []
                multi_value_updates[attr_name] = new_value
                if orig_value is None:
                    orig_value = []
                original_multi_values[attr_name] = orig_value
            else:
                # Single-value: skip None values for optional attributes
                if new_value is not None:
                    single_value_updates[attr_name] = new_value
                if orig_value is not None:
                    original_single_values[attr_name] = orig_value

        # Build match clause with role players
        role_parts = []
        match_statements = []

        for role_name, entity in role_players.items():
            role_var = f"${role_name}"
            role = roles[role_name]
            role_parts.append(f"{role.role_name}: {role_var}")

            # Match the role player by their key attributes (including inherited)
            entity_class = entity.__class__
            player_owned_attrs = entity_class.get_all_attributes()
            for field_name, attr_info in player_owned_attrs.items():
                if attr_info.flags.is_key:
                    key_value = getattr(entity, field_name, None)
                    if key_value is not None:
                        attr_name = attr_info.typ.get_attribute_name()
                        # Extract value from Attribute instance if needed
                        if hasattr(key_value, "value"):
                            key_value = key_value.value
                        formatted_value = format_value(key_value)
                        match_statements.append(f"{role_var} has {attr_name} {formatted_value};")
                        break

        roles_str = ", ".join(role_parts)
        relation_match_parts = [f"$r isa {self.model_class.get_type_name()} ({roles_str})"]

        # IMPORTANT: Match by ORIGINAL attribute values to uniquely identify the relation
        # This is crucial because multiple relations can have same role players
        for attr_name, orig_value in original_single_values.items():
            formatted_value = format_value(orig_value)
            relation_match_parts.append(f"has {attr_name} {formatted_value}")

        relation_match = ", ".join(relation_match_parts) + ";"
        match_statements.insert(0, relation_match)

        # Add match statements to bind multi-value attributes for deletion
        if multi_value_updates:
            for attr_name in multi_value_updates:
                match_statements.append(f"$r has {attr_name} ${attr_name};")

        match_clause = "\n".join(match_statements)

        # Build query parts
        query_parts = [f"match\n{match_clause}"]

        # Delete clause (for multi-value attributes)
        if multi_value_updates:
            delete_parts = []
            for attr_name in multi_value_updates:
                delete_parts.append(f"${attr_name} of $r;")
            delete_clause = "\n".join(delete_parts)
            query_parts.append(f"delete\n{delete_clause}")

        # Insert clause (for multi-value attributes)
        if multi_value_updates:
            insert_parts = []
            for attr_name, values in multi_value_updates.items():
                for value in values:
                    formatted_value = format_value(value)
                    insert_parts.append(f"$r has {attr_name} {formatted_value};")
            if insert_parts:
                insert_clause = "\n".join(insert_parts)
                query_parts.append(f"insert\n{insert_clause}")

        # Update clause (for single-value attributes)
        if single_value_updates:
            update_parts = []
            for attr_name, value in single_value_updates.items():
                formatted_value = format_value(value)
                update_parts.append(f"$r has {attr_name} {formatted_value};")
            update_clause = "\n".join(update_parts)
            query_parts.append(f"update\n{update_clause}")

        # Combine and return
        return "\n".join(query_parts)

    def aggregate(self, *aggregates: Any) -> dict[str, Any]:
        """Execute aggregation queries.

        Performs database-side aggregations for efficiency.

        Args:
            *aggregates: AggregateExpr objects (Employment.salary.avg(), etc.)

        Returns:
            Dictionary mapping aggregate keys to results

        Examples:
            # Single aggregation
            result = manager.filter().aggregate(Employment.salary.avg())
            avg_salary = result['avg_salary']

            # Multiple aggregations
            result = manager.filter(Employment.position.eq(Position("Engineer"))).aggregate(
                Employment.salary.avg(),
                Employment.salary.sum(),
                Employment.salary.max()
            )
            avg_salary = result['avg_salary']
            total_salary = result['sum_salary']
            max_salary = result['max_salary']
        """
        from type_bridge.expressions import AggregateExpr

        if not aggregates:
            raise ValueError("At least one aggregation expression required")

        # Get all attributes (including inherited)
        all_attrs = self.model_class.get_all_attributes()

        # Separate attribute filters from role player filters
        attr_filters = {}
        role_player_filters = {}

        for key, value in self.filters.items():
            if key in self.model_class._roles:
                role_player_filters[key] = value
            elif key in all_attrs:
                attr_filters[key] = value
            else:
                raise ValueError(f"Unknown filter: {key}")

        # Build base match clause
        role_parts = []
        role_info = {}
        for role_name, role in self.model_class._roles.items():
            role_var = f"${role_name}"
            role_parts.append(f"{role.role_name}: {role_var}")
            role_info[role_name] = (role_var, role.player_entity_type)

        roles_str = ", ".join(role_parts)
        match_clauses = [f"$r isa {self.model_class.get_type_name()} ({roles_str})"]

        # Add dict-based attribute filters
        for field_name, value in attr_filters.items():
            attr_info = all_attrs[field_name]
            attr_name = attr_info.typ.get_attribute_name()
            formatted_value = format_value(value)
            match_clauses.append(f"$r has {attr_name} {formatted_value}")

        # Add role player filter clauses
        for role_name, player_entity in role_player_filters.items():
            role_var = f"${role_name}"
            entity_class = role_info[role_name][1]

            player_owned_attrs = entity_class.get_all_attributes()
            for field_name, attr_info in player_owned_attrs.items():
                if attr_info.flags.is_key:
                    key_value = getattr(player_entity, field_name, None)
                    if key_value is not None:
                        attr_name = attr_info.typ.get_attribute_name()
                        if hasattr(key_value, "value"):
                            key_value = key_value.value
                        formatted_value = format_value(key_value)
                        match_clauses.append(f"{role_var} has {attr_name} {formatted_value}")
                        break

        # Apply expression-based filters
        for expr in self._expressions:
            pattern = expr.to_typeql("$r")
            match_clauses.append(pattern)

        match_clause = ";\n".join(match_clauses) + ";"

        # Build reduce query with aggregations
        reduce_clauses = []
        for agg in aggregates:
            if not isinstance(agg, AggregateExpr):
                raise TypeError(f"Expected AggregateExpr, got {type(agg).__name__}")

            # If this aggregation is on a specific attr_type (not count), add binding pattern
            if agg.attr_type is not None:
                attr_name = agg.attr_type.get_attribute_name()
                attr_var = f"${attr_name.lower()}"
                match_clause = match_clause.rstrip(";")
                match_clause += f";\n$r has {attr_name} {attr_var};"

            # Generate reduce clause: $result_var = function($var)
            result_var = f"${agg.get_fetch_key()}"
            reduce_clauses.append(f"{result_var} = {agg.to_typeql('$r')}")

        # Convert match to reduce query
        reduce_query = f"match\n{match_clause}\nreduce {', '.join(reduce_clauses)};"

        with self.db.transaction("read") as tx:
            results = tx.execute(reduce_query)

        # Parse aggregation results
        if not results:
            return {}

        result = results[0] if results else {}

        # TypeDB reduce returns results as a formatted string in 'result' key
        import re

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

    def group_by(self, *fields: Any) -> "RelationGroupByQuery[R]":
        """Group relations by field values.

        Args:
            *fields: FieldRef objects to group by

        Returns:
            RelationGroupByQuery for chained aggregations

        Example:
            result = manager.group_by(Employment.position).aggregate(Employment.salary.avg())
        """
        # Import here to avoid circular dependency
        from .group_by import RelationGroupByQuery

        return RelationGroupByQuery(
            self.db, self.model_class, self.filters, self._expressions, fields
        )

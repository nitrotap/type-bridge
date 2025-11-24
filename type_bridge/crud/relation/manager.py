"""RelationManager for relation CRUD operations."""

from typing import TYPE_CHECKING, Any

from type_bridge.models import Relation
from type_bridge.query import Query
from type_bridge.session import Database

from ..base import R
from ..utils import format_value, is_multi_value_attribute

if TYPE_CHECKING:
    from .group_by import RelationGroupByQuery
    from .query import RelationQuery


class RelationManager[R: Relation]:
    """Manager for relation CRUD operations.

    Type-safe manager that preserves relation type information.
    """

    def __init__(self, db: Database, model_class: type[R]):
        """Initialize relation manager.

        Args:
            db: Database connection
            model_class: Relation model class
        """
        self.db = db
        self.model_class = model_class

    def insert(self, relation: R) -> R:
        """Insert a typed relation instance into the database.

        Args:
            relation: Typed relation instance with role players and attributes

        Returns:
            The inserted relation instance

        Example:
            # Typed construction - full IDE support and type checking
            employment = Employment(
                employee=person,
                employer=company,
                position="Engineer",
                salary=100000
            )
            employment_manager.insert(employment)
        """
        # Extract role players from relation instance
        roles = self.model_class._roles
        role_players = {}
        for role_name, role in roles.items():
            entity = relation.__dict__.get(role_name)
            if entity is not None:
                role_players[role_name] = entity

        # Build match clause for role players
        match_parts = []
        for role_name, entity in role_players.items():
            # Get key attributes from the entity (including inherited attributes)
            entity_type_name = entity.__class__.get_type_name()
            key_attrs = {
                field_name: attr_info
                for field_name, attr_info in entity.__class__.get_all_attributes().items()
                if attr_info.flags.is_key
            }

            # Match entity by its key attribute
            for field_name, attr_info in key_attrs.items():
                value = getattr(entity, field_name)
                attr_class = attr_info.typ
                attr_name = attr_class.get_attribute_name()
                formatted_value = format_value(value)
                match_parts.append(
                    f"${role_name} isa {entity_type_name}, has {attr_name} {formatted_value}"
                )
                break  # Only use first key attribute

        # Build insert clause
        relation_type_name = self.model_class.get_type_name()
        role_parts = [
            f"{roles[role_name].role_name}: ${role_name}" for role_name in role_players.keys()
        ]
        relation_pattern = f"({', '.join(role_parts)}) isa {relation_type_name}"

        # Add attributes (including inherited)
        attr_parts = []
        for field_name, attr_info in self.model_class.get_all_attributes().items():
            value = getattr(relation, field_name, None)
            if value is not None:
                attr_class = attr_info.typ
                attr_name = attr_class.get_attribute_name()

                # Handle lists (multi-value attributes)
                if isinstance(value, list):
                    for item in value:
                        # Extract value from Attribute instance
                        if hasattr(item, "value"):
                            item = item.value
                        # Use format_value to ensure proper escaping
                        formatted = format_value(item)
                        attr_parts.append(f"has {attr_name} {formatted}")
                else:
                    # Extract value from Attribute instance
                    if hasattr(value, "value"):
                        value = value.value
                    # Use format_value to ensure proper escaping
                    formatted = format_value(value)
                    attr_parts.append(f"has {attr_name} {formatted}")

        # Combine relation pattern with attributes
        if attr_parts:
            insert_pattern = relation_pattern + ", " + ", ".join(attr_parts)
        else:
            insert_pattern = relation_pattern

        # Build full query
        match_clause = "match\n" + ";\n".join(match_parts) + ";"
        insert_clause = "insert\n" + insert_pattern + ";"
        query = match_clause + "\n" + insert_clause

        with self.db.transaction("write") as tx:
            tx.execute(query)
            tx.commit()

        return relation

    def insert_many(self, relations: list[R]) -> list[R]:
        """Insert multiple relations into the database in a single transaction.

        More efficient than calling insert() multiple times.

        Args:
            relations: List of relation instances to insert

        Returns:
            List of inserted relation instances

        Example:
            employments = [
                Employment(
                    position="Engineer",
                    salary=100000,
                    employee=alice,
                    employer=tech_corp
                ),
                Employment(
                    position="Manager",
                    salary=120000,
                    employee=bob,
                    employer=tech_corp
                ),
            ]
            Employment.manager(db).insert_many(employments)
        """
        if not relations:
            return []

        # Build query
        query = Query()

        # Collect all unique role players to match
        all_players = {}  # key: (entity_type, key_attr_values) -> player_var
        player_counter = 0

        # First pass: collect all unique players from all relation instances
        for relation in relations:
            # Extract role players from instance
            for role_name, role in self.model_class._roles.items():
                player_entity = relation.__dict__.get(role_name)
                if player_entity is None:
                    continue
                # Create unique key for this player based on key attributes (including inherited)
                player_type = player_entity.get_type_name()
                owned_attrs = player_entity.get_all_attributes()

                key_values = []
                for field_name, attr_info in owned_attrs.items():
                    if attr_info.flags.is_key:
                        value = getattr(player_entity, field_name, None)
                        if value is not None:
                            attr_name = attr_info.typ.get_attribute_name()
                            key_values.append((attr_name, value))

                player_key = (player_type, tuple(sorted(key_values)))

                if player_key not in all_players:
                    player_var = f"$player{player_counter}"
                    player_counter += 1
                    all_players[player_key] = player_var

                    # Build match clause for this player
                    match_parts = [f"{player_var} isa {player_type}"]
                    for attr_name, value in key_values:
                        formatted_value = format_value(value)
                        match_parts.append(f"has {attr_name} {formatted_value}")

                    query.match(", ".join(match_parts))

        # Second pass: build insert patterns for relations
        insert_patterns = []

        for i, relation in enumerate(relations):
            # Map role players to their variables
            role_var_map = {}
            for role_name, role in self.model_class._roles.items():
                player_entity = relation.__dict__.get(role_name)
                if player_entity is None:
                    raise ValueError(f"Missing role player for role: {role_name}")

                # Find the player variable (including inherited attributes)
                player_type = player_entity.get_type_name()
                owned_attrs = player_entity.get_all_attributes()

                key_values = []
                for field_name, attr_info in owned_attrs.items():
                    if attr_info.flags.is_key:
                        value = getattr(player_entity, field_name, None)
                        if value is not None:
                            attr_name = attr_info.typ.get_attribute_name()
                            key_values.append((attr_name, value))

                player_key = (player_type, tuple(sorted(key_values)))
                player_var = all_players[player_key]
                role_var_map[role_name] = (player_var, role.role_name)

            # Build insert pattern for this relation
            role_players_str = ", ".join(
                [f"{role_name}: {var}" for var, role_name in role_var_map.values()]
            )
            insert_pattern = f"({role_players_str}) isa {self.model_class.get_type_name()}"

            # Extract and add attributes from relation instance (including inherited)
            attr_parts = []
            all_attrs = self.model_class.get_all_attributes()
            for field_name, attr_info in all_attrs.items():
                if hasattr(relation, field_name):
                    attr_value = getattr(relation, field_name)
                    if attr_value is None:
                        continue

                    typeql_attr_name = attr_info.typ.get_attribute_name()

                    # Handle multi-value attributes (lists)
                    if isinstance(attr_value, list):
                        # Extract raw values from each Attribute instance in the list
                        for item in attr_value:
                            if hasattr(item, "value"):
                                raw_value = item.value
                            else:
                                raw_value = item
                            formatted_value = format_value(raw_value)
                            attr_parts.append(f"has {typeql_attr_name} {formatted_value}")
                    else:
                        # Single-value attribute - extract raw value from Attribute instance
                        if hasattr(attr_value, "value"):
                            attr_value = attr_value.value
                        formatted_value = format_value(attr_value)
                        attr_parts.append(f"has {typeql_attr_name} {formatted_value}")

            if attr_parts:
                insert_pattern += ", " + ", ".join(attr_parts)

            insert_patterns.append(insert_pattern)

        # Add all insert patterns to query
        query.insert(";\n".join(insert_patterns))

        # Execute the query
        query_str = query.build()
        with self.db.transaction("write") as tx:
            tx.execute(query_str)
            tx.commit()

        return relations

    def get(self, **filters) -> list[R]:
        """Get relations matching filters.

        Supports filtering by both attributes and role players.

        Args:
            filters: Attribute filters and/or role player filters
                - Attribute filters: position="Engineer", salary=100000, is_remote=True
                - Role player filters: employee=person_entity, employer=company_entity

        Returns:
            List of matching relations

        Example:
            # Filter by attribute
            Employment.manager(db).get(position="Engineer")

            # Filter by role player
            Employment.manager(db).get(employee=alice)

            # Filter by both
            Employment.manager(db).get(position="Manager", employer=tech_corp)
        """
        # Build TypeQL 3.x query with correct syntax for fetching relations with role players
        # Use get_all_attributes to include inherited attributes for filtering
        all_attrs = self.model_class.get_all_attributes()

        # Separate attribute filters from role player filters
        attr_filters = {}
        role_player_filters = {}

        for key, value in filters.items():
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

        # Add attribute filter clauses
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
        fetch_str = f"fetch {{\n  {fetch_body}\n}};"

        query_str = f"match\n{match_str}\n{fetch_str}"

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

    def all(self) -> list[R]:
        """Get all relations of this type.

        Syntactic sugar for get() with no filters.

        Returns:
            List of all relations

        Example:
            all_employments = Employment.manager(db).all()
        """
        return self.get()

    def update(self, relation: R) -> R:
        """Update a relation in the database based on its current state.

        Uses role players to identify the relation, then updates its attributes.
        Role players themselves cannot be changed (that would be a different relation).

        For single-value attributes (@card(0..1) or @card(1..1)), uses TypeQL update clause.
        For multi-value attributes (e.g., @card(0..5), @card(2..)), deletes old values
        and inserts new ones.

        Args:
            relation: The relation instance to update (must have all role players set)

        Returns:
            The same relation instance

        Example:
            # Fetch relation
            emp = employment_manager.get(employee=alice)[0]

            # Modify attributes
            emp.position = Position("Senior Engineer")
            emp.salary = Salary(120000)

            # Update in database
            employment_manager.update(emp)
        """
        # Get all attributes (including inherited)
        all_attrs = self.model_class.get_all_attributes()

        # Extract role players from relation instance for matching
        roles = self.model_class._roles
        role_players = {}
        for role_name, role in roles.items():
            entity = relation.__dict__.get(role_name)
            if entity is None:
                raise ValueError(f"Role player '{role_name}' is required for update")
            role_players[role_name] = entity

        # Separate single-value and multi-value updates from relation state
        single_value_updates = {}
        single_value_deletes = set()  # Track single-value attributes to delete
        multi_value_updates = {}

        for field_name, attr_info in all_attrs.items():
            attr_class = attr_info.typ
            attr_name = attr_class.get_attribute_name()
            flags = attr_info.flags

            # Get current value from relation
            current_value = getattr(relation, field_name, None)

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
            if is_multi_value_attribute(flags):
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
        relation_match = f"$r isa {self.model_class.get_type_name()} ({roles_str});"
        match_statements.insert(0, relation_match)

        # Add match statements to bind multi-value attributes for deletion
        if multi_value_updates:
            for attr_name in multi_value_updates:
                match_statements.append(f"$r has {attr_name} ${attr_name};")

        # Add match statements to bind single-value attributes for deletion
        if single_value_deletes:
            for attr_name in single_value_deletes:
                match_statements.append(f"$r has {attr_name} ${attr_name};")

        match_clause = "\n".join(match_statements)

        # Build query parts
        query_parts = [f"match\n{match_clause}"]

        # Delete clause (for multi-value and single-value deletions)
        delete_parts = []
        if multi_value_updates:
            for attr_name in multi_value_updates:
                delete_parts.append(f"${attr_name} of $r;")
        if single_value_deletes:
            for attr_name in single_value_deletes:
                delete_parts.append(f"${attr_name} of $r;")
        if delete_parts:
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

        # Combine and execute
        full_query = "\n".join(query_parts)

        with self.db.transaction("write") as tx:
            tx.execute(full_query)
            tx.commit()

        return relation

    def delete(self, **filters) -> int:
        """Delete relations matching filters.

        Supports filtering by both attributes and role players to identify relations to delete.

        Args:
            **filters: Attribute and/or role player filters
                - Attribute filters: position="Engineer", salary=100000
                - Role player filters: employee=person_entity, employer=company_entity

        Returns:
            Number of relations deleted

        Example:
            # Delete by role players
            manager.delete(employee=alice, employer=techcorp)

            # Delete by attribute
            manager.delete(position="Intern")

            # Delete by both
            manager.delete(employee=alice, position="Engineer")
        """
        # Get all attributes (including inherited) for validation
        all_attrs = self.model_class.get_all_attributes()

        # Separate attribute filters from role player filters
        attr_filters = {}
        role_player_filters = {}

        for key, value in filters.items():
            if key in self.model_class._roles:
                # This is a role player filter
                role_player_filters[key] = value
            elif key in all_attrs:
                # This is an attribute filter
                attr_filters[key] = value
            else:
                raise ValueError(f"Unknown filter: {key}")

        # Build match clause with role players and filters
        role_parts = []
        role_info = {}  # role_name -> (var, entity_class)
        for role_name, role in self.model_class._roles.items():
            role_var = f"${role_name}"
            role_parts.append(f"{role.role_name}: {role_var}")
            role_info[role_name] = (role_var, role.player_entity_type)

        roles_str = ", ".join(role_parts)

        # Build relation match with inline attribute filters
        relation_parts = [f"$r isa {self.model_class.get_type_name()} ({roles_str})"]

        # Add attribute filters inline using commas
        for field_name, value in attr_filters.items():
            attr_info = all_attrs[field_name]
            attr_name = attr_info.typ.get_attribute_name()
            formatted_value = format_value(value)
            relation_parts.append(f"has {attr_name} {formatted_value}")

        # Combine relation and attribute filters with commas
        relation_match = ", ".join(relation_parts)
        match_statements = [relation_match]

        # Add role player filter clauses (without semicolons inside)
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
                        match_statements.append(f"{role_var} has {attr_name} {formatted_value}")
                        break

        # Build query
        query = Query()
        # Join statements with semicolons, Query class adds final semicolon
        pattern = ";\n".join(match_statements) if match_statements else ""
        query.match(pattern)
        query.delete("$r")

        with self.db.transaction("write") as tx:
            results = tx.execute(query.build())
            tx.commit()

        return len(results) if results else 0

    def filter(self, *expressions: Any, **filters: Any) -> "RelationQuery[R]":
        """Create a query for filtering relations.

        Supports both expression-based and dictionary-based filtering.

        Args:
            *expressions: Expression objects (Age.gt(Age(30)), etc.)
            **filters: Attribute and role player filters (exact match)
                - Attribute filters: position="Engineer", salary=100000
                - Role player filters: employee=person_entity, employer=company_entity

        Returns:
            RelationQuery for chaining

        Examples:
            # Expression-based (advanced filtering)
            manager.filter(Salary.gt(Salary(100000)))
            manager.filter(Salary.gt(Salary(50000)), Salary.lt(Salary(150000)))

            # Dictionary-based (exact match)
            manager.filter(position="Engineer", employee=alice)

            # Mixed
            manager.filter(Salary.gt(Salary(80000)), position="Engineer")

        Raises:
            ValueError: If expression references attribute type not owned by relation
        """
        # Import here to avoid circular dependency
        from .query import RelationQuery

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

        query = RelationQuery(self.db, self.model_class, filters if filters else None)
        if expressions:
            query._expressions.extend(expressions)
        return query

    def group_by(self, *fields: Any) -> "RelationGroupByQuery[R]":
        """Create a group-by query for aggregating by field values.

        Args:
            *fields: Field references to group by (Employment.position, etc.)

        Returns:
            RelationGroupByQuery for aggregation

        Example:
            # Group by single field
            result = manager.group_by(Employment.position).aggregate(Employment.salary.avg())

            # Group by multiple fields
            result = manager.group_by(Employment.position, Employment.department).aggregate(
                Employment.salary.avg()
            )
        """
        # Import here to avoid circular dependency
        from .group_by import RelationGroupByQuery

        return RelationGroupByQuery(self.db, self.model_class, {}, [], fields)

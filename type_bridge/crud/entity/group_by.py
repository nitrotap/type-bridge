"""Grouped aggregation queries for entities."""

import re
from typing import Any

from typedb.driver import TransactionType

from type_bridge.models import Entity
from type_bridge.query import QueryBuilder
from type_bridge.session import Database, Transaction


class GroupByQuery[E: Entity]:
    """Query for grouped aggregations.

    Allows grouping entities by field values and computing aggregations per group.
    """

    def __init__(
        self,
        db: Database,
        model_class: type[E],
        filters: dict[str, Any],
        expressions: list[Any],
        group_fields: tuple[Any, ...],
        transaction: Transaction | None = None,
    ):
        """Initialize grouped query.

        Args:
            db: Database connection
            model_class: Entity model class
            filters: Dict-based filters
            expressions: Expression-based filters
            group_fields: Fields to group by
        """
        self.db = db
        self.model_class = model_class
        self.filters = filters
        self._expressions = expressions
        self.group_fields = group_fields
        self.transaction = transaction

    def aggregate(self, *aggregates: Any) -> dict[Any, dict[str, Any]]:
        """Execute grouped aggregation.

        Args:
            *aggregates: AggregateExpr objects

        Returns:
            Dictionary mapping group values to aggregation results

        Example:
            # Group by city, compute average age per city
            result = manager.group_by(Person.city).aggregate(Person.age.avg())
            # Returns: {
            #   "NYC": {"avg_age": 35.5},
            #   "LA": {"avg_age": 28.3}
            # }
        """
        from type_bridge.expressions import AggregateExpr

        if not aggregates:
            raise ValueError("At least one aggregation expression required")

        # Build base match query
        query = QueryBuilder.match_entity(self.model_class, **self.filters)

        # Apply expression filters
        for expr in self._expressions:
            pattern = expr.to_typeql("$e")
            query.match(pattern)

        # Add group-by fields to match
        group_vars = []
        for i, field in enumerate(self.group_fields):
            var_name = f"$group{i}"
            attr_name = field.attr_type.get_attribute_name()
            query.match(f"$e has {attr_name} {var_name}")
            group_vars.append(var_name)

        # Build reduce query with group-by
        # First, bind all the fields being aggregated in the match clause
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

        # TypeQL 3.x group-by syntax:
        # match ... reduce $result = function($var) groupby $group_var;
        match_clause = query.build().replace("fetch", "get").split("fetch")[0]
        group_clause = ", ".join(group_vars)
        reduce_clause = ", ".join(reduce_clauses)
        reduce_query = f"{match_clause}\nreduce {reduce_clause} groupby {group_clause};"

        results = self._execute(reduce_query, TransactionType.READ)

        # Parse grouped results
        # TypeDB 3.x reduce with groupby returns formatted strings
        output = {}
        for result in results:
            # Result is a dict with 'result' key containing formatted string
            if "result" not in result:
                continue

            result_str = result["result"]

            # Parse both Value(...) and Attribute(...) formats
            # Value format: $var: Value(type: value)
            # Attribute format: $var: Attribute(type: "value")
            value_pattern = r"\$([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*Value\([^:]+:\s*([^)]+)\)"
            attr_pattern = r'\$([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*Attribute\([^:]+:\s*"([^"]+)"\)'

            value_matches = re.findall(value_pattern, result_str)
            attr_matches = re.findall(attr_pattern, result_str)

            # Combine all matches
            all_matches = [(name, val) for name, val in value_matches] + [
                (name, val) for name, val in attr_matches
            ]

            # Separate group keys from aggregation values
            group_keys = []
            group_aggs = {}

            for var_name, value_str in all_matches:
                # Convert value to appropriate type
                try:
                    if "." in value_str:
                        value = float(value_str)
                    else:
                        value = int(value_str)
                except ValueError:
                    value = value_str.strip().strip('"')

                # Check if this is a group variable
                is_group_var = False
                for group_var in group_vars:
                    if group_var.lstrip("$") == var_name:
                        group_keys.append(value)
                        is_group_var = True
                        break

                if not is_group_var:
                    # This is an aggregation result
                    group_aggs[var_name] = value

            # Create group key (single value or tuple)
            if len(group_keys) == 1:
                group_key = group_keys[0]
            else:
                group_key = tuple(group_keys)

            output[group_key] = group_aggs

        return output

    def _execute(self, query: str, tx_type: TransactionType) -> list[dict[str, Any]]:
        """Execute a query using an existing transaction if provided."""
        if self.transaction:
            return self.transaction.execute(query)

        with self.db.transaction(tx_type) as tx:
            return tx.execute(query)

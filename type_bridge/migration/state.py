"""Migration state tracking for TypeDB.

Tracks applied migrations in TypeDB as the sole source of truth.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from type_bridge.session import Database

logger = logging.getLogger(__name__)


@dataclass
class MigrationRecord:
    """Record of an applied migration."""

    app_label: str
    name: str
    applied_at: str  # ISO format datetime
    checksum: str  # Hash of migration content for change detection

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MigrationRecord):
            return NotImplemented
        return self.app_label == other.app_label and self.name == other.name


@dataclass
class MigrationState:
    """Complete state of applied migrations."""

    applied: list[MigrationRecord] = field(default_factory=list)
    version: str = "1.0"

    def is_applied(self, app_label: str, name: str) -> bool:
        """Check if a migration has been applied.

        Args:
            app_label: Application label
            name: Migration name

        Returns:
            True if migration has been applied
        """
        return any(r.app_label == app_label and r.name == name for r in self.applied)

    def add(self, record: MigrationRecord) -> None:
        """Add a migration record.

        Args:
            record: Migration record to add
        """
        if not self.is_applied(record.app_label, record.name):
            self.applied.append(record)

    def remove(self, app_label: str, name: str) -> None:
        """Remove a migration record (for rollback).

        Args:
            app_label: Application label
            name: Migration name
        """
        self.applied = [
            r for r in self.applied if not (r.app_label == app_label and r.name == name)
        ]

    def get_latest(self, app_label: str) -> MigrationRecord | None:
        """Get the most recently applied migration for an app.

        Args:
            app_label: Application label

        Returns:
            Most recent migration record, or None
        """
        app_migrations = [r for r in self.applied if r.app_label == app_label]
        return app_migrations[-1] if app_migrations else None

    def get_all_for_app(self, app_label: str) -> list[MigrationRecord]:
        """Get all applied migrations for an app.

        Args:
            app_label: Application label

        Returns:
            List of migration records in application order
        """
        return [r for r in self.applied if r.app_label == app_label]


class MigrationStateManager:
    """Manages migration state in TypeDB.

    State is stored in TypeDB as type_bridge_migration entities.

    Example:
        manager = MigrationStateManager(db)
        state = manager.load_state()

        if not state.is_applied("myapp", "0001_initial"):
            # Apply migration...
            manager.record_applied("myapp", "0001_initial", "abc123")
    """

    ENTITY_NAME = "type_bridge_migration"

    def __init__(self, db: Database):
        """Initialize state manager.

        Args:
            db: Database connection
        """
        self.db = db
        self._state: MigrationState | None = None
        self._schema_ensured = False

    def ensure_schema(self) -> None:
        """Ensure migration tracking schema exists in TypeDB.

        Creates the type_bridge_migration entity type if it doesn't exist.
        """
        if self._schema_ensured:
            return

        # Check if entity type exists
        check_query = f"""
            match $t type {self.ENTITY_NAME};
            fetch {{ "exists": true }};
        """

        try:
            with self.db.transaction("read") as tx:
                results = list(tx.execute(check_query))
                if results:
                    self._schema_ensured = True
                    return
        except Exception:
            # Type doesn't exist, will create it
            pass

        # Create migration tracking schema
        # Use composite key (app_label:name) since TypeDB 3.x @key requires unique ownership
        schema = f"""define
attribute migration_id, value string;
attribute migration_app_label, value string;
attribute migration_name, value string;
attribute migration_applied_at, value datetime;
attribute migration_checksum, value string;

entity {self.ENTITY_NAME},
    owns migration_id @key,
    owns migration_app_label,
    owns migration_name,
    owns migration_applied_at,
    owns migration_checksum;
"""

        logger.info("Creating migration tracking schema")
        with self.db.transaction("schema") as tx:
            tx.execute(schema)
            tx.commit()

        self._schema_ensured = True

    def load_state(self) -> MigrationState:
        """Load migration state from TypeDB.

        Returns:
            Current migration state
        """
        self.ensure_schema()

        query = f"""
match
$m isa {self.ENTITY_NAME},
    has migration_app_label $app,
    has migration_name $name,
    has migration_applied_at $applied,
    has migration_checksum $checksum;
fetch {{
    "app": $app,
    "name": $name,
    "applied": $applied,
    "checksum": $checksum
}};
"""

        state = MigrationState()

        try:
            with self.db.transaction("read") as tx:
                results = tx.execute(query)
                for result in results:
                    # Handle TypeDB result format
                    app = self._extract_value(result, "app")
                    name = self._extract_value(result, "name")
                    applied = self._extract_value(result, "applied")
                    checksum = self._extract_value(result, "checksum")

                    if all([app, name, applied, checksum]):
                        state.add(
                            MigrationRecord(
                                app_label=str(app),
                                name=str(name),
                                applied_at=str(applied),
                                checksum=str(checksum),
                            )
                        )
        except Exception as e:
            logger.warning(f"Failed to load migration state from TypeDB: {e}")

        self._state = state
        return state

    def _extract_value(self, result: dict, key: str) -> str | None:
        """Extract value from TypeDB fetch result.

        Args:
            result: Fetch result dictionary
            key: Key to extract

        Returns:
            Extracted value or None
        """
        value = result.get(key)
        if value is None:
            return None
        # Handle different result formats
        if isinstance(value, dict):
            return value.get("value")
        return str(value)

    def record_applied(self, app_label: str, name: str, checksum: str) -> None:
        """Record that a migration was applied.

        Args:
            app_label: Application label
            name: Migration name
            checksum: Migration content hash
        """
        self.ensure_schema()

        applied_at = datetime.now(UTC)
        applied_at_str = applied_at.strftime("%Y-%m-%dT%H:%M:%S.%f")

        migration_id = f"{app_label}:{name}"
        query = f"""
insert $m isa {self.ENTITY_NAME},
    has migration_id "{migration_id}",
    has migration_app_label "{app_label}",
    has migration_name "{name}",
    has migration_applied_at {applied_at_str},
    has migration_checksum "{checksum}";
"""

        with self.db.transaction("write") as tx:
            tx.execute(query)
            tx.commit()

        logger.info(f"Recorded migration: {app_label}.{name}")

        # Update local state
        if self._state:
            self._state.add(
                MigrationRecord(
                    app_label=app_label,
                    name=name,
                    applied_at=applied_at.isoformat(),
                    checksum=checksum,
                )
            )

    def record_unapplied(self, app_label: str, name: str) -> None:
        """Record that a migration was rolled back.

        Args:
            app_label: Application label
            name: Migration name
        """
        self.ensure_schema()

        query = f"""
match
$m isa {self.ENTITY_NAME},
    has migration_app_label "{app_label}",
    has migration_name "{name}";
delete $m isa {self.ENTITY_NAME};
"""

        with self.db.transaction("write") as tx:
            tx.execute(query)
            tx.commit()

        logger.info(f"Removed migration record: {app_label}.{name}")

        # Update local state
        if self._state:
            self._state.remove(app_label, name)

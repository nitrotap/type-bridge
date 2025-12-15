"""CLI for TypeBridge migrations.

Usage:
    python -m type_bridge.migration migrate                    # Apply all pending
    python -m type_bridge.migration migrate 0002_add_company   # Migrate to specific
    python -m type_bridge.migration showmigrations             # List status
    python -m type_bridge.migration sqlmigrate 0002_add_company        # Preview TypeQL
    python -m type_bridge.migration sqlmigrate 0002_add_company -r     # Preview rollback
    python -m type_bridge.migration makemigrations -n add_phone        # Generate migration
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from type_bridge.migration.executor import MigrationError, MigrationExecutor
from type_bridge.migration.generator import MigrationGenerator
from type_bridge.migration.registry import ModelRegistry
from type_bridge.session import Database

logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> int:
    """Main CLI entry point.

    Args:
        argv: Command line arguments (defaults to sys.argv)

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    parser = argparse.ArgumentParser(
        prog="python -m type_bridge.migration",
        description="TypeBridge database migration tool",
    )

    parser.add_argument(
        "--database",
        "-d",
        default="typedb",
        help="Database name (default: typedb)",
    )
    parser.add_argument(
        "--address",
        "-a",
        default="localhost:1729",
        help="TypeDB server address (default: localhost:1729)",
    )
    parser.add_argument(
        "--migrations-dir",
        "-m",
        type=Path,
        default=Path("migrations"),
        help="Migrations directory (default: ./migrations)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without executing",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose output",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # migrate command
    migrate_parser = subparsers.add_parser(
        "migrate",
        help="Apply migrations",
    )
    migrate_parser.add_argument(
        "target",
        nargs="?",
        help="Target migration name (default: apply all pending)",
    )

    # showmigrations command
    subparsers.add_parser(
        "showmigrations",
        help="List all migrations and their status",
    )

    # sqlmigrate command
    sql_parser = subparsers.add_parser(
        "sqlmigrate",
        help="Show TypeQL for a migration",
    )
    sql_parser.add_argument(
        "migration_name",
        help="Migration name to show",
    )
    sql_parser.add_argument(
        "--reverse",
        "-r",
        action="store_true",
        help="Show rollback TypeQL",
    )

    # makemigrations command
    make_parser = subparsers.add_parser(
        "makemigrations",
        help="Auto-generate migration from model changes",
    )
    make_parser.add_argument(
        "--name",
        "-n",
        default="auto",
        help="Migration name suffix",
    )
    make_parser.add_argument(
        "--empty",
        action="store_true",
        help="Create empty migration for manual editing",
    )
    make_parser.add_argument(
        "--models",
        "-M",
        type=str,
        help="Python path to models module (e.g., myapp.models)",
    )

    # plan command
    plan_parser = subparsers.add_parser(
        "plan",
        help="Show migration plan without executing",
    )
    plan_parser.add_argument(
        "target",
        nargs="?",
        help="Target migration name",
    )

    args = parser.parse_args(argv)

    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s",
    )

    try:
        # Connect to database
        db = Database(address=args.address, database=args.database)
        db.connect()

        result = _execute_command(db, args)

        db.close()
        return result

    except MigrationError as e:
        print(f"Migration error: {e}", file=sys.stderr)
        return 1
    except ConnectionError as e:
        print(f"Connection error: {e}", file=sys.stderr)
        print("Make sure TypeDB server is running and accessible.", file=sys.stderr)
        return 1
    except Exception as e:
        logger.exception("Unexpected error")
        print(f"Error: {e}", file=sys.stderr)
        return 1


def _execute_command(db: Database, args: argparse.Namespace) -> int:
    """Execute the specified command.

    Args:
        db: Database connection
        args: Parsed arguments

    Returns:
        Exit code
    """
    # Create executor
    executor = MigrationExecutor(
        db=db,
        migrations_dir=args.migrations_dir,
        dry_run=args.dry_run,
    )

    if args.command == "migrate":
        return _cmd_migrate(executor, args)
    elif args.command == "showmigrations":
        return _cmd_showmigrations(executor)
    elif args.command == "sqlmigrate":
        return _cmd_sqlmigrate(executor, args)
    elif args.command == "makemigrations":
        return _cmd_makemigrations(db, args)
    elif args.command == "plan":
        return _cmd_plan(executor, args)
    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return 1


def _cmd_migrate(executor: MigrationExecutor, args: argparse.Namespace) -> int:
    """Execute migrate command."""
    results = executor.migrate(target=args.target)

    if not results:
        print("No migrations to apply")
        return 0

    for result in results:
        status = "OK" if result.success else "FAILED"
        action = "Applied" if result.action == "applied" else "Rolled back"
        print(f"  {action}: {result.name} ... {status}")
        if result.error:
            print(f"    Error: {result.error}")

    success_count = sum(1 for r in results if r.success)
    print(f"\n{success_count}/{len(results)} migration(s) completed")

    return 0 if all(r.success for r in results) else 1


def _cmd_showmigrations(executor: MigrationExecutor) -> int:
    """Execute showmigrations command."""
    migrations = executor.showmigrations()

    if not migrations:
        print("No migrations found")
        return 0

    app_label = executor.migrations_dir.name
    print(app_label)

    for name, is_applied in migrations:
        status = "[X]" if is_applied else "[ ]"
        print(f" {status} {name}")

    return 0


def _cmd_sqlmigrate(executor: MigrationExecutor, args: argparse.Namespace) -> int:
    """Execute sqlmigrate command."""
    typeql = executor.sqlmigrate(
        args.migration_name,
        reverse=args.reverse,
    )
    print(typeql)
    return 0


def _cmd_makemigrations(db: Database, args: argparse.Namespace) -> int:
    """Execute makemigrations command."""
    generator = MigrationGenerator(db, args.migrations_dir)

    # Get models from specified source
    models: list = []

    if args.models:
        # Auto-discover models from specified module
        try:
            models = ModelRegistry.discover(args.models, register=False)
            print(f"Discovered {len(models)} model(s) from {args.models}")
        except ImportError as e:
            print(f"Error importing models module: {e}", file=sys.stderr)
            return 1
    else:
        # Use pre-registered models
        models = ModelRegistry.get_all()
        if models:
            print(f"Using {len(models)} registered model(s)")

    if not models and not args.empty:
        print(
            "No models found. Either:\n"
            "  1. Use --models to specify a module: makemigrations --models myapp.models\n"
            "  2. Register models with ModelRegistry.register() before running\n"
            "  3. Use --empty to create an empty migration for manual editing",
            file=sys.stderr,
        )
        return 1

    path = generator.generate(
        models=models,
        name=args.name,
        empty=args.empty,
    )

    if path:
        print(f"Created: {path}")
    else:
        print("No changes detected")

    return 0


def _cmd_plan(executor: MigrationExecutor, args: argparse.Namespace) -> int:
    """Execute plan command."""
    plan = executor.plan(target=args.target)

    if plan.is_empty():
        print("No migrations pending")
        return 0

    if plan.to_rollback:
        print("Rollback:")
        for loaded in plan.to_rollback:
            print(f"  - {loaded.migration.name}")

    if plan.to_apply:
        print("Apply:")
        for loaded in plan.to_apply:
            print(f"  + {loaded.migration.name}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

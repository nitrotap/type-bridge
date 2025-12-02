#!/usr/bin/env python3
"""Interactive CRUD Tutorial Runner.

This script runs through all 4 parts of the CRUD tutorial interactively:
1. crud_01_define.py - Schema Definition and Initial Data
2. crud_02_insert.py - Bulk Insertion
3. crud_03_read.py - Reading and Querying
4. crud_04_update.py - Updating Entities

Run this to learn TypeBridge CRUD operations step-by-step!
"""

import sys

from type_bridge import Database


def get_user_input(prompt: str, default: str) -> str:
    """Get user input with a default value."""
    user_input = input(f"{prompt} [{default}]: ").strip()
    return user_input if user_input else default


def wait_for_continue():
    """Wait for user to press Enter to continue."""
    input("\nPress Enter to continue to next part...")


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def run_part(part_number: int, script_name: str, description: str):
    """Run a tutorial part by importing and executing it."""
    print_section(f"Part {part_number}: {description}")
    print()
    print(f"Running: {script_name}")
    print()

    # Import and run the script
    module_name = script_name.replace(".py", "")
    try:
        # Import the module dynamically
        if module_name in sys.modules:
            # Reload if already imported
            import importlib

            module = importlib.reload(sys.modules[module_name])
        else:
            module = __import__(module_name)

        # Run the main function (guard against non-callable attributes)
        main_fn = getattr(module, "main", None)
        if callable(main_fn):
            main_fn()
        else:
            print(f"❌ Error: {script_name} doesn't have a callable main() function")
            return False

        return True
    except Exception as e:
        print(f"❌ Error running {script_name}: {e}")
        import traceback

        traceback.print_exc()
        return False


def check_database_exists(db: Database, should_exist: bool, part_name: str) -> bool:
    """Check if database exists (or doesn't exist) as expected."""
    exists = db.database_exists()

    if should_exist and not exists:
        print("\n❌ Error: Database doesn't exist!")
        print(f"   Part {part_name} requires the database to exist from previous parts.")
        print("   Please restart the tutorial or run the previous parts first.")
        return False

    if not should_exist and exists:
        print(f"\n⚠️  Warning: Database '{db.database_name}' already exists.")
        cleanup = get_user_input("Delete existing database before starting?", "y")
        if cleanup.lower() in ("y", "yes"):
            db.delete_database()
            print("  ✓ Database deleted")
        else:
            print("  Continuing with existing database (may cause conflicts)...")

    return True


def main():
    """Run the interactive CRUD tutorial."""
    print()
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "TypeBridge CRUD Tutorial" + " " * 34 + "║")
    print("║" + " " * 18 + "Interactive Step-by-Step Guide" + " " * 30 + "║")
    print("╚" + "═" * 78 + "╝")
    print()
    print("Welcome! This tutorial will guide you through all TypeBridge CRUD operations.")
    print()
    print("Tutorial Parts:")
    print("  1. Schema Definition Only (crud_01_define.py)")
    print("  2. All Data Insertion (crud_02_insert.py)")
    print("  3. Reading and Querying (crud_03_read.py)")
    print("  4. Updating Entities (crud_04_update.py)")
    print()

    # Get database configuration
    print("Database Configuration")
    print("-" * 80)
    address = get_user_input("TypeDB address", "localhost:1729")
    database_name = get_user_input("Database name", "crud_demo")
    print()

    # Test connection
    print(f"Testing connection to TypeDB at {address}...")
    db = Database(address=address, database=database_name)
    try:
        db.connect()
        print("✓ Connected successfully!")
        db.close()
    except Exception as e:
        print(f"❌ Error: Could not connect to TypeDB at {address}")
        print(f"   {e}")
        print()
        print("Please ensure TypeDB is running:")
        print("  docker run -d -p 1729:1729 --name typedb vaticle/typedb:latest")
        return

    print()

    # Ask user which parts to run
    start_from = get_user_input("Start from part (1-4)", "1")
    try:
        start_from = int(start_from)
        if start_from < 1 or start_from > 4:
            print("Invalid part number. Starting from Part 1.")
            start_from = 1
    except ValueError:
        print("Invalid input. Starting from Part 1.")
        start_from = 1

    print()
    print(f"Starting from Part {start_from}...")
    print()

    try:
        # Part 1: Schema Definition Only
        if start_from <= 1:
            print("\n" + "▶" * 40)
            print("Part 1/4: Schema Definition Only")
            print("▶" * 40)
            print()
            print("What you'll learn:")
            print("  • Defining attributes, entities, and relations")
            print("  • Creating a TypeDB database")
            print("  • Syncing schema with SchemaManager")
            print("  • Preparing database for data insertion")
            print()
            wait_for_continue()

            if not run_part(1, "crud_01_define", "Schema Definition Only"):
                return

            if start_from < 4:
                wait_for_continue()

        # Part 2: All Data Insertion
        if start_from <= 2:
            print("\n" + "▶" * 40)
            print("Part 2/4: All Data Insertion")
            print("▶" * 40)
            print()
            print("What you'll learn:")
            print("  • Inserting initial data (Alice, Bob, TechCorp)")
            print("  • Using insert_many() for efficient bulk operations")
            print("  • Inserting multiple entities in a single transaction")
            print("  • Populating the database with all tutorial data")
            print()
            wait_for_continue()

            if not run_part(2, "crud_02_insert", "All Data Insertion"):
                return

            if start_from < 4:
                wait_for_continue()

        # Part 3: Reading and Querying
        if start_from <= 3:
            print("\n" + "▶" * 40)
            print("Part 3/4: Reading and Querying")
            print("▶" * 40)
            print()
            print("What you'll learn:")
            print("  • Fetching entities with get(), all(), filter()")
            print("  • Chainable query methods")
            print("  • Querying relations by role players")
            print("  • Complex query patterns")
            print()
            print("Note: Advanced filtering (range queries, comparisons) is covered in Part 5 (crud_05_filter.py)")
            print()
            wait_for_continue()

            if not run_part(3, "crud_03_read", "Reading and Querying"):
                return

            wait_for_continue()

        # Part 4: Updating Entities
        print("\n" + "▶" * 40)
        print("Part 4/4: Updating Entities")
        print("▶" * 40)
        print()
        print("What you'll learn:")
        print("  • Updating single-value attributes")
        print("  • Updating multi-value attributes")
        print("  • The Fetch → Modify → Update workflow")
        print("  • TypeQL update query generation")
        print()
        wait_for_continue()

        if not run_part(4, "crud_04_update", "Updating Entities"):
            return

        # Tutorial complete
        print_section("🎉 Tutorial Complete!")
        print()
        print("Congratulations! You've completed the TypeBridge CRUD tutorial!")
        print()
        print("You learned:")
        print("  ✓ Schema definition and database setup")
        print("  ✓ Single and bulk insertion")
        print("  ✓ Querying with get(), all(), and filter()")
        print("  ✓ Updating single and multi-value attributes")
        print()
        print("Next steps:")
        print("  • Explore the advanced examples in examples/advanced/")
        print("  • Read the documentation in CLAUDE.md and ATTRIBUTE_API.md")
        print("  • Build your own TypeBridge application!")
        print()

    except KeyboardInterrupt:
        print("\n\n⚠️  Tutorial interrupted by user")
        print("\nTo resume from a specific part, run:")
        print("  uv run python examples/basic/crud.py")
        print("  and choose the part number when prompted.")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback

        traceback.print_exc()

    print()
    print("Thank you for trying TypeBridge! 🚀")
    print()


if __name__ == "__main__":
    main()

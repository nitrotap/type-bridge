"""CLI entry point for the TypeBridge schema generator.

Usage:
    python -m type_bridge.generator schema.tql -o ./myapp/models/
    python -m type_bridge.generator schema.tql --output ./myapp/models/ --version 2.0.0

The output directory is required to ensure generated code goes to an explicit,
intentional location. This prevents accidental overwrites and makes the
destination clear in version control.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from . import generate_models

logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> int:
    """Run the code generator CLI."""
    parser = argparse.ArgumentParser(
        prog="python -m type_bridge.generator",
        description="Generate TypeBridge Python models from a TypeDB schema file.",
        epilog=(
            "The --output directory is required. We recommend a dedicated "
            "directory like './myapp/models/' or './src/schema/' to keep "
            "generated code separate from hand-written code."
        ),
    )

    parser.add_argument(
        "schema",
        type=Path,
        help="Path to the TypeDB schema file (.tql)",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        metavar="DIR",
        help="Output directory for generated package (required)",
    )

    parser.add_argument(
        "--version",
        type=str,
        default="1.0.0",
        help="Schema version string (default: 1.0.0)",
    )

    parser.add_argument(
        "--no-copy-schema",
        action="store_true",
        help="Don't copy the schema file to the output directory",
    )

    parser.add_argument(
        "--implicit-keys",
        type=str,
        nargs="*",
        default=[],
        help="Attribute names to treat as @key even if not marked",
    )

    args = parser.parse_args(argv)
    logger.debug(
        f"CLI arguments: schema={args.schema}, output={args.output}, version={args.version}"
    )

    # Validate schema file exists
    if not args.schema.exists():
        logger.error(f"Schema file not found: {args.schema}")
        print(f"Error: Schema file not found: {args.schema}", file=sys.stderr)
        return 1

    if not args.schema.is_file():
        logger.error(f"Not a file: {args.schema}")
        print(f"Error: Not a file: {args.schema}", file=sys.stderr)
        return 1

    try:
        logger.info(f"Generating models from {args.schema} to {args.output}")
        generate_models(
            schema=args.schema,
            output_dir=args.output,
            implicit_key_attributes=args.implicit_keys or None,
            schema_version=args.version,
            copy_schema=not args.no_copy_schema,
        )
    except Exception as e:
        logger.error(f"Generation failed: {e}", exc_info=True)
        print(f"Error: {e}", file=sys.stderr)
        return 1

    logger.info(f"Successfully generated models in: {args.output}")
    print(f"Generated TypeBridge models in: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

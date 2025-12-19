"""CLI entry point for the TypeBridge schema generator.

Usage:
    python -m type_bridge.generator schema.tql -o ./myapp/models/
    python -m type_bridge.generator schema.tql --output ./myapp/models/ --version 2.0.0
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated

import typer

from . import generate_models

logger = logging.getLogger(__name__)

app = typer.Typer(
    name="type_bridge.generator",
    help="Generate TypeBridge Python models from a TypeDB schema file.",
    epilog=(
        "The --output directory is required. We recommend a dedicated "
        "directory like './myapp/models/' or './src/schema/' to keep "
        "generated code separate from hand-written code."
    ),
    no_args_is_help=True,
)


@app.command()
def main(
    schema: Annotated[
        Path,
        typer.Argument(help="Path to the TypeDB schema file (.tql)"),
    ],
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output directory for generated package"),
    ],
    version: Annotated[
        str,
        typer.Option(help="Schema version string"),
    ] = "1.0.0",
    no_copy_schema: Annotated[
        bool,
        typer.Option("--no-copy-schema", help="Don't copy the schema file to the output directory"),
    ] = False,
    schema_path: Annotated[
        str | None,
        typer.Option(
            "--schema-path",
            help=(
                "Custom path for the schema file. Relative paths are resolved "
                "against the output directory. Absolute paths write to that location."
            ),
        ),
    ] = None,
    implicit_keys: Annotated[
        list[str] | None,
        typer.Option("--implicit-keys", help="Attribute names to treat as @key even if not marked"),
    ] = None,
) -> None:
    """Generate TypeBridge Python models from a TypeDB schema file."""
    logger.debug(f"CLI arguments: schema={schema}, output={output}, version={version}")

    if not schema.exists():
        logger.error(f"Schema file not found: {schema}")
        typer.echo(f"Error: Schema file not found: {schema}", err=True)
        raise typer.Exit(1)

    if not schema.is_file():
        logger.error(f"Not a file: {schema}")
        typer.echo(f"Error: Not a file: {schema}", err=True)
        raise typer.Exit(1)

    try:
        logger.info(f"Generating models from {schema} to {output}")
        generate_models(
            schema=schema,
            output_dir=output,
            implicit_key_attributes=implicit_keys or None,
            schema_version=version,
            copy_schema=not no_copy_schema,
            schema_path=schema_path,
        )
    except Exception as e:
        logger.error(f"Generation failed: {e}", exc_info=True)
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    logger.info(f"Successfully generated models in: {output}")
    typer.echo(f"Generated TypeBridge models in: {output}")


if __name__ == "__main__":
    app()

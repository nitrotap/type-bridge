"""Pytest configuration and shared fixtures."""

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add custom command line options."""
    parser.addoption(
        "--cleanup",
        action="store_true",
        default=False,
        help="Enable database cleanup after tests (default: False, databases are kept for inspection)",
    )

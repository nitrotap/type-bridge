# Development Guide

This guide covers development setup, commands, and code quality standards for TypeBridge.

## Table of Contents

- [Package Management](#package-management)
- [Docker Setup](#docker-setup)
- [Running Examples](#running-examples)
- [Code Quality Standards](#code-quality-standards)
- [Temporary Files Policy](#temporary-files-policy)

## Package Management

### Installing Dependencies

```bash
# Install all dependencies including dev tools
uv sync --extra dev

# Or install in editable mode with pip
uv pip install -e ".[dev]"
```

### Project Dependencies

The project requires:
- `typedb-driver==3.5.5`: Official Python driver for TypeDB connectivity
- `pydantic>=2.0`: For validation and type coercion
- `isodate==0.7.2`: For Duration type support (ISO 8601)

Development dependencies include:
- `pytest`: Testing framework
- `ruff`: Fast Python linter and formatter
- `pyright`: Static type checker
- `pytest-order`: For ordered integration tests

## Docker Setup

### Integration Tests with TypeDB

Integration tests require a TypeDB 3.5.5 server. The project includes Docker configuration for automated setup.

**Requirements:**
- Docker and Docker Compose installed
- Port 1729 available (TypeDB server)

**Docker is managed automatically** by the test fixtures. Simply run:

```bash
./test-integration.sh          # Starts Docker, runs tests, stops Docker
./test-integration.sh -v       # With verbose output
```

### Manual Docker Control

```bash
# Start TypeDB container
docker compose up -d

# View TypeDB logs
docker compose logs typedb

# Stop TypeDB container
docker compose down
```

### Skip Docker (Use Existing Server)

If you have a TypeDB server already running:

```bash
# Start your TypeDB 3.x server
typedb server

# Run integration tests without Docker
USE_DOCKER=false uv run pytest -m integration
USE_DOCKER=false uv run pytest -m integration -v  # Verbose
```

## Running Examples

TypeBridge includes comprehensive examples organized by complexity:

### Basic CRUD Examples (Start Here!)

```bash
uv run python examples/basic/crud_01_define.py  # Schema definition and basic usage
uv run python examples/basic/crud_02_insert.py  # Bulk insertion
uv run python examples/basic/crud_03_read.py    # Fetching API: get(), filter(), all()
uv run python examples/basic/crud_04_update.py  # Update API for single and multi-value attrs
```

### Advanced Examples

```bash
uv run python examples/advanced/schema_01_manager.py     # Schema operations
uv run python examples/advanced/schema_02_comparison.py  # Schema diff and comparison
uv run python examples/advanced/schema_03_conflict.py    # Conflict detection
uv run python examples/advanced/pydantic_features.py     # Pydantic integration
uv run python examples/advanced/type_safety.py           # Literal types for type safety
uv run python examples/advanced/string_representation.py # Custom __str__ and __repr__
```

## Code Quality Standards

TypeBridge maintains high code quality standards with zero tolerance for technical debt.

### Linting and Type Checking

All code must pass these checks without errors or warnings:

```bash
# Ruff - Python linter and formatter (must pass with 0 errors)
uv run ruff check .          # Check for style issues
uv run ruff format .         # Auto-format code

# Pyright - Static type checker (must pass with 0 errors, 0 warnings)
uv run pyright type_bridge/  # Check core library
uv run pyright examples/     # Check examples
uv run pyright tests/        # Check tests (note: intentional validation errors are OK)
```

### Code Quality Requirements

1. **No linter suppressions**: Do not use `# noqa`, `# type: ignore`, or similar comments
   - Exception: Tests intentionally checking validation failures may show type warnings

2. **Modern Python syntax**:
   - Use PEP 604 (`X | Y`) instead of `Union[X, Y]`
   - Use PEP 695 type parameters (`class Foo[T]:`) when possible
   - Use `X | None` instead of `Optional[X]`

   ```python
   # ✅ Modern (Python 3.12+)
   age: int | str | None

   # ❌ Deprecated
   from typing import Union, Optional
   age: Optional[Union[int, str]]
   ```

3. **Consistent ModelAttrInfo usage**:
   - Always use `attr_info.typ` and `attr_info.flags`
   - Never use dict-style access like `attr_info["type"]`

   ```python
   # ✅ CORRECT
   owned_attrs = Entity.get_owned_attributes()
   for field_name, attr_info in owned_attrs.items():
       attr_class = attr_info.typ
       flags = attr_info.flags

   # ❌ WRONG - Never use dict-style access
   attr_class = attr_info["type"]   # Will fail!
   flags = attr_info["flags"]       # Will fail!
   ```

4. **Import organization**: Imports must be sorted and organized (ruff handles this automatically)

### Testing Requirements

All tests must pass:

```bash
# Unit tests (default)
uv run pytest                              # All 284 unit tests

# Integration tests
./test-integration.sh                     # All 133 integration tests with Docker

# All tests
uv run pytest -m ""                       # All 417 tests
./test.sh                                 # Full test suite with detailed output
./check.sh                                # Linting and type checking
```

When adding new features:
- Add corresponding tests in `tests/`
- Ensure examples in `examples/` demonstrate the feature
- Update documentation
- Run all quality checks before committing

### Pre-commit Checklist

Before committing changes, ensure:

1. ✅ All tests pass (`uv run pytest -m ""`)
2. ✅ Ruff passes (`uv run ruff check .`)
3. ✅ Code is formatted (`uv run ruff format .`)
4. ✅ Pyright passes with 0 errors (`uv run pyright type_bridge/`)
5. ✅ Examples run successfully
6. ✅ Documentation is updated

Quick command to run all checks:

```bash
./check.sh  # Runs linting and type checking
```

## Temporary Files Policy

When creating temporary test scripts, reports, or analysis files during development/debugging:

- **Create them in the `tmp/` directory** (already in .gitignore)
- **DO NOT create temporary files in the project root**
- Examples: test scripts, debug reports, analysis documents, verification files
- Exception: Permanent documentation that should be committed belongs in the root or docs/

```bash
# ✅ CORRECT
tmp/test_script.py
tmp/debug_report.md
tmp/analysis.txt

# ❌ WRONG
test_script.py          # Don't put in root
debug_report.md         # Don't put in root
```

## Development Workflow

### Typical Development Cycle

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**:
   - Edit code in `type_bridge/`
   - Add tests in `tests/unit/` or `tests/integration/`
   - Add examples in `examples/` if applicable

3. **Run tests locally**:
   ```bash
   # Quick: unit tests only
   uv run pytest

   # Full: with integration tests
   ./test-integration.sh
   ```

4. **Check code quality**:
   ```bash
   ./check.sh
   ```

5. **Run examples to verify**:
   ```bash
   uv run python examples/basic/crud_01_define.py
   ```

6. **Update documentation**:
   - Update relevant docs in `docs/`
   - Update CHANGELOG.md
   - Update README.md if needed

7. **Commit and push**:
   ```bash
   git add .
   git commit -m "feat: your feature description"
   git push origin feature/your-feature-name
   ```

### Debugging Tips

**Using Python Debugger:**

```python
# Add breakpoint in code
breakpoint()

# Run test with pdb
uv run pytest tests/unit/test_something.py -s
```

**Verbose Test Output:**

```bash
# Show print statements and full output
uv run pytest -v -s

# Show captured logs
uv run pytest --log-cli-level=DEBUG
```

**TypeDB Query Debugging:**

Enable query logging in your test/example:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Environment Setup

### Python Version

This project requires **Python 3.13+**. Check your Python version:

```bash
python --version  # Should show 3.13 or higher
```

If you need to install Python 3.13, use:

```bash
# Using pyenv (recommended)
pyenv install 3.13
pyenv local 3.13

# Or download from python.org
```

### Virtual Environment

The project uses `uv` for package management, which handles virtual environments automatically. If you need to manually activate:

```bash
# uv creates .venv automatically
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
```

### IDE Configuration

**VS Code:**

Install recommended extensions:
- Python (Microsoft)
- Pylance (Microsoft)
- Ruff (Astral Software)

Configure settings.json:

```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "none",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll": true,
      "source.organizeImports": true
    }
  }
}
```

**PyCharm:**

1. Set Python interpreter to `.venv/bin/python`
2. Enable Pyright as external tool
3. Configure Ruff as external formatter
4. Enable "Reformat code" on save

## Continuous Integration

The project uses GitHub Actions for CI. See `.github/workflows/ci.yml` for the full configuration.

CI runs:
- Linting (Ruff)
- Type checking (Pyright)
- Unit tests
- Integration tests (with Docker)

All checks must pass before merging PRs.

---

For testing specifics, see [TESTING.md](TESTING.md).

For TypeDB integration details, see [TYPEDB.md](TYPEDB.md).

For internal architecture, see [INTERNALS.md](INTERNALS.md).

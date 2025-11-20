#!/bin/bash
# Code quality check script for local development

set -e  # Exit on error

echo "🔍 Running code quality checks..."
echo ""

echo "📝 Running ruff check with auto-fix..."
uv run ruff check --fix .
echo "✓ Ruff check complete"
echo ""

echo "🔧 Running ruff format..."
uv run ruff format .
echo "✓ Ruff format complete"
echo ""

echo "🔎 Running pyright type checker..."
uv run pyright type_bridge
uv run pyright examples
uv run pyright tests
echo "✓ Pyright check complete"
echo ""

bash ./find_type_ignores.sh

echo "✅ All checks passed!"

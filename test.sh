#!/bin/bash
# Test script for running unit and integration tests

set -e  # Exit on error

echo "🧪 Running test suite..."
echo ""

echo "⚡ Running unit tests (fast, no external dependencies)..."
uv run pytest -v --tb=short
echo "✓ Unit tests complete"
echo ""

echo "🔗 Running integration tests (requires TypeDB server)..."
echo "⚠️  Make sure TypeDB server is running: typedb server"
echo ""
uv run pytest -m integration -v --tb=short
echo "✓ Integration tests complete"
echo ""

echo "✅ All tests passed!"

#!/usr/bin/env bash
# Helper script to run integration tests with Docker

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Running integration tests with Docker...${NC}"

# Run pytest with integration marker
# Docker container management is handled by conftest.py
uv run pytest -m integration "$@"

echo -e "${GREEN}Integration tests completed!${NC}"

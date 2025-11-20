#!/bin/bash
# Find all type ignore comments in the codebase
# Excludes: tests, examples, tmp directories (optional)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
EXCLUDE_TESTS=false
EXCLUDE_EXAMPLES=false
EXCLUDE_TMP=true

while [[ $# -gt 0 ]]; do
    case $1 in
        --exclude-tests)
            EXCLUDE_TESTS=true
            shift
            ;;
        --exclude-examples)
            EXCLUDE_EXAMPLES=true
            shift
            ;;
        --include-tmp)
            EXCLUDE_TMP=false
            shift
            ;;
        --all)
            EXCLUDE_TESTS=false
            EXCLUDE_EXAMPLES=false
            EXCLUDE_TMP=false
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--exclude-tests] [--exclude-examples] [--include-tmp] [--all]"
            exit 1
            ;;
    esac
done

# Build grep exclude patterns (always exclude .venv, .git, etc.)
EXCLUDE_PATTERN="--exclude-dir=.venv --exclude-dir=.git --exclude-dir=__pycache__ --exclude-dir=node_modules --exclude-dir=.pytest_cache --exclude-dir=type-check-except"

if [ "$EXCLUDE_TESTS" = true ]; then
    EXCLUDE_PATTERN="$EXCLUDE_PATTERN --exclude-dir=tests"
fi
if [ "$EXCLUDE_EXAMPLES" = true ]; then
    EXCLUDE_PATTERN="$EXCLUDE_PATTERN --exclude-dir=examples"
fi
if [ "$EXCLUDE_TMP" = true ]; then
    EXCLUDE_PATTERN="$EXCLUDE_PATTERN --exclude-dir=tmp"
fi

echo -e "${BLUE}Searching for type ignore comments...${NC}"
echo ""

# Search patterns
PATTERNS=(
    "type:\s*ignore"
    "noqa"
    "pyright:\s*ignore"
    "mypy:\s*ignore"
    "@(typing\.)?no_type_check"
)

# Count total
TOTAL=0

for pattern in "${PATTERNS[@]}"; do
    COUNT=$(grep -r -n --include="*.py" $EXCLUDE_PATTERN -E "#\s*$pattern" "$SCRIPT_DIR" 2>/dev/null | wc -l)
    if [ $COUNT -gt 0 ]; then
        TOTAL=$((TOTAL + COUNT))
    fi
done

if [ $TOTAL -eq 0 ]; then
    echo -e "${GREEN}✅ No type ignore comments found!${NC}"
    exit 0
fi

echo -e "${YELLOW}Found $TOTAL type ignore comment(s):${NC}"
echo ""

# Show detailed results
echo -e "${BLUE}# type: ignore${NC}"
grep -r -n --include="*.py" $EXCLUDE_PATTERN -E "#\s*type:\s*ignore" "$SCRIPT_DIR" 2>/dev/null || echo "  (none)"
echo ""

echo -e "${BLUE}# noqa${NC}"
grep -r -n --include="*.py" $EXCLUDE_PATTERN -E "#\s*noqa" "$SCRIPT_DIR" 2>/dev/null || echo "  (none)"
echo ""

echo -e "${BLUE}# pyright: ignore${NC}"
grep -r -n --include="*.py" $EXCLUDE_PATTERN -E "#\s*pyright:\s*ignore" "$SCRIPT_DIR" 2>/dev/null || echo "  (none)"
echo ""

echo -e "${BLUE}# mypy: ignore${NC}"
grep -r -n --include="*.py" $EXCLUDE_PATTERN -E "#\s*mypy:\s*ignore" "$SCRIPT_DIR" 2>/dev/null || echo "  (none)"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "Total: ${RED}$TOTAL${NC} type ignore comment(s)"

if [ "$EXCLUDE_TESTS" = false ] && [ "$EXCLUDE_EXAMPLES" = false ]; then
    echo ""
    echo "💡 Tip: Use --exclude-tests and --exclude-examples to see only production code issues"
fi

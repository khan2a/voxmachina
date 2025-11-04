#!/bin/bash
# Manual code quality check script
# Run this to check code quality without committing

echo "🔍 Running code quality checks..."
echo ""

echo "📝 Running Black (formatter)..."
black --check webhook_server.py view_transcripts.py src/ tests/
BLACK_EXIT=$?

echo ""
echo "🔎 Running Ruff (linter)..."
ruff check webhook_server.py view_transcripts.py src/ tests/
RUFF_EXIT=$?

echo ""
if [ $BLACK_EXIT -eq 0 ] && [ $RUFF_EXIT -eq 0 ]; then
    echo "✅ All checks passed!"
    exit 0
else
    echo "❌ Some checks failed. Run the following to fix:"
    echo ""
    if [ $BLACK_EXIT -ne 0 ]; then
        echo "  black webhook_server.py view_transcripts.py src/ tests/"
    fi
    if [ $RUFF_EXIT -ne 0 ]; then
        echo "  ruff check --fix webhook_server.py view_transcripts.py src/ tests/"
    fi
    exit 1
fi

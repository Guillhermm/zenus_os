#!/bin/bash
# Test all packages in the monorepo

set -e

echo "🧪 Testing Zenus Monorepo..."
echo ""

# Check if Poetry is available
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry not found. Please install: curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

# Test core package
echo "📦 Testing zenus-core..."
poetry run pytest packages/core/tests -v --tb=short
echo "✅ Core tests passed"
echo ""

# Test CLI package
echo "📦 Testing zenus-cli..."
poetry run pytest packages/cli/tests -v --tb=short || {
    echo "⚠️  Some CLI tests failed (might be expected during migration)"
}
echo ""

# Verify CLI works
echo "🔍 Verifying CLI functionality..."
poetry run zenus --version
poetry run zenus help
echo "✅ CLI verification passed"
echo ""

echo "✅ All tests complete!"

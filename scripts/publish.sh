#!/bin/bash
# Publish packages to PyPI

set -e

echo "📦 Publishing Zenus packages to PyPI..."
echo ""

# Check version consistency
CORE_VERSION=$(grep '^version = ' packages/core/pyproject.toml | cut -d'"' -f2)
CLI_VERSION=$(grep '^version = ' packages/cli/pyproject.toml | cut -d'"' -f2)

echo "Core version: $CORE_VERSION"
echo "CLI version: $CLI_VERSION"

if [ "$CORE_VERSION" != "$CLI_VERSION" ]; then
    echo "❌ Version mismatch! Core and CLI must have same version."
    exit 1
fi

echo ""
read -p "Publish version $CORE_VERSION to PyPI? (y/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

# Run tests first
echo "🧪 Running tests before publish..."
poetry run pytest packages/core/tests -v || {
    echo "❌ Tests failed. Fix tests before publishing."
    exit 1
}

# Build and publish core
echo ""
echo "📦 Publishing zenus-core..."
cd packages/core
poetry build
poetry publish
cd ../..
echo "✅ zenus-core published"

# Build and publish CLI
echo ""
echo "📦 Publishing zenus-cli..."
cd packages/cli
poetry build
poetry publish
cd ../..
echo "✅ zenus-cli published"

echo ""
echo "✅ All packages published successfully!"
echo ""
echo "To install:"
echo "  pip install zenus-cli==$CLI_VERSION"

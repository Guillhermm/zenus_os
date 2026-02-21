#!/bin/bash
set -e

echo "🔄 Applying monorepo structure to zenus_os (in place)..."
echo ""

# Backup current structure
echo "📦 Creating backup..."
cp -r src src_backup
echo "  ✓ Backed up to src_backup/"

# Create monorepo structure
echo "🏗️  Creating monorepo structure..."
mkdir -p packages/core/src/zenus_core
mkdir -p packages/core/tests
mkdir -p packages/cli/src/zenus_cli
mkdir -p packages/cli/tests

# Core modules
CORE_MODULES=(
    "brain"
    "tools"
    "memory"
    "execution"
    "safety"
    "sandbox"
    "audit"
    "context"
)

# CLI modules
CLI_MODULES=(
    "cli"
    "zenusd"
)

echo "📋 Moving core modules..."
for module in "${CORE_MODULES[@]}"; do
    if [ -d "src/$module" ]; then
        echo "  ✓ $module → packages/core/src/zenus_core/"
        mv "src/$module" "packages/core/src/zenus_core/"
    fi
done

echo "📋 Moving CLI modules..."
for module in "${CLI_MODULES[@]}"; do
    if [ -d "src/$module" ]; then
        echo "  ✓ $module → packages/cli/src/zenus_cli/"
        mv "src/$module" "packages/cli/src/zenus_cli/"
    fi
done

# Move remaining src files
echo "📋 Moving remaining src files..."
if [ -f "src/__init__.py" ]; then
    cp "src/__init__.py" "packages/core/src/zenus_core/"
fi
if [ -f "src/main.py" ]; then
    cp "src/main.py" "packages/cli/src/zenus_cli/"
fi

# Move tests
echo "🧪 Organizing tests..."
for test_file in tests/*.py; do
    if [ -f "$test_file" ]; then
        # Core tests
        cp "$test_file" "packages/core/tests/" 2>/dev/null || true
    fi
done

# Copy configurations from monorepo
echo "📄 Copying configurations from zenus_monorepo..."
cp ~/projects/zenus_monorepo/pyproject.toml .
cp ~/projects/zenus_monorepo/packages/core/pyproject.toml packages/core/
cp ~/projects/zenus_monorepo/packages/cli/pyproject.toml packages/cli/
cp ~/projects/zenus_monorepo/pytest.ini .
cp ~/projects/zenus_monorepo/.gitignore .gitignore.new

# Copy CI/CD
echo "🔧 Copying CI/CD workflows..."
mkdir -p .github/workflows
cp ~/projects/zenus_monorepo/.github/workflows/*.yml .github/workflows/

# Copy scripts
echo "📜 Copying utility scripts..."
mkdir -p scripts
cp ~/projects/zenus_monorepo/scripts/*.sh scripts/
chmod +x scripts/*.sh

# Copy documentation
echo "📚 Copying new documentation..."
cp ~/projects/zenus_monorepo/MIGRATION.md .
cp ~/projects/zenus_monorepo/SETUP.md .
cp ~/projects/zenus_monorepo/TODO.md .
cp ~/projects/zenus_monorepo/MONOREPO_REFACTOR_SUMMARY.md .

# Create __init__.py files
echo "🔧 Creating __init__.py files..."
cat > packages/core/src/zenus_core/__init__.py << 'EOF'
"""
Zenus Core - Intent Execution Engine

The brain of Zenus OS: translates intent into validated system operations.
"""

__version__ = "0.3.0"

from zenus_core.cli.orchestrator import Orchestrator, OrchestratorError
from zenus_core.brain.llm.schemas import IntentIR, Step

__all__ = ["Orchestrator", "OrchestratorError", "IntentIR", "Step", "__version__"]
EOF

cat > packages/cli/src/zenus_cli/__init__.py << 'EOF'
"""
Zenus CLI - Command Line Interface

User-facing command-line interface for Zenus OS.
"""

__version__ = "0.3.0"

__all__ = ["__version__"]
EOF

# Create package READMEs
cat > packages/core/README.md << 'EOF'
# Zenus Core

The brain of Zenus OS - intelligent intent execution engine.

## Installation

```bash
pip install zenus-core
```

See main [Zenus documentation](../../README.md) for details.
EOF

cat > packages/cli/README.md << 'EOF'
# Zenus CLI

Command-line interface for Zenus OS.

## Installation

```bash
pip install zenus-cli
```

See main [Zenus documentation](../../README.md) for details.
EOF

# Fix imports
echo "🔧 Fixing imports..."
python3 ~/projects/zenus_monorepo/fix_imports.py

# Remove old src directory (now empty)
echo "🗑️  Removing old src directory..."
rmdir src 2>/dev/null || echo "  (src directory not empty, keeping it)"

echo ""
echo "✅ Monorepo structure applied successfully!"
echo ""
echo "Structure:"
echo "  zenus_os/"
echo "  ├── packages/"
echo "  │   ├── core/     (zenus-core)"
echo "  │   └── cli/      (zenus-cli)"
echo "  ├── .github/workflows/  (CI/CD)"
echo "  ├── scripts/      (utilities)"
echo "  └── src_backup/   (original backup)"
echo ""
echo "Next steps:"
echo "  1. poetry install"
echo "  2. poetry run pytest"
echo "  3. poetry run zenus --version"
echo "  4. git add -A"
echo "  5. git commit -m 'Refactor: Apply monorepo structure'"

# Zenus Monorepo Setup Guide

Complete guide for setting up the Zenus development environment.

## Prerequisites

- Python 3.10 or higher
- Git
- pip

## Quick Start

### 1. Install Poetry

```bash
curl -sSL https://install.python-poetry.org | python3 -

# Add to PATH (add to ~/.bashrc or ~/.zshrc)
export PATH="$HOME/.local/bin:$PATH"

# Verify installation
poetry --version
```

### 2. Clone and Setup

```bash
git clone https://github.com/Guillhermm/zenus.git
cd zenus

# Install all dependencies
poetry install

# Install Playwright browsers (for BrowserOps)
poetry run playwright install chromium
```

### 3. Configure LLM

```bash
cp .env.example .env
# Edit .env to configure your LLM backend
```

**Options**:
```bash
# Ollama (local, free)
ZENUS_LLM=ollama
OLLAMA_MODEL=phi3:mini

# OpenAI (cloud)
ZENUS_LLM=openai
OPENAI_API_KEY=sk-your-key

# DeepSeek (cloud, cost-effective)
ZENUS_LLM=deepseek
DEEPSEEK_API_KEY=sk-your-key
```

### 4. Run Tests

```bash
# All tests
poetry run pytest

# Quick smoke test
./scripts/test-all.sh

# Specific package
poetry run pytest packages/core/tests -v
```

### 5. Try the CLI

```bash
# Check version
poetry run zenus --version

# Interactive mode
poetry run zenus

# Direct execution
poetry run zenus "list files in downloads"

# Dry run
poetry run zenus --dry-run "organize downloads"
```

## Development Workflow

### Making Changes

```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes in packages/core or packages/cli

# Run tests
poetry run pytest

# Format code
poetry run black packages/

# Lint code
poetry run ruff check packages/

# Commit
git add .
git commit -m "feat: Add new feature"

# Push and create PR
git push origin feature/my-feature
```

### Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov

# Run specific test file
poetry run pytest packages/core/tests/test_planner.py -v

# Run specific test
poetry run pytest packages/core/tests/test_planner.py::test_execute_plan -v

# Run tests matching pattern
poetry run pytest -k "test_file" -v
```

### Working with Packages

#### Core Package (zenus-core)
```bash
cd packages/core

# Install in editable mode (already done by root poetry install)
# Make changes to src/zenus_core/

# Run core tests
poetry run pytest tests/ -v

# Build package
poetry build
```

#### CLI Package (zenus-cli)
```bash
cd packages/cli

# Make changes to src/zenus_cli/

# Test CLI
poetry run zenus --version

# Run CLI tests
poetry run pytest tests/ -v

# Build package
poetry build
```

### Adding Dependencies

```bash
# Add to core
cd packages/core
poetry add requests

# Add to CLI
cd packages/cli
poetry add typer

# Add dev dependency (root)
cd ../..
poetry add --group dev pytest-asyncio
```

## CI/CD

### GitHub Actions Workflows

**test.yml** - Runs on every push and PR
- Installs dependencies
- Runs linting
- Runs all tests
- Uploads coverage

**pr-check.yml** - Blocks PR merging
- Runs all tests
- Checks code formatting
- Verifies CLI works
- Comments on PR status

**publish.yml** - Publishes to PyPI on release
- Runs tests first (blocks if fail)
- Builds packages
- Publishes to PyPI

### Running CI Locally

```bash
# Simulate CI test workflow
./scripts/test-all.sh

# Check formatting
poetry run black --check packages/

# Run linting
poetry run ruff check packages/

# Type checking
poetry run mypy packages/core/src --ignore-missing-imports
```

## Publishing

### Prerequisites

1. PyPI account
2. API token from https://pypi.org/manage/account/token/
3. Token added to GitHub secrets as `PYPI_TOKEN`

### Manual Publishing

```bash
# Update version in both pyproject.toml files
# packages/core/pyproject.toml
# packages/cli/pyproject.toml

# Run publish script
./scripts/publish.sh

# Or manually:
cd packages/core
poetry build
poetry publish

cd ../cli
poetry build
poetry publish
```

### Automated Publishing

```bash
# Create and push tag
git tag v0.3.0
git push origin v0.3.0

# Create GitHub release
# This triggers the publish workflow automatically
```

## Troubleshooting

### Poetry not found

```bash
# Add to PATH
export PATH="$HOME/.local/bin:$PATH"

# Or reinstall
curl -sSL https://install.python-poetry.org | python3 -
```

### Import errors

```bash
# Reinstall packages
poetry install --no-cache

# Check Python path
poetry run python -c "import sys; print(sys.path)"

# Verify package installed
poetry run python -c "import zenus_core; print(zenus_core.__version__)"
```

### Tests failing

```bash
# Clear pytest cache
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null

# Reinstall
poetry install

# Run single test for debugging
poetry run pytest packages/core/tests/test_planner.py::test_execute_plan -vv
```

### CLI not working

```bash
# Verify installation
poetry run which zenus

# Check if executable
poetry run zenus --version

# Debug imports
poetry run python -c "from zenus_cli.main import main; main(['--version'])"
```

## Package Structure

```
zenus/
├── packages/
│   ├── core/              # zenus-core
│   │   ├── src/
│   │   │   └── zenus_core/
│   │   │       ├── __init__.py
│   │   │       ├── brain/      # LLM, planning
│   │   │       ├── tools/      # 10 tools
│   │   │       ├── memory/     # 4-layer memory
│   │   │       ├── execution/  # Parallel executor
│   │   │       └── ...
│   │   └── tests/
│   │
│   └── cli/               # zenus-cli
│       ├── src/
│       │   └── zenus_cli/
│       │       ├── cli/        # Orchestrator, formatter
│       │       └── zenusd/     # Entry point
│       └── tests/
│
├── docs/                  # Documentation
├── scripts/               # Utility scripts
└── .github/workflows/     # CI/CD
```

## Tips

### Fast Testing
```bash
# Skip slow tests
poetry run pytest -m "not slow"

# Run only unit tests
poetry run pytest -m unit

# Parallel testing (install pytest-xdist)
poetry run pytest -n auto
```

### Code Quality
```bash
# Auto-format
poetry run black packages/

# Auto-fix linting issues
poetry run ruff check --fix packages/

# Type check
poetry run mypy packages/core/src
```

### Development Speed
```bash
# Use poetry shell for repeated commands
poetry shell

# Now you can run without "poetry run"
zenus --version
pytest
black packages/
```

## Resources

- [Poetry Documentation](https://python-poetry.org/docs/)
- [pytest Documentation](https://docs.pytest.org/)
- [GitHub Actions](https://docs.github.com/en/actions)
- [Zenus Documentation](./docs/)

## Support

- GitHub Issues: https://github.com/Guillhermm/zenus/issues
- Discussions: https://github.com/Guillhermm/zenus/discussions

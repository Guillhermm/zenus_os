# Dependency Fix - CLI/TUI Missing LLM Provider Dependencies

## The Problem

After adding Anthropic Claude support, users on fresh installations experienced:

```
ModuleNotFoundError: No module named 'anthropic'
```

Even after running `./update.sh`, which runs `poetry install` in all packages.

## Root Cause

### Monorepo Package Structure

Zenus OS is structured as a Poetry monorepo with 3 packages:

```
packages/
├── core/          # Core library (has anthropic, openai dependencies)
├── cli/           # CLI interface (depends on core)
└── tui/           # TUI interface (depends on core)
```

### The CLI Dependency Chain

```
User runs: zenus "list files"
    ↓
CLI package (packages/cli) executes
    ↓
Uses CLI package's virtual environment
    ↓
Imports from zenus_core
    ↓
zenus_core tries: from anthropic import Anthropic
    ❌ FAILS - anthropic not in CLI's venv!
```

### Why Core's Dependencies Weren't Available

When CLI declares `zenus-core = {path = "../core", develop = true}`:
- ✓ Core's Python modules are importable
- ✗ Core's dependencies are NOT installed in CLI's venv

This is Poetry's default behavior for path dependencies - it links the code but doesn't install transitive dependencies unless explicitly requested.

## The Solution

### Add LLM Dependencies to CLI and TUI

Both CLI and TUI packages now explicitly declare the LLM provider dependencies they need at runtime:

**packages/cli/pyproject.toml**:
```toml
[tool.poetry.dependencies]
python = "^3.10"
zenus-core = {path = "../core", develop = true}
rich = "^13.7.0"
# LLM provider dependencies (needed for runtime)
openai = "^1.0.0"
anthropic = "^0.47.0"
```

**packages/tui/pyproject.toml**:
```toml
[tool.poetry.dependencies]
python = "^3.10"
zenus-core = {path = "../core", develop = true}
textual = "^0.47.0"
rich = "^13.7.0"
# LLM provider dependencies (needed for runtime)
openai = "^1.0.0"
anthropic = "^0.47.0"
```

### Why This Works

Now the dependency chain is:
```
CLI package declares: anthropic ^0.47.0
    ↓
poetry install for CLI
    ↓
Installs anthropic into CLI's venv
    ↓
User runs: zenus "list files"
    ↓
Core imports anthropic
    ✓ SUCCESS - anthropic is in CLI's venv!
```

## Why Not Use Different Package Modes?

### Option 1: All packages share one venv (rejected)
- Would require restructuring the entire monorepo
- Breaks package isolation
- Makes individual package testing harder

### Option 2: Include all transitive dependencies (rejected)
- Poetry doesn't have a simple flag for this with path dependencies
- Would still require configuration changes

### Option 3: Current solution (chosen) ✓
- Simple, explicit, and clear
- Each package declares what it actually needs at runtime
- Easy to understand and maintain
- Works with Poetry's default behavior

## Files Changed

1. **packages/cli/pyproject.toml**
   - Added `openai = "^1.0.0"`
   - Added `anthropic = "^0.47.0"`

2. **packages/cli/poetry.lock**
   - Regenerated with new dependencies

3. **packages/tui/pyproject.toml**
   - Added `openai = "^1.0.0"`
   - Added `anthropic = "^0.47.0"`

4. **packages/tui/poetry.lock**
   - Regenerated with new dependencies

5. **TROUBLESHOOTING.md**
   - Updated to explain this issue and solution

## For Users on the Broken Version

If you pulled updates before this fix:

```bash
cd ~/projects/zenus_os
git pull
./update.sh
```

The `update.sh` script will install the newly-added dependencies.

## For Future LLM Providers

When adding new LLM providers, remember to:

1. ✓ Add dependency to `packages/core/pyproject.toml`
2. ✓ Add dependency to `packages/cli/pyproject.toml`
3. ✓ Add dependency to `packages/tui/pyproject.toml`
4. ✓ Create the LLM provider class in core
5. ✓ Update factory.py
6. ✓ Update .env.example
7. ✓ Update install.sh

## Testing Checklist

To verify a fresh installation works:

```bash
# In a clean directory (or use a different machine)
git clone <repo-url>
cd zenus_os
./install.sh

# Choose Anthropic during setup
# Enter a valid API key

# Test it
zenus "list files"
```

Should work without any module import errors!

## Commit

This fix is in commit: `[upcoming after commit]`

View changes:
```bash
git show [commit-hash]
```

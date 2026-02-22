# Installation Script Fixes - 2026-02-22 (REVISED)

## Issues Found

When attempting to run Zenus OS on another PC, three critical issues were identified:

### 1. Poetry Incorrectly Added as Dependency
**Problem**: Initially tried to add `poetry = "^1.8.0"` to root `pyproject.toml` dependencies, which is circular and breaks the installation.

**Root Cause**: Zenus OS is a **monorepo** with separate packages:
- `packages/core` - Core library
- `packages/cli` - CLI interface (depends on core)
- `packages/tui` - TUI interface (depends on core)

**Fix**: 
- Removed poetry from root dependencies (it's a tool, not a dependency)
- Updated install script to install each package independently
- Each package has its own `pyproject.toml` and is installed via Poetry

### 2. Install Script Not Properly Installing Packages
**Problem**: The install script only installed pip dependencies, not the Poetry packages themselves.

**Fix**: Updated `install.sh` to:
- Check if Poetry is installed, install if missing
- Install each package in order:
  1. `cd packages/core && poetry install` (core first)
  2. `cd packages/cli && poetry install` (CLI depends on core)
  3. `cd packages/tui && poetry install` (TUI depends on core)
- Skip LLM configuration if `.env` already exists
- Automatically add/update shell aliases

### 3. Inconsistent Alias Naming
**Problem**: Three aliases with mixed naming conventions:
- `zenus_os` (underscore)
- `zenus` (plain)
- `zenus-tui` (hyphen)

**Fix**: Standardized to two consistent aliases:
- `zenus` - Main CLI interface
- `zenus-tui` - TUI interface

## Monorepo Structure

```
zenus_os/
├── pyproject.toml           # Root config (no code, just dev tools)
├── poetry.lock              # Root lockfile
├── zenus.sh                 # CLI launcher
├── zenus-tui.sh             # TUI launcher
└── packages/
    ├── core/
    │   ├── pyproject.toml   # Core package config
    │   ├── poetry.lock
    │   └── src/zenus_core/
    ├── cli/
    │   ├── pyproject.toml   # CLI package config
    │   ├── poetry.lock
    │   └── src/zenus_cli/
    └── tui/
        ├── pyproject.toml   # TUI package config
        ├── poetry.lock
        └── src/zenus_tui/
```

## How It Works Now

1. **Install Poetry** (if not present)
2. **Install Core Package** (`packages/core`)
   - Contains `zenus_core` module
   - All other packages depend on this
3. **Install CLI Package** (`packages/cli`)
   - Contains `zenus_cli` module
   - Depends on `zenus-core`
   - Defines `zenus` command entry point
4. **Install TUI Package** (`packages/tui`)
   - Contains `zenus_tui` module
   - Depends on `zenus-core`
   - Defines `zenus-tui` command entry point
5. **Configure LLM** (if `.env` doesn't exist)
6. **Set up shell aliases**

## Launcher Scripts

Both launcher scripts use their respective package's Poetry environment:

**zenus.sh**:
```bash
cd packages/cli
poetry run zenus "$@"
```

**zenus-tui.sh**:
```bash
cd packages/tui
poetry run zenus-tui "$@"
```

## Testing the Fixes

On a fresh machine:

```bash
git clone <repo>
cd zenus_os
./install.sh
source ~/.bashrc
zenus help        # Works!
zenus-tui         # Works!
```

## Why This Approach?

✅ **Proper separation** - Each package is independently installable  
✅ **Clear dependencies** - CLI and TUI both depend on core  
✅ **No circular deps** - Poetry is a tool, not a package dependency  
✅ **Portable** - Works on any fresh Linux machine  
✅ **Maintainable** - Each package can be versioned independently

## Common Errors and Solutions

### Error: `poetry.lock is out of sync with pyproject.toml`
**Solution**: Run `poetry lock` in the affected package directory

### Error: `Module zenus_cli not found`
**Solution**: 
```bash
cd packages/cli
poetry install
```

### Error: `Module zenus_core not found`
**Solution**: Core must be installed first:
```bash
cd packages/core
poetry install
cd ../cli
poetry install
```

## Migration for Existing Users

If you already have Zenus OS installed:

```bash
cd ~/projects/zenus_os
git pull
./install.sh
source ~/.bashrc
```

The install script will:
- Reinstall all packages properly
- Update your shell aliases
- Skip LLM reconfiguration (keeps existing `.env`)

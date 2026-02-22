# Installation Script Fixes - 2026-02-22

## Issues Found

When attempting to run Zenus OS on another PC, three critical issues were identified:

### 1. Poetry Missing from Dependencies
**Problem**: Poetry was installed manually on the development machine but wasn't listed in `pyproject.toml` dependencies.

**Fix**: Added `poetry = "^1.8.0"` to `[tool.poetry.dependencies]` section.

### 2. Install Script Not Setting Up Aliases
**Problem**: The install script only suggested adding aliases manually but didn't automate the process.

**Fix**: Updated `install.sh` to:
- Check if Poetry is installed, install if missing
- Run `poetry install` to install all project dependencies
- Automatically add aliases to `~/.bashrc`
- Update existing aliases if they're already present
- Remove old inconsistent aliases

### 3. Inconsistent Alias Naming
**Problem**: Three aliases with mixed naming conventions:
- `zenus_os` (underscore)
- `zenus` (plain)
- `zenus-tui` (hyphen)

**Fix**: Standardized to two consistent aliases:
- `zenus` - Main CLI interface
- `zenus-tui` - TUI interface

## Files Modified

### 1. `pyproject.toml`
```toml
[tool.poetry.dependencies]
python = "^3.10"
poetry = "^1.8.0"  # ← ADDED
```

### 2. `install.sh`
Added automatic Poetry installation and alias setup:
- Installs Poetry if not present
- Runs `poetry install` for project dependencies
- Removes old aliases (zenus_os, inconsistent entries)
- Adds standardized aliases with absolute paths
- Provides clear post-install instructions

### 3. `zenus-tui.sh`
Fixed hardcoded path to use dynamic script directory:
```bash
# Before:
cd ~/projects/zenus_os/packages/tui

# After:
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/packages/tui"
```

## Testing the Fixes

To verify the fixes work on a fresh machine:

1. Clone the repository
2. Run `./install.sh`
3. Source the bashrc: `source ~/.bashrc`
4. Test the commands:
   - `zenus help`
   - `zenus "list files"`
   - `zenus-tui`

## Migration for Existing Users

If you already have Zenus OS installed with old aliases:

```bash
cd ~/projects/zenus_os
git pull
./install.sh
source ~/.bashrc
```

The install script will automatically update your aliases to the new standard.

## Benefits

✅ **Portable**: Works on any fresh Linux machine  
✅ **Consistent**: Standardized naming across all entry points  
✅ **Automated**: No manual alias editing required  
✅ **Self-contained**: All dependencies properly declared  
✅ **Idempotent**: Safe to run multiple times

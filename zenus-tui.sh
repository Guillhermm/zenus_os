#!/usr/bin/env bash
# Zenus TUI Launcher
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$SCRIPT_DIR/packages/tui"
poetry run zenus-tui "$@"

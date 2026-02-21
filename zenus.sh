#!/bin/bash
# Zenus OS launcher script for monorepo
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Run zenus via Poetry in the CLI package
cd "$SCRIPT_DIR/packages/cli"
poetry run zenus "$@"

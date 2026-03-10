"""
Pytest configuration and shared fixtures
"""

import sys
from pathlib import Path

# Add package src directories to path
root = Path(__file__).parent.parent
sys.path.insert(0, str(root / "packages" / "core" / "src"))
sys.path.insert(0, str(root / "packages" / "cli" / "src"))

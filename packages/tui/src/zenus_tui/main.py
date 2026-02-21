"""
Zenus TUI - Main Entry Point
"""

import sys
from zenus_tui.dashboard import main as dashboard_main


def main():
    """Main entry point for zenus-tui"""
    try:
        dashboard_main()
    except KeyboardInterrupt:
        print("\nGoodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

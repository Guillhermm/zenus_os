"""
Shell Helpers

Utilities for better readline integration and terminal handling.
"""

import sys


def setup_readline_prompt():
    """
    Configure readline to work properly with colored prompts
    
    Prevents prompt disappearing when using arrow keys.
    """
    try:
        import readline
        
        # Tell readline about invisible characters (color codes)
        # This prevents cursor position issues
        
        # Enable colored prompt without breaking readline
        # Use \001 and \002 to mark invisible sequences
        
        # This is handled by using plain input() instead of rich console.input()
        # which automatically handles ANSI codes correctly
        
    except ImportError:
        pass


def clear_line():
    """Clear current line in terminal"""
    sys.stdout.write('\r\033[K')
    sys.stdout.flush()


def move_cursor_up(lines: int = 1):
    """Move cursor up N lines"""
    sys.stdout.write(f'\033[{lines}A')
    sys.stdout.flush()


def save_cursor():
    """Save cursor position"""
    sys.stdout.write('\033[s')
    sys.stdout.flush()


def restore_cursor():
    """Restore cursor position"""
    sys.stdout.write('\033[u')
    sys.stdout.flush()

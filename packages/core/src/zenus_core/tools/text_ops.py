"""
Text Operations Tool

Handle text file operations: read, write, append, search.
"""

import os
from pathlib import Path
from typing import Optional
from zenus_core.tools.base import Tool


class TextOps(Tool):
    """Text file operations"""
    
    name = "TextOps"
    
    def read(self, path: str) -> str:
        """Read text file contents"""
        full_path = os.path.expanduser(path)
        
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {path}")
        
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Truncate very long files
        max_chars = 10000
        if len(content) > max_chars:
            content = content[:max_chars] + f"\n... (truncated, total {len(content)} chars)"
        
        return f"File content ({len(content)} chars):\n{content}"
    
    def write(self, path: str, content: str, overwrite: bool = True) -> str:
        """Write content to text file"""
        full_path = os.path.expanduser(path)
        
        # Check if file exists BEFORE writing
        file_existed = os.path.exists(full_path)
        
        if file_existed and not overwrite:
            raise FileExistsError(f"File exists: {path}. Use overwrite=true to replace.")
        
        # Create parent directories
        parent = os.path.dirname(full_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        action = "Overwrote" if file_existed else "Wrote"
        return f"{action} {len(content)} chars to {path}"
    
    def append(self, path: str, content: str) -> str:
        """Append content to text file"""
        full_path = os.path.expanduser(path)
        
        with open(full_path, 'a', encoding='utf-8') as f:
            f.write(content)
        
        return f"Appended {len(content)} chars to {path}"
    
    def search(self, path: str, pattern: str, case_sensitive: bool = False) -> str:
        """Search for pattern in text file"""
        full_path = os.path.expanduser(path)
        
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {path}")
        
        with open(full_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        matches = []
        search_pattern = pattern if case_sensitive else pattern.lower()
        
        for line_num, line in enumerate(lines, 1):
            search_line = line if case_sensitive else line.lower()
            if search_pattern in search_line:
                matches.append(f"Line {line_num}: {line.rstrip()}")
        
        if not matches:
            return f"No matches found for '{pattern}' in {path}"
        
        return f"Found {len(matches)} matches:\n" + "\n".join(matches[:50])
    
    def count_lines(self, path: str) -> str:
        """Count lines in text file"""
        full_path = os.path.expanduser(path)
        
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {path}")
        
        with open(full_path, 'r', encoding='utf-8') as f:
            line_count = sum(1 for _ in f)
        
        return f"{path}: {line_count} lines"
    
    def head(self, path: str, lines: int = 10) -> str:
        """Show first N lines of file"""
        full_path = os.path.expanduser(path)
        
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {path}")
        
        with open(full_path, 'r', encoding='utf-8') as f:
            head_lines = [next(f).rstrip() for _ in range(lines) if f]
        
        return f"First {len(head_lines)} lines of {path}:\n" + "\n".join(head_lines)
    
    def tail(self, path: str, lines: int = 10) -> str:
        """Show last N lines of file"""
        full_path = os.path.expanduser(path)
        
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {path}")
        
        with open(full_path, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
        
        tail_lines = [line.rstrip() for line in all_lines[-lines:]]
        
        return f"Last {len(tail_lines)} lines of {path}:\n" + "\n".join(tail_lines)

"""
Rich Output Formatter

Auto-detects data types and formats them beautifully:
- Tables with borders and alignment
- Lists with bullets
- JSON with syntax highlighting
- ASCII charts for numeric data
- Code blocks with language detection
"""

import json
import re
from typing import Any, List, Dict, Optional
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from rich.panel import Panel
from rich import box


class OutputFormatter:
    """
    Automatically format output based on detected data type
    
    Detects:
    - Tables (structured data)
    - Lists (bullet points)
    - JSON (syntax highlighting)
    - Code (language-specific highlighting)
    - Plain text (as-is)
    """
    
    def __init__(self):
        self.console = Console()
    
    def format(self, data: Any, title: Optional[str] = None) -> str:
        """
        Auto-format data based on type
        
        Args:
            data: Data to format (any type)
            title: Optional title for the output
        
        Returns:
            Formatted string (but also prints to console)
        """
        # Detect and format based on type
        if isinstance(data, dict):
            return self._format_dict(data, title)
        elif isinstance(data, list):
            return self._format_list(data, title)
        elif isinstance(data, str):
            return self._format_string(data, title)
        else:
            return str(data)
    
    def _format_dict(self, data: Dict, title: Optional[str] = None) -> str:
        """Format dictionary as table or JSON"""
        # Check if it's a simple key-value dict (format as table)
        if self._is_simple_dict(data):
            return self._dict_to_table(data, title)
        else:
            # Complex nested dict - show as JSON
            return self._dict_to_json(data, title)
    
    def _format_list(self, data: List, title: Optional[str] = None) -> str:
        """Format list as table or bullets"""
        if not data:
            return "Empty list"
        
        # Check if it's a list of dicts (table)
        if all(isinstance(item, dict) for item in data):
            return self._list_of_dicts_to_table(data, title)
        
        # Check if it's a list of tuples/lists (table)
        elif all(isinstance(item, (list, tuple)) for item in data):
            return self._list_of_lists_to_table(data, title)
        
        # Simple list - format as bullets
        else:
            return self._list_to_bullets(data, title)
    
    def _format_string(self, data: str, title: Optional[str] = None) -> str:
        """Format string - detect JSON, code, table patterns"""
        data = data.strip()
        
        # Try to parse as JSON
        if self._looks_like_json(data):
            try:
                parsed = json.loads(data)
                return self._dict_to_json(parsed, title)
            except:
                pass
        
        # Check for table-like structure
        if self._looks_like_table(data):
            return self._text_to_table(data, title)
        
        # Check for code
        if self._looks_like_code(data):
            lang = self._detect_language(data)
            return self._highlight_code(data, lang, title)
        
        # Plain text
        if title:
            panel = Panel(data, title=title, border_style="blue")
            self.console.print(panel)
        else:
            self.console.print(data)
        
        return data
    
    def _is_simple_dict(self, data: Dict) -> bool:
        """Check if dict is simple key-value (no nesting)"""
        for value in data.values():
            if isinstance(value, (dict, list)):
                return False
        return True
    
    def _dict_to_table(self, data: Dict, title: Optional[str] = None) -> str:
        """Format simple dict as two-column table"""
        table = Table(
            title=title,
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan"
        )
        
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="white")
        
        for key, value in data.items():
            table.add_row(str(key), str(value))
        
        self.console.print(table)
        return f"[Table: {len(data)} rows]"
    
    def _dict_to_json(self, data: Dict, title: Optional[str] = None) -> str:
        """Format dict as syntax-highlighted JSON"""
        json_str = json.dumps(data, indent=2)
        syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
        
        if title:
            panel = Panel(syntax, title=title, border_style="blue")
            self.console.print(panel)
        else:
            self.console.print(syntax)
        
        return json_str
    
    def _list_of_dicts_to_table(self, data: List[Dict], title: Optional[str] = None) -> str:
        """Format list of dicts as table"""
        if not data:
            return "Empty list"
        
        # Get all unique keys
        keys = set()
        for item in data:
            keys.update(item.keys())
        keys = sorted(keys)
        
        # Create table
        table = Table(
            title=title,
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan"
        )
        
        for key in keys:
            table.add_column(str(key), style="white")
        
        # Add rows
        for item in data:
            row = [str(item.get(key, "")) for key in keys]
            table.add_row(*row)
        
        self.console.print(table)
        return f"[Table: {len(data)} rows × {len(keys)} columns]"
    
    def _list_of_lists_to_table(self, data: List, title: Optional[str] = None) -> str:
        """Format list of lists/tuples as table"""
        table = Table(
            title=title,
            box=box.ROUNDED,
            show_header=False
        )
        
        # Determine number of columns
        max_cols = max(len(row) for row in data)
        for _ in range(max_cols):
            table.add_column(style="white")
        
        # Add rows
        for row in data:
            table.add_row(*[str(item) for item in row])
        
        self.console.print(table)
        return f"[Table: {len(data)} rows × {max_cols} columns]"
    
    def _list_to_bullets(self, data: List, title: Optional[str] = None) -> str:
        """Format list as bullet points"""
        lines = []
        if title:
            lines.append(f"[bold cyan]{title}[/bold cyan]")
        
        for item in data:
            lines.append(f"  • {item}")
        
        output = "\n".join(lines)
        self.console.print(output)
        return output
    
    def _text_to_table(self, text: str, title: Optional[str] = None) -> str:
        """Parse text table and format nicely"""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Detect delimiter
        delimiter = self._detect_delimiter(lines[0])
        
        # Parse rows
        rows = []
        for line in lines:
            row = [cell.strip() for cell in line.split(delimiter)]
            rows.append(row)
        
        if not rows:
            return text
        
        # Create table
        table = Table(
            title=title,
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan"
        )
        
        # First row as header
        for header in rows[0]:
            table.add_column(header, style="white")
        
        # Rest as data
        for row in rows[1:]:
            table.add_row(*row)
        
        self.console.print(table)
        return f"[Table: {len(rows)-1} rows × {len(rows[0])} columns]"
    
    def _highlight_code(self, code: str, language: str, title: Optional[str] = None) -> str:
        """Syntax highlight code"""
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        
        if title:
            panel = Panel(syntax, title=title, border_style="blue")
            self.console.print(panel)
        else:
            self.console.print(syntax)
        
        return code
    
    def _looks_like_json(self, text: str) -> bool:
        """Check if string looks like JSON"""
        return (text.startswith('{') and text.endswith('}')) or \
               (text.startswith('[') and text.endswith(']'))
    
    def _looks_like_table(self, text: str) -> bool:
        """Check if string looks like a table"""
        lines = text.split('\n')
        if len(lines) < 2:
            return False
        
        # Check for common delimiters in multiple lines
        delimiters = ['|', '\t', ',']
        for delim in delimiters:
            if sum(delim in line for line in lines[:3]) >= 2:
                return True
        
        return False
    
    def _looks_like_code(self, text: str) -> bool:
        """Check if string looks like code"""
        code_indicators = [
            'def ', 'class ', 'import ', 'function ', 'const ',
            'var ', 'let ', '#!/', '<?php', '<html', 'public class'
        ]
        return any(indicator in text for indicator in code_indicators)
    
    def _detect_language(self, code: str) -> str:
        """Detect programming language"""
        if 'def ' in code or 'import ' in code:
            return 'python'
        elif 'function ' in code or 'const ' in code or 'var ' in code:
            return 'javascript'
        elif 'public class' in code or 'private ' in code:
            return 'java'
        elif '<?php' in code:
            return 'php'
        elif '<html' in code or '<div' in code:
            return 'html'
        elif '#!/bin/bash' in code or '#!/bin/sh' in code:
            return 'bash'
        else:
            return 'text'
    
    def _detect_delimiter(self, line: str) -> str:
        """Detect delimiter in table line"""
        delimiters = {
            '|': line.count('|'),
            '\t': line.count('\t'),
            ',': line.count(','),
            ' ': line.count('  ')  # Multiple spaces
        }
        return max(delimiters, key=delimiters.get)


# Global formatter
_formatter: Optional[OutputFormatter] = None


def get_formatter() -> OutputFormatter:
    """Get singleton formatter"""
    global _formatter
    if _formatter is None:
        _formatter = OutputFormatter()
    return _formatter


def format_output(data: Any, title: Optional[str] = None) -> str:
    """Convenience function to format output"""
    formatter = get_formatter()
    return formatter.format(data, title)

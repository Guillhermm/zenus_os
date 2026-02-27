"""
Table Formatter

Creates beautiful, sortable, filterable tables using Rich.
Auto-formats data into professional tables.
"""

from typing import List, Dict, Optional, Any, Union
from enum import Enum
from rich.console import Console
from rich.table import Table
from rich.text import Text
from io import StringIO
import json


class TableStyle(Enum):
    """Predefined table styles"""
    DEFAULT = "default"
    MINIMAL = "simple"
    BOLD = "bold"
    DOUBLE = "double"
    ROUNDED = "rounded"
    MARKDOWN = "markdown"


class TableFormatter:
    """
    Formats data into beautiful tables
    
    Features:
    - Auto-detects columns from data
    - Sortable and filterable
    - Multiple visual styles
    - Handles various data types
    - Pagination for large datasets
    """
    
    def __init__(self):
        self.console = Console()
        self.max_cell_width = 50
    
    def format_table(
        self,
        data: Union[List[Dict], List[List], Dict],
        title: Optional[str] = None,
        columns: Optional[List[str]] = None,
        style: TableStyle = TableStyle.DEFAULT,
        sort_by: Optional[str] = None,
        filter_func: Optional[callable] = None,
        limit: Optional[int] = None,
        show_index: bool = False
    ) -> str:
        """
        Format data as a table
        
        Args:
            data: Data to format (list of dicts, list of lists, or dict)
            title: Table title
            columns: Column names (auto-detected if None)
            style: Visual style
            sort_by: Column to sort by
            filter_func: Function to filter rows
            limit: Max rows to display
            show_index: Show row index column
        
        Returns:
            Formatted table string
        """
        # Normalize data to list of dicts
        normalized_data = self._normalize_data(data, columns)
        
        if not normalized_data:
            return "No data to display"
        
        # Apply filter
        if filter_func:
            normalized_data = [row for row in normalized_data if filter_func(row)]
        
        # Apply sort
        if sort_by and sort_by in normalized_data[0]:
            try:
                normalized_data = sorted(normalized_data, key=lambda x: x.get(sort_by, ''))
            except:
                pass  # Sorting failed, continue unsorted
        
        # Apply limit
        total_rows = len(normalized_data)
        if limit and limit < total_rows:
            normalized_data = normalized_data[:limit]
            show_truncated = True
        else:
            show_truncated = False
        
        # Create Rich table
        table = self._create_rich_table(
            normalized_data,
            title,
            style,
            show_index
        )
        
        # Render to string
        buffer = StringIO()
        console = Console(file=buffer, force_terminal=True, width=120)
        console.print(table)
        
        # Add truncation notice
        if show_truncated:
            console.print(f"\n[dim]Showing {len(normalized_data)} of {total_rows} rows[/dim]")
        
        return buffer.getvalue()
    
    def _normalize_data(
        self, 
        data: Union[List, Dict], 
        columns: Optional[List[str]]
    ) -> List[Dict]:
        """Normalize various data formats to list of dicts"""
        
        # Already list of dicts
        if isinstance(data, list) and data and isinstance(data[0], dict):
            return data
        
        # List of lists/tuples
        elif isinstance(data, list) and data and isinstance(data[0], (list, tuple)):
            if columns:
                return [dict(zip(columns, row)) for row in data]
            else:
                # Auto-generate column names
                num_cols = len(data[0])
                auto_columns = [f"Col{i}" for i in range(num_cols)]
                return [dict(zip(auto_columns, row)) for row in data]
        
        # Dict (single row or column-oriented)
        elif isinstance(data, dict):
            # Check if values are lists (column-oriented)
            if data and isinstance(list(data.values())[0], list):
                # Column-oriented dict
                num_rows = len(list(data.values())[0])
                rows = []
                for i in range(num_rows):
                    row = {k: v[i] for k, v in data.items()}
                    rows.append(row)
                return rows
            else:
                # Single row
                return [data]
        
        # List of simple values
        elif isinstance(data, list):
            return [{"Value": v} for v in data]
        
        return []
    
    def _create_rich_table(
        self,
        data: List[Dict],
        title: Optional[str],
        style: TableStyle,
        show_index: bool
    ) -> Table:
        """Create Rich Table object"""
        
        # Map style enum to Rich style
        style_map = {
            TableStyle.DEFAULT: "default",
            TableStyle.MINIMAL: "simple",
            TableStyle.BOLD: "bold",
            TableStyle.DOUBLE: "double",
            TableStyle.ROUNDED: "rounded",
            TableStyle.MARKDOWN: "markdown"
        }
        
        # Create table
        table = Table(
            title=title,
            show_header=True,
            header_style="bold cyan",
            border_style="blue",
            box=None if style == TableStyle.MINIMAL else getattr(__import__('rich.box'), style_map.get(style, "DEFAULT").upper(), None)
        )
        
        # Add index column if requested
        if show_index:
            table.add_column("#", style="dim", width=5, justify="right")
        
        # Get columns from first row
        columns = list(data[0].keys())
        
        # Add columns
        for col in columns:
            # Determine column width
            max_val_len = max(len(str(row.get(col, ''))) for row in data[:10])  # Check first 10 rows
            width = min(max_val_len + 2, self.max_cell_width)
            
            table.add_column(col, overflow="fold", width=width)
        
        # Add rows
        for i, row in enumerate(data):
            row_values = []
            
            if show_index:
                row_values.append(str(i + 1))
            
            for col in columns:
                value = row.get(col, '')
                
                # Format value
                formatted_value = self._format_cell_value(value)
                row_values.append(formatted_value)
            
            table.add_row(*row_values)
        
        return table
    
    def _format_cell_value(self, value: Any) -> str:
        """Format a cell value for display"""
        if value is None:
            return "[dim]null[/dim]"
        elif isinstance(value, bool):
            return "[green]✓[/green]" if value else "[red]✗[/red]"
        elif isinstance(value, (int, float)):
            # Format numbers
            if isinstance(value, float):
                return f"{value:,.2f}"
            else:
                return f"{value:,}"
        elif isinstance(value, (list, dict)):
            # JSON-ify complex types
            json_str = json.dumps(value)
            if len(json_str) > self.max_cell_width:
                return json_str[:self.max_cell_width - 3] + "..."
            return json_str
        else:
            # String
            s = str(value)
            if len(s) > self.max_cell_width:
                return s[:self.max_cell_width - 3] + "..."
            return s
    
    def format_dict_as_properties(self, data: Dict, title: Optional[str] = None) -> str:
        """Format dict as property list (key-value table)"""
        
        table = Table(
            title=title,
            show_header=True,
            header_style="bold cyan",
            border_style="blue"
        )
        
        table.add_column("Property", style="cyan", width=30)
        table.add_column("Value", overflow="fold", width=70)
        
        for key, value in data.items():
            formatted_value = self._format_cell_value(value)
            table.add_row(str(key), formatted_value)
        
        buffer = StringIO()
        console = Console(file=buffer, force_terminal=True, width=120)
        console.print(table)
        
        return buffer.getvalue()


def format_table(
    data: Union[List, Dict],
    **kwargs
) -> str:
    """
    Quick function to format a table
    
    Returns:
        Formatted table string
    """
    formatter = TableFormatter()
    return formatter.format_table(data, **kwargs)

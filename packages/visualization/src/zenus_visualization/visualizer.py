"""
Main Visualizer - Automatic Data Visualization

Detects data types and renders beautiful visualizations automatically.
"""

import re
from typing import Any, Dict, List, Optional, Union
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich import box
from rich.tree import Tree
from rich.progress import Progress, BarColumn, TextColumn
import json


console = Console()


class Visualizer:
    """
    Automatically visualizes data in the most appropriate format
    
    Detects:
    - Tables (lists of dicts, process lists, file listings)
    - Progress/percentages (disk usage, memory usage)
    - JSON/structured data
    - Code diffs
    - File trees
    - Key-value pairs
    - Plain text (fallback)
    """
    
    @staticmethod
    def visualize(data: Union[str, Dict, List], context: Optional[str] = None) -> None:
        """
        Main entry point - automatically detects type and visualizes
        
        Args:
            data: Data to visualize (string, dict, list)
            context: Optional context (e.g., "file_list", "process_list", "disk_usage")
        """
        if isinstance(data, dict):
            Visualizer._visualize_dict(data, context)
        elif isinstance(data, list):
            Visualizer._visualize_list(data, context)
        elif isinstance(data, str):
            Visualizer._visualize_string(data, context)
        else:
            # Fallback to string representation
            console.print(f"  → {str(data)}", style="dim")
    
    @staticmethod
    def _visualize_string(data: str, context: Optional[str]) -> None:
        """Visualize string data with smart detection"""
        
        # Check for process list pattern
        if "PID" in data and "%" in data:
            Visualizer._visualize_process_list(data)
            return
        
        # Check for disk usage pattern
        if "GB" in data and ("used" in data.lower() or "free" in data.lower()):
            Visualizer._visualize_disk_usage(data)
            return
        
        # Check for CPU/Memory/Disk summary
        if "CPU:" in data and "Memory:" in data and "Disk:" in data:
            Visualizer._visualize_system_summary(data)
            return
        
        # Check for file list pattern (filenames with sizes)
        if context == "file_list" or re.search(r'\.(py|txt|md|json|yaml)', data):
            Visualizer._visualize_file_list(data)
            return
        
        # Check for percentage/progress
        if "%" in data:
            Visualizer._visualize_percentage(data)
            return
        
        # Check for JSON
        if data.strip().startswith('{') or data.strip().startswith('['):
            try:
                parsed = json.loads(data)
                Visualizer._visualize_dict(parsed, context)
                return
            except:
                pass
        
        # Check for key-value pairs
        if "\n" in data and ":" in data:
            Visualizer._visualize_key_value(data)
            return
        
        # Fallback: plain text with formatting
        console.print(f"  → {data}", style="cyan")
    
    @staticmethod
    def _visualize_process_list(data: str) -> None:
        """Visualize process list as a rich table"""
        lines = data.strip().split("\n")
        
        table = Table(
            title="🖥️  Processes",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta"
        )
        
        table.add_column("PID", style="cyan", justify="right", width=8)
        table.add_column("Name", style="green")
        table.add_column("Memory", style="yellow", justify="right", width=10)
        table.add_column("Usage Bar", width=20)
        
        for line in lines:
            # Parse: "PID 1009: openclaw-gateway (12.6% mem)"
            match = re.match(r'PID\s+(\d+):\s+(.+?)\s+\(([0-9.]+)%\s+mem\)', line)
            if match:
                pid, name, mem_pct = match.groups()
                mem_float = float(mem_pct)
                
                # Create visual bar
                bar_width = int(mem_float / 5)  # Scale to 20 chars max
                bar = "█" * bar_width + "░" * (20 - bar_width)
                
                # Color code by usage
                if mem_float > 10:
                    mem_style = "bold red"
                elif mem_float > 5:
                    mem_style = "bold yellow"
                else:
                    mem_style = "green"
                
                table.add_row(
                    pid,
                    name,
                    f"[{mem_style}]{mem_pct}%[/{mem_style}]",
                    f"[{mem_style}]{bar}[/{mem_style}]"
                )
        
        console.print(table)
    
    @staticmethod
    def _visualize_disk_usage(data: str) -> None:
        """Visualize disk usage with progress bar"""
        # Parse: "Disk /tmp: 110.0GB used / 260.0GB total (42.3% used, 136.8GB free)"
        match = re.search(
            r'Disk\s+(.+?):\s+([0-9.]+)GB\s+used\s+/\s+([0-9.]+)GB\s+total\s+\(([0-9.]+)%\s+used,\s+([0-9.]+)GB\s+free\)',
            data
        )
        
        if not match:
            console.print(f"  → {data}", style="cyan")
            return
        
        path, used, total, pct, free = match.groups()
        used_f, total_f, pct_f, free_f = float(used), float(total), float(pct), float(free)
        
        # Color code based on usage
        if pct_f > 90:
            color = "red"
            emoji = "🔴"
        elif pct_f > 75:
            color = "yellow"
            emoji = "🟡"
        else:
            color = "green"
            emoji = "🟢"
        
        # Create visual bar
        bar_width = 40
        filled = int((pct_f / 100) * bar_width)
        bar = "█" * filled + "░" * (bar_width - filled)
        
        # Build panel content
        content = f"""
[bold cyan]Path:[/bold cyan] {path}

[bold {color}]{emoji} {pct_f:.1f}% Used[/bold {color}]

[{color}]{bar}[/{color}]

[bold]Used:[/bold] {used_f:.1f} GB  [bold]Free:[/bold] {free_f:.1f} GB  [bold]Total:[/bold] {total_f:.1f} GB
"""
        
        panel = Panel(
            content.strip(),
            title="💾 Disk Usage",
            border_style=color,
            box=box.ROUNDED
        )
        
        console.print(panel)
    
    @staticmethod
    def _visualize_system_summary(data: str) -> None:
        """Visualize system resource summary"""
        lines = data.strip().split("\n")
        
        table = Table(
            title="🖥️  System Resources",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta"
        )
        
        table.add_column("Resource", style="cyan", width=12)
        table.add_column("Usage", style="yellow", justify="right", width=15)
        table.add_column("Visual", width=25)
        table.add_column("Details", style="dim")
        
        for line in lines:
            if line.startswith("CPU:"):
                # Parse: "CPU: 5.1% used (2 cores)"
                match = re.search(r'CPU:\s+([0-9.]+)%\s+used\s+\((\d+)\s+cores?\)', line)
                if match:
                    pct, cores = match.groups()
                    pct_f = float(pct)
                    bar = "█" * int(pct_f / 4) + "░" * (25 - int(pct_f / 4))
                    
                    color = "red" if pct_f > 80 else "yellow" if pct_f > 50 else "green"
                    
                    table.add_row(
                        "CPU",
                        f"[bold {color}]{pct}%[/bold {color}]",
                        f"[{color}]{bar}[/{color}]",
                        f"{cores} cores"
                    )
            
            elif line.startswith("Memory:"):
                # Parse: "Memory: 1.5GB / 3.7GB (52.9% used, 1.7GB free)"
                match = re.search(r'Memory:\s+([0-9.]+)GB\s+/\s+([0-9.]+)GB\s+\(([0-9.]+)%\s+used,\s+([0-9.]+)GB\s+free\)', line)
                if match:
                    used, total, pct, free = match.groups()
                    pct_f = float(pct)
                    bar = "█" * int(pct_f / 4) + "░" * (25 - int(pct_f / 4))
                    
                    color = "red" if pct_f > 90 else "yellow" if pct_f > 70 else "green"
                    
                    table.add_row(
                        "Memory",
                        f"[bold {color}]{pct}%[/bold {color}]",
                        f"[{color}]{bar}[/{color}]",
                        f"{used}GB / {total}GB"
                    )
            
            elif line.startswith("Disk:"):
                # Parse: "Disk: 110.0GB / 260.0GB (42.3% used, 136.8GB free)"
                match = re.search(r'Disk:\s+([0-9.]+)GB\s+/\s+([0-9.]+)GB\s+\(([0-9.]+)%\s+used,\s+([0-9.]+)GB\s+free\)', line)
                if match:
                    used, total, pct, free = match.groups()
                    pct_f = float(pct)
                    bar = "█" * int(pct_f / 4) + "░" * (25 - int(pct_f / 4))
                    
                    color = "red" if pct_f > 90 else "yellow" if pct_f > 75 else "green"
                    
                    table.add_row(
                        "Disk",
                        f"[bold {color}]{pct}%[/bold {color}]",
                        f"[{color}]{bar}[/{color}]",
                        f"{used}GB / {total}GB"
                    )
        
        console.print(table)
    
    @staticmethod
    def _visualize_file_list(data: str) -> None:
        """Visualize file listing"""
        # Try to parse as list first
        if data.startswith('[') and data.endswith(']'):
            try:
                files = eval(data)  # Safe here since we control the input
                if isinstance(files, list):
                    tree = Tree("📁 Files", guide_style="dim")
                    
                    for item in files:
                        if isinstance(item, str):
                            # Detect file vs directory
                            if '.' in item:
                                tree.add(f"📄 [cyan]{item}[/cyan]")
                            else:
                                tree.add(f"📁 [green]{item}/[/green]")
                    
                    console.print(tree)
                    return
            except:
                pass
        
        # Fallback to plain display
        console.print(f"  → {data}", style="cyan")
    
    @staticmethod
    def _visualize_percentage(data: str) -> None:
        """Visualize percentage values"""
        console.print(f"  → {data}", style="cyan")
    
    @staticmethod
    def _visualize_key_value(data: str) -> None:
        """Visualize key-value pairs as a table"""
        lines = [l.strip() for l in data.split("\n") if l.strip() and ":" in l]
        
        if len(lines) < 2:
            console.print(f"  → {data}", style="cyan")
            return
        
        table = Table(box=box.SIMPLE, show_header=False)
        table.add_column("Key", style="cyan", width=20)
        table.add_column("Value", style="white")
        
        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                table.add_row(key.strip(), value.strip())
        
        console.print(table)
    
    @staticmethod
    def _visualize_dict(data: Dict, context: Optional[str]) -> None:
        """Visualize dictionary as formatted JSON or table"""
        # Try to display as table if simple key-value pairs
        if all(isinstance(v, (str, int, float, bool, type(None))) for v in data.values()):
            table = Table(box=box.SIMPLE, show_header=False)
            table.add_column("Key", style="cyan", width=20)
            table.add_column("Value", style="white")
            
            for key, value in data.items():
                table.add_row(str(key), str(value))
            
            console.print(table)
        else:
            # Complex dict - show as formatted JSON
            syntax = Syntax(
                json.dumps(data, indent=2),
                "json",
                theme="monokai",
                word_wrap=True
            )
            console.print(syntax)
    
    @staticmethod
    def _visualize_list(data: List, context: Optional[str]) -> None:
        """Visualize list as table or tree"""
        if not data:
            console.print("  → (empty)", style="dim")
            return
        
        # If list of dicts, create table
        if all(isinstance(item, dict) for item in data):
            # Get all unique keys
            keys = set()
            for item in data:
                keys.update(item.keys())
            keys = sorted(keys)
            
            table = Table(
                box=box.ROUNDED,
                show_header=True,
                header_style="bold magenta"
            )
            
            for key in keys:
                table.add_column(str(key), style="cyan")
            
            for item in data:
                table.add_row(*[str(item.get(key, "")) for key in keys])
            
            console.print(table)
        
        # If list of strings, show as tree
        elif all(isinstance(item, str) for item in data):
            tree = Tree("📋 Items", guide_style="dim")
            for item in data:
                tree.add(f"• [cyan]{item}[/cyan]")
            console.print(tree)
        
        # Otherwise, show as formatted list
        else:
            for i, item in enumerate(data, 1):
                console.print(f"  {i}. {item}", style="cyan")

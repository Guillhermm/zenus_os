"""
Diff Viewer

Shows before/after comparisons with highlighted changes.
Perfect for showing what changed after an operation.
"""

import difflib
from typing import Union, List, Dict, Optional
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.panel import Panel
from io import StringIO
import json


class DiffViewer:
    """
    Visualizes differences between before and after states
    
    Features:
    - Text diff with syntax highlighting
    - File diff
    - Dict/JSON diff
    - List diff
    - Side-by-side or unified view
    """
    
    def __init__(self):
        self.console = Console()
    
    def show_diff(
        self,
        before: Union[str, List, Dict],
        after: Union[str, List, Dict],
        title: Optional[str] = None,
        unified: bool = True,
        context_lines: int = 3
    ) -> str:
        """
        Show diff between before and after
        
        Args:
            before: Before state
            after: After state
            title: Diff title
            unified: Use unified diff (vs side-by-side)
            context_lines: Lines of context around changes
        
        Returns:
            Formatted diff string
        """
        # Detect type and format appropriately
        if isinstance(before, str) and isinstance(after, str):
            return self._show_text_diff(before, after, title, unified, context_lines)
        elif isinstance(before, dict) and isinstance(after, dict):
            return self._show_dict_diff(before, after, title)
        elif isinstance(before, list) and isinstance(after, list):
            return self._show_list_diff(before, after, title)
        else:
            # Convert to JSON and diff
            before_json = json.dumps(before, indent=2)
            after_json = json.dumps(after, indent=2)
            return self._show_text_diff(before_json, after_json, title, unified, context_lines)
    
    def _show_text_diff(
        self,
        before: str,
        after: str,
        title: Optional[str],
        unified: bool,
        context_lines: int
    ) -> str:
        """Show text diff"""
        
        before_lines = before.splitlines(keepends=True)
        after_lines = after.splitlines(keepends=True)
        
        if unified:
            diff = difflib.unified_diff(
                before_lines,
                after_lines,
                fromfile="before",
                tofile="after",
                n=context_lines
            )
        else:
            diff = difflib.ndiff(before_lines, after_lines)
        
        buffer = StringIO()
        console = Console(file=buffer, force_terminal=True, width=120)
        
        if title:
            console.print(f"\n[bold]{title}[/bold]\n")
        
        # Print diff with colors
        for line in diff:
            if line.startswith('+'):
                console.print(Text(line.rstrip(), style="green"))
            elif line.startswith('-'):
                console.print(Text(line.rstrip(), style="red"))
            elif line.startswith('?'):
                console.print(Text(line.rstrip(), style="yellow"))
            elif line.startswith('@@'):
                console.print(Text(line.rstrip(), style="cyan bold"))
            else:
                console.print(Text(line.rstrip(), style="dim"))
        
        return buffer.getvalue()
    
    def _show_dict_diff(
        self,
        before: Dict,
        after: Dict,
        title: Optional[str]
    ) -> str:
        """Show dict diff (added/removed/changed keys)"""
        
        buffer = StringIO()
        console = Console(file=buffer, force_terminal=True, width=120)
        
        if title:
            console.print(f"\n[bold]{title}[/bold]\n")
        
        before_keys = set(before.keys())
        after_keys = set(after.keys())
        
        # Keys added
        added = after_keys - before_keys
        # Keys removed
        removed = before_keys - after_keys
        # Keys in both
        common = before_keys & after_keys
        
        # Show changes
        if added:
            console.print("[green bold]Added:[/green bold]")
            for key in sorted(added):
                console.print(f"  [green]+[/green] {key}: {after[key]}")
        
        if removed:
            console.print("\n[red bold]Removed:[/red bold]")
            for key in sorted(removed):
                console.print(f"  [red]-[/red] {key}: {before[key]}")
        
        # Check for changed values
        changed = []
        for key in common:
            if before[key] != after[key]:
                changed.append(key)
        
        if changed:
            console.print("\n[yellow bold]Changed:[/yellow bold]")
            for key in sorted(changed):
                console.print(f"  [cyan]{key}:[/cyan]")
                console.print(f"    [red]- {before[key]}[/red]")
                console.print(f"    [green]+ {after[key]}[/green]")
        
        if not (added or removed or changed):
            console.print("[dim]No changes[/dim]")
        
        return buffer.getvalue()
    
    def _show_list_diff(
        self,
        before: List,
        after: List,
        title: Optional[str]
    ) -> str:
        """Show list diff"""
        
        buffer = StringIO()
        console = Console(file=buffer, force_terminal=True, width=120)
        
        if title:
            console.print(f"\n[bold]{title}[/bold]\n")
        
        # Convert lists to strings for difflib
        before_str = [str(item) for item in before]
        after_str = [str(item) for item in after]
        
        # Use difflib to find differences
        diff = difflib.ndiff(before_str, after_str)
        
        for line in diff:
            if line.startswith('+ '):
                console.print(f"[green]+ {line[2:]}[/green]")
            elif line.startswith('- '):
                console.print(f"[red]- {line[2:]}[/red]")
            elif line.startswith('? '):
                continue  # Skip hint lines
            else:
                console.print(f"[dim]  {line[2:]}[/dim]")
        
        return buffer.getvalue()
    
    def show_file_diff(
        self,
        before_path: str,
        after_path: str,
        title: Optional[str] = None
    ) -> str:
        """Show diff between two files"""
        
        try:
            with open(before_path, 'r') as f:
                before_content = f.read()
        except Exception as e:
            return f"Error reading {before_path}: {e}"
        
        try:
            with open(after_path, 'r') as f:
                after_content = f.read()
        except Exception as e:
            return f"Error reading {after_path}: {e}"
        
        title = title or f"Diff: {before_path} → {after_path}"
        
        return self._show_text_diff(before_content, after_content, title, unified=True, context_lines=3)
    
    def show_summary(
        self,
        before: Union[str, List, Dict],
        after: Union[str, List, Dict]
    ) -> str:
        """Show quick summary of changes"""
        
        buffer = StringIO()
        console = Console(file=buffer, force_terminal=True, width=120)
        
        if isinstance(before, dict) and isinstance(after, dict):
            added = len(set(after.keys()) - set(before.keys()))
            removed = len(set(before.keys()) - set(after.keys()))
            common = set(before.keys()) & set(after.keys())
            changed = sum(1 for k in common if before[k] != after[k])
            
            console.print(f"[green]+{added}[/green] added, [red]-{removed}[/red] removed, [yellow]~{changed}[/yellow] changed")
        
        elif isinstance(before, list) and isinstance(after, list):
            before_set = set(before)
            after_set = set(after)
            added = len(after_set - before_set)
            removed = len(before_set - after_set)
            
            console.print(f"[green]+{added}[/green] added, [red]-{removed}[/red] removed")
        
        elif isinstance(before, str) and isinstance(after, str):
            before_lines = before.splitlines()
            after_lines = after.splitlines()
            
            diff = list(difflib.ndiff(before_lines, after_lines))
            added = sum(1 for line in diff if line.startswith('+'))
            removed = sum(1 for line in diff if line.startswith('-'))
            
            console.print(f"[green]+{added}[/green] lines added, [red]-{removed}[/red] lines removed")
        
        return buffer.getvalue()


def show_diff(before, after, **kwargs) -> str:
    """
    Quick function to show diff
    
    Returns:
        Formatted diff string
    """
    viewer = DiffViewer()
    return viewer.show_diff(before, after, **kwargs)

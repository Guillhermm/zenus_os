"""
Progress Display System

Real-time progress indicators for operations:
- Spinners for thinking/planning
- Progress bars for file operations
- Step counters for iterations
- Elapsed time tracking
"""

import time
import sys
from typing import Optional, Callable
from contextlib import contextmanager
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeElapsedColumn,
    TimeRemainingColumn
)
from rich.live import Live
from rich.table import Table
from rich.panel import Panel


console = Console()


class ProgressTracker:
    """
    Tracks and displays progress for various operations
    
    Features:
    - Spinners for indeterminate operations
    - Progress bars for determinate operations
    - Time tracking
    - Nested progress (e.g., batch > iteration > step)
    """
    
    def __init__(self):
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console
        )
        self.active_tasks = {}
        self.start_times = {}
    
    @contextmanager
    def thinking(self, message: str = "Thinking..."):
        """
        Context manager for showing thinking spinner
        
        Args:
            message: Message to display
        
        Example:
            with progress.thinking("Analyzing dependencies"):
                # Do work
                pass
        """
        task_id = self.progress.add_task(f"[cyan]{message}[/cyan]", total=None)
        
        try:
            with self.progress:
                yield
        finally:
            self.progress.remove_task(task_id)
    
    @contextmanager
    def batch(self, total_iterations: int, batch_number: int = 1):
        """
        Context manager for batch progress
        
        Args:
            total_iterations: Total iterations in batch
            batch_number: Current batch number
        
        Example:
            with progress.batch(12, batch_number=2) as update:
                for i in range(12):
                    # Do work
                    update(i + 1)
        """
        task_id = self.progress.add_task(
            f"[bold cyan]Batch {batch_number}[/bold cyan]",
            total=total_iterations
        )
        
        def update(completed: int):
            self.progress.update(task_id, completed=completed)
        
        try:
            with self.progress:
                yield update
        finally:
            self.progress.remove_task(task_id)
    
    @contextmanager
    def step(self, description: str, total: Optional[int] = None):
        """
        Context manager for step progress
        
        Args:
            description: Step description
            total: Total items (None for indeterminate)
        
        Example:
            with progress.step("Moving files", total=10) as update:
                for i in range(10):
                    # Move file
                    update(i + 1)
        """
        task_id = self.progress.add_task(
            f"[yellow]{description}[/yellow]",
            total=total
        )
        
        def update(completed: int):
            self.progress.update(task_id, completed=completed)
        
        try:
            with self.progress:
                yield update
        finally:
            self.progress.remove_task(task_id)
    
    def start_timer(self, name: str) -> None:
        """Start a named timer"""
        self.start_times[name] = time.time()
    
    def stop_timer(self, name: str) -> float:
        """
        Stop a named timer and return elapsed time
        
        Args:
            name: Timer name
        
        Returns:
            Elapsed time in seconds
        """
        if name not in self.start_times:
            return 0.0
        
        elapsed = time.time() - self.start_times[name]
        del self.start_times[name]
        return elapsed
    
    def get_elapsed(self, name: str) -> float:
        """
        Get elapsed time for running timer
        
        Args:
            name: Timer name
        
        Returns:
            Elapsed time in seconds (0 if not found)
        """
        if name not in self.start_times:
            return 0.0
        
        return time.time() - self.start_times[name]


class StreamingDisplay:
    """
    Streaming display for iterative execution
    
    Shows:
    - Current iteration number
    - Current step being executed
    - Live results as they come in
    - Elapsed time
    """
    
    def __init__(self):
        self.console = Console()
        self.start_time = None
        self.current_iteration = 0
        self.current_batch = 1
        self.total_steps = 0
    
    def start(self, initial_message: str = "Starting execution..."):
        """Start streaming display"""
        self.start_time = time.time()
        self.console.print(f"\n[bold cyan]{initial_message}[/bold cyan]")
    
    def new_iteration(self, iteration: int, batch: int, max_per_batch: int):
        """Display new iteration header"""
        self.current_iteration = iteration
        self.current_batch = batch
        iteration_in_batch = ((iteration - 1) % max_per_batch) + 1
        
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        self.console.print()
        self.console.print(
            f"[bold cyan]═══ Iteration {iteration} "
            f"(Batch {batch}, {iteration_in_batch}/{max_per_batch}) "
            f"[{elapsed:.1f}s] ═══[/bold cyan]"
        )
    
    def show_goal(self, goal: str):
        """Display iteration goal"""
        self.console.print(f"[yellow]→ Goal:[/yellow] {goal}")
    
    def start_step(self, step_num: int, tool: str, action: str):
        """Display step start"""
        self.console.print(f"  [{step_num}] {tool}.{action}", end="", flush=True)
    
    def complete_step(self, result: str, success: bool = True):
        """Display step completion"""
        if success:
            truncated = result[:100] + "..." if len(result) > 100 else result
            self.console.print(f" → [green]{truncated}[/green]")
        else:
            self.console.print(f" → [red]✗ {result}[/red]")
    
    def show_reflection(self, achieved: bool, confidence: float, reasoning: str):
        """Display goal reflection"""
        self.console.print()
        
        if achieved:
            self.console.print(f"[bold green]✓ Goal Achieved![/bold green]")
        else:
            self.console.print(f"[yellow]⟳ Goal not yet achieved[/yellow]")
            self.console.print(f"[dim]Confidence: {confidence:.0%}[/dim]")
        
        self.console.print(f"[dim]Reasoning: {reasoning}[/dim]")
    
    def batch_complete(self, batch_num: int, iterations_in_batch: int):
        """Display batch completion"""
        self.console.print()
        self.console.print(
            f"[yellow]⟳ Batch {batch_num} complete ({iterations_in_batch} iterations)[/yellow]"
        )
        self.console.print(f"[dim]Goal not yet achieved. Continuing with batch {batch_num + 1}...[/dim]")
    
    def finish(self, total_iterations: int, total_batches: int):
        """Display final completion"""
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        self.console.print()
        self.console.print(
            f"[bold green]✓ Task completed in {total_iterations} iteration(s) "
            f"across {total_batches} batch(es) ({elapsed:.1f}s)[/bold green]"
        )


# Global instances
_progress_tracker: Optional[ProgressTracker] = None
_streaming_display: Optional[StreamingDisplay] = None


def get_progress_tracker() -> ProgressTracker:
    """Get singleton progress tracker"""
    global _progress_tracker
    if _progress_tracker is None:
        _progress_tracker = ProgressTracker()
    return _progress_tracker


def get_streaming_display() -> StreamingDisplay:
    """Get singleton streaming display"""
    global _streaming_display
    if _streaming_display is None:
        _streaming_display = StreamingDisplay()
    return _streaming_display


# Backward compatibility alias
ProgressIndicator = ProgressTracker

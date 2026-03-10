"""
Streaming Output Handler

Provides real-time feedback during LLM inference and task execution.
"""

import sys
import threading
import time
from typing import Optional, Callable
from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn


console = Console()


class StreamHandler:
    """
    Handles streaming output for LLM and tool execution
    
    Capabilities:
    - Stream LLM tokens as they arrive
    - Show progress bars for long operations
    - Display spinners for indeterminate tasks
    - Cancelable operations (Ctrl+C handling)
    """
    
    def __init__(self):
        self.cancelled = False
        self._cancel_callbacks = []
    
    def register_cancel_callback(self, callback: Callable):
        """Register callback to be called on cancel"""
        self._cancel_callbacks.append(callback)
    
    def cancel(self):
        """Cancel current operation"""
        self.cancelled = True
        for callback in self._cancel_callbacks:
            try:
                callback()
            except:
                pass
    
    def stream_llm_tokens(self, stream_iterator, prefix: str = ""):
        """
        Stream LLM tokens in real-time
        
        Args:
            stream_iterator: Iterator of token chunks
            prefix: Prefix text to display before tokens
        
        Returns:
            Complete text
        """
        if prefix:
            console.print(f"[cyan]{prefix}[/cyan]", end="")
        
        complete_text = ""
        
        try:
            for chunk in stream_iterator:
                if self.cancelled:
                    console.print("\n[yellow]Cancelled by user[/yellow]")
                    break
                
                # Extract token from chunk (format depends on provider)
                if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        token = delta.content
                        console.print(token, end="")
                        sys.stdout.flush()
                        complete_text += token
        
        except KeyboardInterrupt:
            self.cancel()
            console.print("\n[yellow]Cancelled by user[/yellow]")
        
        console.print()  # New line
        return complete_text
    
    def show_spinner(self, text: str, duration: Optional[float] = None):
        """
        Show spinner for indeterminate task
        
        Args:
            text: Text to display
            duration: Auto-stop after duration (None = manual stop)
        
        Returns:
            Context manager
        """
        return Live(
            Spinner("dots", text=f"[cyan]{text}[/cyan]"),
            console=console,
            transient=True
        )
    
    def show_progress(
        self,
        total: int,
        description: str = "Processing"
    ) -> Progress:
        """
        Create progress bar
        
        Args:
            total: Total items
            description: Progress description
        
        Returns:
            Progress object with task ID
        """
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        )
        
        task_id = progress.add_task(description, total=total)
        
        return progress, task_id
    
    def stream_step_execution(self, step_number: int, tool: str, action: str):
        """
        Display step execution start
        
        Args:
            step_number: Step number
            tool: Tool name
            action: Action name
        """
        console.print(f"[bold cyan]Step {step_number}:[/bold cyan] {tool}.{action}", end=" ")
        sys.stdout.flush()
    
    def stream_step_result(self, result: str, success: bool = True):
        """
        Display step execution result
        
        Args:
            result: Result string
            success: Whether step succeeded
        """
        if success:
            console.print(f"[green]✓[/green] {result[:100]}")
        else:
            console.print(f"[red]✗[/red] {result[:100]}")


class CancelableOperation:
    """Context manager for cancelable operations"""
    
    def __init__(self, stream_handler: StreamHandler):
        self.stream_handler = stream_handler
        self._original_sigint = None
    
    def __enter__(self):
        import signal
        
        # Save original handler
        self._original_sigint = signal.getsignal(signal.SIGINT)
        
        # Set our handler
        def handler(sig, frame):
            self.stream_handler.cancel()
        
        signal.signal(signal.SIGINT, handler)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        import signal
        
        # Restore original handler
        if self._original_sigint:
            signal.signal(signal.SIGINT, self._original_sigint)
        
        # Don't suppress KeyboardInterrupt
        return False


# Global stream handler
_global_handler = StreamHandler()


def get_stream_handler() -> StreamHandler:
    """Get global stream handler"""
    return _global_handler

"""
Zenus OS Dashboard

Main TUI application with multiple views and real-time updates.
Fully wired to Zenus orchestrator and memory systems.
Polished with advanced features.
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual.widgets import (
    Header, Footer, Static, Button, Input, 
    DataTable, TabbedContent, TabPane, Log,
    Label, ProgressBar, RichLog, LoadingIndicator
)
from textual.binding import Binding
from textual.worker import Worker, WorkerState
from textual.message import Message
from rich.text import Text
from rich.table import Table as RichTable
from rich.panel import Panel
from rich.tree import Tree
from datetime import datetime
import asyncio
from typing import Optional, List
from collections import deque

# Zenus imports
from zenus_core.cli.orchestrator import Orchestrator
from zenus_core.memory.action_tracker import get_action_tracker
from zenus_core.brain.pattern_detector import PatternDetector
from zenus_core.memory.world_model import WorldModel


class StatusBar(Static):
    """Status bar showing system state"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.session_start = datetime.now()
        self.command_count = 0
        self.last_result = "Ready"
    
    def update_status(self, command_count: int = None, last_result: str = None):
        """Update status information"""
        if command_count is not None:
            self.command_count = command_count
        if last_result is not None:
            self.last_result = last_result
        
        # Calculate session duration
        duration = datetime.now() - self.session_start
        minutes = int(duration.total_seconds() / 60)
        
        # Build status text with emoji indicators
        status_text = Text()
        status_text.append("Status: ", style="bold")
        
        # Smart status styling
        if "Executing" in self.last_result:
            status_text.append(self.last_result, style="bold yellow")
        elif "✓" in self.last_result or "Success" in self.last_result:
            status_text.append(self.last_result, style="bold green")
        elif "✗" in self.last_result or "Failed" in self.last_result:
            status_text.append(self.last_result, style="bold red")
        else:
            status_text.append(self.last_result, style="cyan")
        
        status_text.append(" | ", style="dim")
        status_text.append(f"Commands: {self.command_count}", style="cyan")
        status_text.append(" | ", style="dim")
        status_text.append(f"Session: {minutes}m", style="dim")
        
        self.update(status_text)


class CommandInput(Container):
    """Command input area with action buttons and history"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.command_history: deque = deque(maxlen=100)
        self.history_index = -1
    
    def compose(self) -> ComposeResult:
        with Horizontal(id="command-input-container"):
            yield Input(placeholder="Enter command... (↑↓ for history)", id="command-input")
            yield Button("Execute", variant="primary", id="execute-btn")
            yield Button("Dry Run", variant="default", id="dry-run-btn")
            yield Button("Iterative", variant="default", id="iterative-btn")
            yield Button("Clear Log", variant="warning", id="clear-log-btn")
    
    def add_to_history(self, command: str):
        """Add command to history"""
        if command and (not self.command_history or self.command_history[-1] != command):
            self.command_history.append(command)
        self.history_index = -1
    
    def get_previous_command(self) -> Optional[str]:
        """Get previous command from history"""
        if not self.command_history:
            return None
        
        if self.history_index == -1:
            self.history_index = len(self.command_history) - 1
        elif self.history_index > 0:
            self.history_index -= 1
        
        return self.command_history[self.history_index] if self.history_index >= 0 else None
    
    def get_next_command(self) -> Optional[str]:
        """Get next command from history"""
        if not self.command_history or self.history_index == -1:
            return ""
        
        self.history_index += 1
        
        if self.history_index >= len(self.command_history):
            self.history_index = -1
            return ""
        
        return self.command_history[self.history_index]


class ExecutionLog(Container):
    """Live execution log viewer with real-time updates"""
    
    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Label("Recent Executions", id="log-title")
            yield LoadingIndicator(id="execution-spinner")
        yield RichLog(id="execution-log", highlight=True, markup=True)
    
    def on_mount(self):
        """Hide spinner initially"""
        spinner = self.query_one("#execution-spinner", LoadingIndicator)
        spinner.display = False
    
    def show_spinner(self):
        """Show loading spinner"""
        spinner = self.query_one("#execution-spinner", LoadingIndicator)
        spinner.display = True
    
    def hide_spinner(self):
        """Hide loading spinner"""
        spinner = self.query_one("#execution-spinner", LoadingIndicator)
        spinner.display = False
    
    def add_execution(self, command: str, result: str, duration: float, success: bool):
        """Add execution to log"""
        log = self.query_one("#execution-log", RichLog)
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        status_icon = "✓" if success else "✗"
        status_style = "green" if success else "red"
        
        log.write(f"[dim][{timestamp}][/dim] [cyan]{command}[/cyan] [{status_style}]{status_icon}[/{status_style}] [dim]{duration:.1f}s[/dim]")
        
        # Show result summary (first few lines)
        if result:
            lines = result.split('\n')[:3]  # First 3 lines
            for line in lines:
                if line.strip():
                    log.write(f"  [dim]→[/dim] {line[:100]}")
    
    def add_progress(self, message: str):
        """Add progress message during execution"""
        log = self.query_one("#execution-log", RichLog)
        log.write(f"[yellow]⏳ {message}[/yellow]")
    
    def clear_log(self):
        """Clear execution log"""
        log = self.query_one("#execution-log", RichLog)
        log.clear()


class PatternSuggestion(Container):
    """Pattern suggestion panel"""
    
    def compose(self) -> ComposeResult:
        yield Label("💡 Pattern Detected", id="pattern-title")
        yield Static("", id="pattern-content")
    
    def show_pattern(self, description: str, suggestion: str):
        """Display a detected pattern"""
        content = self.query_one("#pattern-content", Static)
        
        text = Text()
        text.append(description, style="yellow")
        text.append("\n\n💡 Suggestion: ", style="bold cyan")
        text.append(suggestion, style="cyan")
        
        content.update(text)
        self.display = True
    
    def hide(self):
        """Hide pattern panel"""
        self.display = False


class HistoryView(ScrollableContainer):
    """Command history viewer with search"""
    
    def compose(self) -> ComposeResult:
        yield Input(placeholder="Search history...", id="history-search")
        yield DataTable(id="history-table")
    
    def on_mount(self):
        """Initialize history table"""
        table = self.query_one("#history-table", DataTable)
        table.add_columns("Time", "Command", "Status", "Duration")
        table.cursor_type = "row"
        self.refresh_history()
    
    def on_input_changed(self, event: Input.Changed):
        """Filter history on search"""
        if event.input.id == "history-search":
            self.refresh_history(search=event.value)
    
    def refresh_history(self, search: str = ""):
        """Load history from action tracker"""
        table = self.query_one("#history-table", DataTable)
        table.clear()
        
        try:
            tracker = get_action_tracker()
            transactions = tracker.get_recent_transactions(limit=100)
            
            for txn in reversed(transactions):  # Most recent first
                timestamp = txn.get('timestamp', 'Unknown')
                
                # Parse ISO timestamp
                try:
                    dt = datetime.fromisoformat(timestamp)
                    time_str = dt.strftime("%m/%d %H:%M")
                except:
                    time_str = timestamp[:16]
                
                # Get command
                actions = txn.get('actions', [])
                if actions:
                    command = f"{actions[0]['tool']}.{actions[0]['operation']}"
                else:
                    command = "Unknown"
                
                # Filter by search
                if search and search.lower() not in command.lower():
                    continue
                
                success = txn.get('success', True)
                status = "✓" if success else "✗"
                
                duration = txn.get('duration', 0)
                duration_str = f"{duration:.1f}s" if duration else "N/A"
                
                table.add_row(time_str, command, status, duration_str)
        except Exception as e:
            table.add_row("Error", f"Failed to load history: {e}", "", "")


class MemoryView(ScrollableContainer):
    """Memory and pattern viewer"""
    
    def compose(self) -> ComposeResult:
        yield RichLog(id="memory-log", highlight=True, markup=True)
    
    def on_mount(self):
        """Load memory and patterns"""
        self.refresh_memory()
    
    def refresh_memory(self):
        """Display patterns and world model state"""
        log = self.query_one("#memory-log", RichLog)
        log.clear()
        
        log.write("[bold cyan]🧠 Detected Patterns[/bold cyan]\n")
        
        try:
            # Get patterns
            tracker = get_action_tracker()
            history = tracker.get_recent_transactions(limit=100)
            
            detector = PatternDetector()
            patterns = detector.detect_patterns(history, lookback_days=30)
            
            if patterns:
                for i, pattern in enumerate(patterns[:10], 1):  # Top 10
                    log.write(f"\n[yellow]{i}. {pattern.pattern_type.title()}[/yellow]")
                    log.write(f"   {pattern.description}")
                    log.write(f"   [dim]Confidence: {pattern.confidence:.0%} | Occurrences: {pattern.occurrences}[/dim]")
                    
                    if pattern.suggested_cron:
                        log.write(f"   [green]💡 Suggested cron: {pattern.suggested_cron}[/green]")
            else:
                log.write("[dim]No patterns detected yet. Keep using Zenus![/dim]")
            
            # World model state
            log.write("\n\n[bold cyan]🌍 World Model[/bold cyan]\n")
            
            try:
                world_model = WorldModel()
                facts = world_model.get_recent_facts(limit=10)
                
                if facts:
                    for fact in facts:
                        log.write(f"• {fact['category']}: {fact['key']} = {fact['value']}")
                else:
                    log.write("[dim]No facts recorded yet[/dim]")
            except Exception as e:
                log.write(f"[dim]World model unavailable: {e}[/dim]")
                
        except Exception as e:
            log.write(f"[red]Error loading memory: {e}[/red]")


class ExplainView(ScrollableContainer):
    """Explainability dashboard with detailed step breakdown"""
    
    def compose(self) -> ComposeResult:
        yield RichLog(id="explain-log", highlight=True, markup=True)
    
    def show_explanation(self, user_input: str, result: str, steps: Optional[List] = None):
        """Display detailed explanation for last command"""
        log = self.query_one("#explain-log", RichLog)
        log.clear()
        
        log.write("[bold cyan]📊 Command Explanation[/bold cyan]\n")
        log.write(f"[yellow]Input:[/yellow] {user_input}\n")
        
        # Show steps if available
        if steps:
            log.write("\n[bold cyan]📝 Execution Steps:[/bold cyan]\n")
            for i, step in enumerate(steps, 1):
                log.write(f"\n[cyan]{i}. {step.get('tool', 'Unknown')}.{step.get('action', 'Unknown')}[/cyan]")
                if step.get('reasoning'):
                    log.write(f"   [dim]{step['reasoning']}[/dim]")
                if step.get('confidence'):
                    log.write(f"   [dim]Confidence: {step['confidence']:.0%}[/dim]")
        
        # Show result
        log.write(f"\n[yellow]Result:[/yellow]")
        all_lines = result.split('\n')
        result_lines = all_lines[:10]  # First 10 lines
        for line in result_lines:
            if line.strip():
                log.write(f"  {line}")
        
        if len(all_lines) > 10:
            remaining = len(all_lines) - 10
            log.write(f"\n  [dim]... ({remaining} more lines)[/dim]")


class RollbackPanel(Container):
    """Rollback control panel"""
    
    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Button("⎌ Rollback Last", variant="error", id="rollback-btn")
            yield Static("", id="rollback-status")
    
    def show_rollback_status(self, message: str, success: bool):
        """Show rollback result"""
        status = self.query_one("#rollback-status", Static)
        style = "green" if success else "red"
        status.update(f"[{style}]{message}[/{style}]")


class ZenusDashboard(App):
    """Zenus OS TUI Dashboard - Polished Edition"""
    
    CSS = """
    #status-bar {
        dock: top;
        height: 1;
        background: $panel;
        color: $text;
        padding: 0 1;
    }
    
    #command-input-container {
        dock: bottom;
        height: 3;
        background: $panel;
        padding: 0 1;
    }
    
    #command-input {
        width: 50%;
    }
    
    #execution-log-container {
        height: 60%;
        border: solid $primary;
    }
    
    #execution-spinner {
        margin-left: 1;
    }
    
    #pattern-suggestion {
        height: 40%;
        border: solid yellow;
        background: $panel;
        padding: 1;
    }
    
    #history-search {
        margin: 0 0 1 0;
    }
    
    #history-table {
        height: 1fr;
    }
    
    #memory-log {
        height: 100%;
    }
    
    #explain-log {
        height: 100%;
    }
    
    Button {
        margin: 0 1;
    }
    
    LoadingIndicator {
        height: 1;
        width: auto;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=True),
        Binding("q", "quit", "Quit", show=False),
        Binding("f1", "tab('execution')", "Execution", show=True),
        Binding("f2", "tab('history')", "History", show=True),
        Binding("f3", "tab('memory')", "Memory", show=True),
        Binding("f4", "tab('explain')", "Explain", show=True),
        Binding("f5", "refresh", "Refresh", show=True),
        Binding("ctrl+r", "rollback", "Rollback", show=True),
    ]
    
    def __init__(self):
        super().__init__()
        self.title = "Zenus OS Dashboard"
        self.sub_title = "AI-Powered System Management"
        
        # Initialize Zenus orchestrator
        self.orchestrator = Orchestrator(
            adaptive=True,
            use_memory=True,
            use_sandbox=True,
            show_progress=False,  # We'll handle progress in TUI
            enable_parallel=True
        )
        
        self.command_count = 0
        self.last_command = None
        self.last_result = None
        self.last_steps = None
    
    def compose(self) -> ComposeResult:
        """Create child widgets"""
        yield Header()
        
        # Status bar
        yield StatusBar(id="status-bar")
        
        # Main content area with tabs
        with TabbedContent(id="main-tabs"):
            with TabPane("Execution", id="execution-tab"):
                yield ExecutionLog(id="execution-log-container")
                yield PatternSuggestion(id="pattern-suggestion")
            
            with TabPane("History", id="history-tab"):
                yield HistoryView(id="history-view")
            
            with TabPane("Memory", id="memory-tab"):
                yield MemoryView(id="memory-view")
            
            with TabPane("Explain", id="explain-tab"):
                yield ExplainView(id="explain-view")
        
        # Command input area
        yield CommandInput(id="command-input-area")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize after mounting"""
        # Hide pattern suggestion initially
        pattern = self.query_one("#pattern-suggestion", PatternSuggestion)
        pattern.display = False
        
        # Update status
        status_bar = self.query_one("#status-bar", StatusBar)
        status_bar.update_status(0, "Ready ✓")
        
        # Focus input
        input_widget = self.query_one("#command-input", Input)
        input_widget.focus()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        button_id = event.button.id
        
        if button_id == "execute-btn":
            self.execute_command(dry_run=False, iterative=False)
        elif button_id == "dry-run-btn":
            self.execute_command(dry_run=True, iterative=False)
        elif button_id == "iterative-btn":
            self.execute_command(dry_run=False, iterative=True)
        elif button_id == "clear-log-btn":
            self.action_clear_log()
        elif button_id == "rollback-btn":
            self.action_rollback()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in input field"""
        if event.input.id == "command-input":
            self.execute_command(dry_run=False, iterative=False)
    
    def on_key(self, event) -> None:
        """Handle special keys"""
        input_widget = self.query_one("#command-input", Input)
        command_input_container = self.query_one("#command-input-area", CommandInput)
        
        # Only handle arrow keys when input is focused
        if self.focused == input_widget:
            if event.key == "up":
                prev_cmd = command_input_container.get_previous_command()
                if prev_cmd:
                    input_widget.value = prev_cmd
                    input_widget.cursor_position = len(prev_cmd)
                event.prevent_default()
            elif event.key == "down":
                next_cmd = command_input_container.get_next_command()
                if next_cmd is not None:
                    input_widget.value = next_cmd
                    input_widget.cursor_position = len(next_cmd)
                event.prevent_default()
    
    def execute_command(self, dry_run: bool = False, iterative: bool = False):
        """Execute command in background worker"""
        # Get command from input
        input_widget = self.query_one("#command-input", Input)
        command = input_widget.value.strip()
        
        if not command:
            return
        
        # Add to history
        command_input_container = self.query_one("#command-input-area", CommandInput)
        command_input_container.add_to_history(command)
        
        # Clear input
        input_widget.value = ""
        
        # Update status and show spinner
        status_bar = self.query_one("#status-bar", StatusBar)
        status_bar.update_status(last_result="Executing... ⏳")
        
        exec_log = self.query_one("#execution-log-container", ExecutionLog)
        exec_log.show_spinner()
        
        # Store for explain view
        self.last_command = command
        
        # Run in background worker
        self.run_worker(
            self._execute_async(command, dry_run, iterative),
            name=f"execute-{datetime.now().timestamp()}"
        )
    
    async def _execute_async(self, command: str, dry_run: bool, iterative: bool):
        """Execute command asynchronously"""
        start_time = datetime.now()
        success = False
        result = ""
        
        try:
            # Execute via orchestrator (run in thread pool to avoid blocking)
            loop = asyncio.get_event_loop()
            
            if iterative:
                result = await loop.run_in_executor(
                    None,  # Use default executor
                    lambda: self.orchestrator.execute_iterative(
                        command,
                        max_iterations=12,
                        dry_run=dry_run
                    )
                )
            else:
                result = await loop.run_in_executor(
                    None,
                    lambda: self.orchestrator.execute_command(
                        command,
                        dry_run=dry_run,
                        force_oneshot=True
                    )
                )
            
            success = True
            self.last_result = result
            
        except Exception as e:
            result = f"Error: {str(e)}"
            success = False
            self.last_result = result
        
        finally:
            # Calculate duration
            duration = (datetime.now() - start_time).total_seconds()
            
            # Update UI directly (we're already in async context on event loop)
            self._update_after_execution(command, result, duration, success)
    
    def _update_after_execution(self, command: str, result: str, duration: float, success: bool):
        """Update UI after command execution (on main thread)"""
        # Increment command count
        self.command_count += 1
        
        # Update status bar
        status_bar = self.query_one("#status-bar", StatusBar)
        status_text = "Success ✓" if success else "Failed ✗"
        status_bar.update_status(self.command_count, status_text)
        
        # Hide spinner and add to execution log
        exec_log = self.query_one("#execution-log-container", ExecutionLog)
        exec_log.hide_spinner()
        exec_log.add_execution(command, result, duration, success)
        
        # Check for patterns (every 10 commands)
        if self.command_count % 10 == 0:
            self._check_patterns()
        
        # Refresh history and memory tabs
        try:
            history_view = self.query_one("#history-view", HistoryView)
            history_view.refresh_history()
        except:
            pass
        
        try:
            memory_view = self.query_one("#memory-view", MemoryView)
            memory_view.refresh_memory()
        except:
            pass
        
        # Update explain view
        try:
            explain_view = self.query_one("#explain-view", ExplainView)
            explain_view.show_explanation(command, result, self.last_steps)
        except:
            pass
    
    def _check_patterns(self):
        """Check for patterns and show suggestions"""
        try:
            tracker = get_action_tracker()
            history = tracker.get_recent_transactions(limit=100)
            
            detector = PatternDetector()
            patterns = detector.detect_patterns(history, lookback_days=30)
            
            # Show top pattern if found
            if patterns:
                pattern = patterns[0]  # Highest confidence
                
                suggestion = pattern.description
                if pattern.suggested_cron:
                    suggestion += f"\n\nTry: zenus schedule '{pattern.suggested_cron}' ..."
                
                pattern_widget = self.query_one("#pattern-suggestion", PatternSuggestion)
                pattern_widget.show_pattern(pattern.description, suggestion)
        except Exception as e:
            pass  # Silent fail for pattern detection
    
    def action_tab(self, tab_name: str) -> None:
        """Switch to a specific tab"""
        tabs = self.query_one("#main-tabs", TabbedContent)
        tabs.active = f"{tab_name}-tab"
    
    def action_refresh(self) -> None:
        """Refresh current tab"""
        tabs = self.query_one("#main-tabs", TabbedContent)
        active_tab = tabs.active
        
        if active_tab == "history-tab":
            history_view = self.query_one("#history-view", HistoryView)
            history_view.refresh_history()
        elif active_tab == "memory-tab":
            memory_view = self.query_one("#memory-view", MemoryView)
            memory_view.refresh_memory()
    
    def action_clear_log(self) -> None:
        """Clear execution log"""
        exec_log = self.query_one("#execution-log-container", ExecutionLog)
        exec_log.clear_log()
    
    def action_rollback(self) -> None:
        """Rollback last command"""
        # TODO: Implement rollback via action_tracker
        status_bar = self.query_one("#status-bar", StatusBar)
        status_bar.update_status(last_result="Rollback not yet implemented")


def main():
    """Entry point for TUI"""
    app = ZenusDashboard()
    app.run()


if __name__ == "__main__":
    main()

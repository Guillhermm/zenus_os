"""
Zenus OS Dashboard

Main TUI application with multiple views and real-time updates.
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import (
    Header, Footer, Static, Button, Input, 
    DataTable, TabbedContent, TabPane, Log,
    Label, ProgressBar
)
from textual.binding import Binding
from rich.text import Text
from datetime import datetime
import asyncio


class StatusBar(Static):
    """Status bar showing system state"""
    
    def __init__(self):
        super().__init__()
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
        
        # Build status text
        status_text = Text()
        status_text.append("Status: ", style="bold")
        status_text.append(self.last_result, style="green" if "✓" in self.last_result else "yellow")
        status_text.append(" | Session: ", style="dim")
        status_text.append(f"{minutes}m", style="cyan")
        status_text.append(" | Commands: ", style="dim")
        status_text.append(str(self.command_count), style="cyan")
        
        self.update(status_text)


class CommandInput(Container):
    """Command input area with action buttons"""
    
    def compose(self) -> ComposeResult:
        with Horizontal(id="command-input-container"):
            yield Input(placeholder="Enter command...", id="command-input")
            yield Button("Execute", variant="primary", id="execute-btn")
            yield Button("Dry Run", variant="default", id="dry-run-btn")
            yield Button("Iterative", variant="default", id="iterative-btn")


class ExecutionLog(Container):
    """Live execution log viewer"""
    
    def compose(self) -> ComposeResult:
        yield Label("Recent Executions", id="log-title")
        yield Log(id="execution-log", auto_scroll=True)
    
    def add_execution(self, command: str, result: str, duration: float, success: bool):
        """Add execution to log"""
        log = self.query_one("#execution-log", Log)
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        status_icon = "✓" if success else "✗"
        status_style = "green" if success else "red"
        
        log_text = Text()
        log_text.append(f"[{timestamp}] ", style="dim")
        log_text.append(command, style="cyan")
        log_text.append(f" {status_icon} ", style=status_style)
        log_text.append(f"{duration:.1f}s", style="dim")
        
        log.write(log_text)


class PatternSuggestion(Container):
    """Pattern suggestion panel"""
    
    def compose(self) -> ComposeResult:
        yield Label("💡 Pattern Detected", id="pattern-title")
        yield Static("", id="pattern-message")
        with Horizontal(id="pattern-actions"):
            yield Button("Create Automation", variant="success", id="pattern-create-btn")
            yield Button("Dismiss", variant="default", id="pattern-dismiss-btn")
    
    def show_pattern(self, description: str, cron_expr: str = None):
        """Show pattern suggestion"""
        message = self.query_one("#pattern-message", Static)
        
        text = Text(description, style="yellow")
        if cron_expr:
            text.append(f"\nCron: {cron_expr}", style="dim")
        
        message.update(text)
        self.display = True
    
    def hide_pattern(self):
        """Hide pattern suggestion"""
        self.display = False


class HistoryView(Container):
    """Execution history viewer"""
    
    def compose(self) -> ComposeResult:
        yield Label("Execution History", id="history-title")
        table = DataTable(id="history-table")
        table.add_columns("Time", "Command", "Status", "Duration")
        yield table
    
    def add_history_item(self, command: str, status: str, duration: float):
        """Add item to history"""
        table = self.query_one("#history-table", DataTable)
        timestamp = datetime.now().strftime("%H:%M:%S")
        table.add_row(timestamp, command, status, f"{duration:.1f}s")


class MemoryView(Container):
    """Memory explorer view"""
    
    def compose(self) -> ComposeResult:
        yield Label("Memory & Patterns", id="memory-title")
        yield Static("Session memory, patterns, and learning data", id="memory-content")


class ExplainView(Container):
    """Explainability viewer"""
    
    def compose(self) -> ComposeResult:
        yield Label("Last Execution Explained", id="explain-title")
        yield Log(id="explain-content", auto_scroll=True)
    
    def show_explanation(self, explanation_text: str):
        """Show execution explanation"""
        log = self.query_one("#explain-content", Log)
        log.clear()
        log.write(explanation_text)


class ZenusDashboard(App):
    """
    Zenus OS Dashboard
    
    Modern TUI with:
    - Real-time execution monitoring
    - Command history
    - Pattern suggestions
    - Memory explorer
    - Explainability viewer
    """
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #status-bar {
        dock: top;
        height: 1;
        background: $boost;
        color: $text;
        padding: 0 1;
    }
    
    #main-container {
        height: 100%;
    }
    
    #command-input-container {
        dock: bottom;
        height: 3;
        background: $panel;
        padding: 0 1;
    }
    
    #command-input {
        width: 3fr;
    }
    
    Button {
        margin: 0 1;
    }
    
    #execution-log {
        height: 50%;
        border: solid $primary;
        margin: 1;
    }
    
    #pattern-suggestion {
        height: 8;
        background: $warning 20%;
        border: solid $warning;
        margin: 1;
        padding: 1;
    }
    
    #pattern-title {
        text-style: bold;
        color: $warning;
    }
    
    #history-table {
        height: 100%;
    }
    
    DataTable {
        height: 100%;
    }
    
    TabbedContent {
        height: 100%;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("ctrl+c", "quit", "Quit", show=False),
        Binding("f1", "tab('execution')", "Execution"),
        Binding("f2", "tab('history')", "History"),
        Binding("f3", "tab('memory')", "Memory"),
        Binding("f4", "tab('explain')", "Explain"),
    ]
    
    def __init__(self):
        super().__init__()
        self.title = "Zenus OS Dashboard"
        self.sub_title = "AI-Powered System Management"
    
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
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        button_id = event.button.id
        
        if button_id == "execute-btn":
            self.execute_command(dry_run=False, iterative=False)
        elif button_id == "dry-run-btn":
            self.execute_command(dry_run=True, iterative=False)
        elif button_id == "iterative-btn":
            self.execute_command(dry_run=False, iterative=True)
        elif button_id == "pattern-create-btn":
            self.create_automation()
        elif button_id == "pattern-dismiss-btn":
            self.dismiss_pattern()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in command input"""
        if event.input.id == "command-input":
            self.execute_command(dry_run=False, iterative=False)
    
    async def execute_command(self, dry_run: bool = False, iterative: bool = False):
        """Execute command from input"""
        input_widget = self.query_one("#command-input", Input)
        command = input_widget.value.strip()
        
        if not command:
            return
        
        # Clear input
        input_widget.value = ""
        
        # Update status
        status_bar = self.query_one("#status-bar", StatusBar)
        status_bar.update_status(last_result="Executing...")
        
        # Add to execution log
        exec_log = self.query_one("#execution-log-container", ExecutionLog)
        
        # TODO: Actually execute via zenus-core
        # For now, simulate execution
        await asyncio.sleep(1)  # Simulate work
        
        success = True
        duration = 1.2
        result = "✓ Completed"
        
        # Update log
        exec_log.add_execution(command, result, duration, success)
        
        # Update status
        status_bar.update_status(
            command_count=status_bar.command_count + 1,
            last_result=result
        )
        
        # Add to history
        history = self.query_one("#history-view", HistoryView)
        history.add_history_item(command, "Success" if success else "Failed", duration)
        
        # Simulate pattern detection every 10 commands
        if status_bar.command_count % 10 == 0:
            self.show_pattern_suggestion()
    
    def show_pattern_suggestion(self):
        """Show pattern suggestion"""
        pattern = self.query_one("#pattern-suggestion", PatternSuggestion)
        pattern.show_pattern(
            "You organize downloads weekly",
            "0 10 * * 1"
        )
    
    def create_automation(self):
        """Create automation from pattern"""
        # TODO: Create actual cron job
        self.notify("Automation created! ✓", severity="information")
        self.dismiss_pattern()
    
    def dismiss_pattern(self):
        """Dismiss pattern suggestion"""
        pattern = self.query_one("#pattern-suggestion", PatternSuggestion)
        pattern.hide_pattern()
    
    def action_tab(self, tab: str) -> None:
        """Switch to tab"""
        tabs = self.query_one(TabbedContent)
        tabs.active = f"{tab}-tab"


def main():
    """Run the dashboard"""
    app = ZenusDashboard()
    app.run()


if __name__ == "__main__":
    main()

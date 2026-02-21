"""
Explainability Dashboard

Provides insights into Zenus decision-making:
- What Zenus understood from user input
- Why it chose specific steps
- Confidence levels for each decision
- Alternative approaches considered
- Time breakdown per step
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from zenus_core.brain.llm.schemas import IntentIR, Step


console = Console()


@dataclass
class StepExplanation:
    """Explanation for a single step"""
    step: Step
    reasoning: str
    confidence: float  # 0.0 to 1.0
    alternatives: List[str] = field(default_factory=list)
    execution_time: Optional[float] = None
    result: Optional[str] = None
    success: bool = True


@dataclass
class ExecutionExplanation:
    """Complete explanation of an execution"""
    user_input: str
    understood_goal: str
    intent: IntentIR
    step_explanations: List[StepExplanation]
    total_time: float
    overall_confidence: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "user_input": self.user_input,
            "understood_goal": self.understood_goal,
            "intent": {
                "goal": self.intent.goal,
                "requires_confirmation": self.intent.requires_confirmation,
                "steps": [
                    {
                        "tool": s.tool,
                        "action": s.action,
                        "args": s.args,
                        "risk": s.risk
                    }
                    for s in self.intent.steps
                ]
            },
            "step_explanations": [
                {
                    "tool": se.step.tool,
                    "action": se.step.action,
                    "reasoning": se.reasoning,
                    "confidence": se.confidence,
                    "alternatives": se.alternatives,
                    "execution_time": se.execution_time,
                    "result": se.result,
                    "success": se.success
                }
                for se in self.step_explanations
            ],
            "total_time": self.total_time,
            "overall_confidence": self.overall_confidence,
            "timestamp": self.timestamp
        }


class ExplainabilityDashboard:
    """
    Dashboard for explaining Zenus decisions
    
    Features:
    - Show what Zenus understood
    - Explain each step's reasoning
    - Display alternatives considered
    - Show confidence scores
    - Time breakdown
    """
    
    def __init__(self):
        self.history: List[ExecutionExplanation] = []
        self.max_history = 50  # Keep last 50 executions
    
    def add_execution(self, explanation: ExecutionExplanation) -> None:
        """Add execution explanation to history"""
        self.history.append(explanation)
        
        # Trim history if too long
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
    
    def explain_last(self, verbose: bool = False) -> None:
        """
        Explain the last execution
        
        Args:
            verbose: Show detailed breakdown
        """
        if not self.history:
            console.print("[yellow]No execution history available[/yellow]")
            return
        
        explanation = self.history[-1]
        self._display_explanation(explanation, verbose=verbose)
    
    def explain_execution(self, index: int = -1, verbose: bool = False) -> None:
        """
        Explain a specific execution from history
        
        Args:
            index: History index (-1 = last, -2 = second to last, etc.)
            verbose: Show detailed breakdown
        """
        if not self.history:
            console.print("[yellow]No execution history available[/yellow]")
            return
        
        try:
            explanation = self.history[index]
            self._display_explanation(explanation, verbose=verbose)
        except IndexError:
            console.print(f"[red]No execution at index {index}[/red]")
    
    def _display_explanation(self, explanation: ExecutionExplanation, verbose: bool = False) -> None:
        """Display execution explanation"""
        
        # Header
        console.print()
        console.print(Panel.fit(
            f"[bold cyan]Execution Explanation[/bold cyan]\n"
            f"[dim]{explanation.timestamp}[/dim]",
            border_style="cyan"
        ))
        
        # User input vs understood goal
        console.print()
        console.print("[bold]What you said:[/bold]")
        console.print(f"  [yellow]{explanation.user_input}[/yellow]")
        console.print()
        console.print("[bold]What I understood:[/bold]")
        console.print(f"  [green]{explanation.understood_goal}[/green]")
        console.print()
        
        # Overall confidence
        confidence_color = (
            "green" if explanation.overall_confidence > 0.8
            else "yellow" if explanation.overall_confidence > 0.6
            else "red"
        )
        console.print(
            f"[bold]Overall Confidence:[/bold] "
            f"[{confidence_color}]{explanation.overall_confidence:.0%}[/{confidence_color}]"
        )
        console.print(f"[bold]Total Time:[/bold] {explanation.total_time:.2f}s")
        console.print()
        
        # Steps breakdown
        console.print("[bold cyan]═══ Execution Plan ═══[/bold cyan]")
        console.print()
        
        for i, step_exp in enumerate(explanation.step_explanations, 1):
            self._display_step_explanation(i, step_exp, verbose=verbose)
        
        # Summary statistics
        if verbose:
            self._display_statistics(explanation)
    
    def _display_step_explanation(
        self,
        step_num: int,
        step_exp: StepExplanation,
        verbose: bool = False
    ) -> None:
        """Display explanation for a single step"""
        
        # Step header
        status_icon = "✓" if step_exp.success else "✗"
        status_color = "green" if step_exp.success else "red"
        
        console.print(f"[bold]Step {step_num}:[/bold] {step_exp.step.tool}.{step_exp.step.action}")
        console.print(f"  Status: [{status_color}]{status_icon}[/{status_color}]")
        
        # Confidence
        confidence_color = (
            "green" if step_exp.confidence > 0.8
            else "yellow" if step_exp.confidence > 0.6
            else "red"
        )
        console.print(
            f"  Confidence: [{confidence_color}]{step_exp.confidence:.0%}[/{confidence_color}]"
        )
        
        # Reasoning
        console.print(f"  [dim]Why: {step_exp.reasoning}[/dim]")
        
        # Arguments (if verbose)
        if verbose and step_exp.step.args:
            console.print(f"  Arguments:")
            for key, value in step_exp.step.args.items():
                console.print(f"    • {key}: {value}")
        
        # Alternatives considered
        if step_exp.alternatives:
            console.print(f"  [dim]Alternatives considered:[/dim]")
            for alt in step_exp.alternatives:
                console.print(f"    [dim]→ {alt}[/dim]")
        
        # Execution time
        if step_exp.execution_time is not None:
            console.print(f"  [dim]Time: {step_exp.execution_time:.2f}s[/dim]")
        
        # Result
        if verbose and step_exp.result:
            result_preview = step_exp.result[:100] + "..." if len(step_exp.result) > 100 else step_exp.result
            console.print(f"  Result: [cyan]{result_preview}[/cyan]")
        
        console.print()
    
    def _display_statistics(self, explanation: ExecutionExplanation) -> None:
        """Display summary statistics"""
        console.print("[bold cyan]═══ Statistics ═══[/bold cyan]")
        console.print()
        
        # Create table
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Metric", style="dim")
        table.add_column("Value")
        
        # Calculate stats
        total_steps = len(explanation.step_explanations)
        successful_steps = sum(1 for se in explanation.step_explanations if se.success)
        avg_confidence = (
            sum(se.confidence for se in explanation.step_explanations) / total_steps
            if total_steps > 0 else 0
        )
        total_exec_time = sum(
            se.execution_time for se in explanation.step_explanations 
            if se.execution_time is not None
        )
        
        table.add_row("Total Steps", str(total_steps))
        table.add_row("Successful", f"{successful_steps}/{total_steps}")
        table.add_row("Avg Confidence", f"{avg_confidence:.0%}")
        table.add_row("Execution Time", f"{total_exec_time:.2f}s")
        table.add_row("Overhead", f"{explanation.total_time - total_exec_time:.2f}s")
        
        console.print(table)
        console.print()
    
    def show_history(self, limit: int = 10) -> None:
        """
        Show execution history
        
        Args:
            limit: Number of recent executions to show
        """
        if not self.history:
            console.print("[yellow]No execution history available[/yellow]")
            return
        
        console.print()
        console.print("[bold cyan]Execution History[/bold cyan]")
        console.print()
        
        # Create table
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("#", style="dim", width=4)
        table.add_column("Time", style="dim", width=16)
        table.add_column("Input", width=40)
        table.add_column("Steps", justify="right", width=6)
        table.add_column("Confidence", justify="right", width=10)
        table.add_column("Time", justify="right", width=8)
        
        # Show last N executions
        recent = self.history[-limit:]
        for i, exp in enumerate(recent, 1):
            confidence_color = (
                "green" if exp.overall_confidence > 0.8
                else "yellow" if exp.overall_confidence > 0.6
                else "red"
            )
            
            # Truncate input
            input_preview = exp.user_input[:37] + "..." if len(exp.user_input) > 40 else exp.user_input
            
            table.add_row(
                str(i),
                exp.timestamp[11:19],  # Time only
                input_preview,
                str(len(exp.step_explanations)),
                f"[{confidence_color}]{exp.overall_confidence:.0%}[/{confidence_color}]",
                f"{exp.total_time:.1f}s"
            )
        
        console.print(table)
        console.print()
        console.print(f"[dim]Showing {len(recent)} of {len(self.history)} total executions[/dim]")
        console.print(f"[dim]Use 'zenus explain <number>' to see details[/dim]")


# Global instance
_dashboard: Optional[ExplainabilityDashboard] = None


def get_explainability_dashboard() -> ExplainabilityDashboard:
    """Get singleton explainability dashboard"""
    global _dashboard
    if _dashboard is None:
        _dashboard = ExplainabilityDashboard()
    return _dashboard

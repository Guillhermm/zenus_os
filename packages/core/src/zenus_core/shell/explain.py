"""
Explain, Explainer, and Explainability modules.

Consolidated explanation layer:
- ExplainMode: shows plan details before execution
- Explainer: interactive reasoning display with confirmations
- ExplainabilityDashboard: post-execution history and analysis
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from zenus_core.brain.llm.schemas import IntentIR, Step
from zenus_core.output.console import (
    print_explanation,
    print_similar_commands,
    console,
)


class ExplainMode:
    """
    Generate and display explanations for execution plans
    """
    
    def __init__(self, semantic_search=None):
        self.semantic_search = semantic_search
    
    def explain(self, user_input: str, intent: IntentIR, show_similar: bool = True):
        """
        Show detailed explanation of the plan
        
        Args:
            user_input: Original user command
            intent: Translated intent
            show_similar: Whether to show similar past commands
        """
        
        # Generate reasoning
        reasoning = self._generate_reasoning(intent)
        
        # Show explanation
        print_explanation(
            goal=intent.goal,
            steps=[step.model_dump() for step in intent.steps],
            reasoning=reasoning
        )
        
        # Show similar past commands if available
        if show_similar and self.semantic_search:
            similar = self.semantic_search.search(user_input, top_k=3)
            if similar:
                print_similar_commands(similar)
                
                # Show success probability
                success_rate = self.semantic_search.get_success_rate(user_input)
                
                if success_rate < 0.5:
                    console.print(
                        f"\n⚠️  [yellow]Warning:[/yellow] Similar commands have "
                        f"[bold]{success_rate:.0%}[/bold] success rate",
                        style="yellow"
                    )
                else:
                    console.print(
                        f"\n✓ [green]Similar commands have "
                        f"[bold]{success_rate:.0%}[/bold] success rate[/green]"
                    )
        
        console.print()
    
    def _generate_reasoning(self, intent: IntentIR) -> str:
        """Generate reasoning explanation"""
        
        reasoning = []
        
        # Analyze steps
        num_steps = len(intent.steps)
        read_steps = sum(1 for s in intent.steps if s.risk == 0)
        modify_steps = sum(1 for s in intent.steps if s.risk in [1, 2])
        danger_steps = sum(1 for s in intent.steps if s.risk == 3)
        
        if num_steps == 1:
            reasoning.append("This is a simple single-step operation.")
        else:
            reasoning.append(f"This requires {num_steps} steps to complete.")
        
        if read_steps == num_steps:
            reasoning.append("All steps are read-only (no changes to your system).")
        elif modify_steps > 0:
            reasoning.append(f"Will modify {modify_steps} item(s).")
        
        if danger_steps > 0:
            reasoning.append(
                f"⚠️  Contains {danger_steps} destructive operation(s) "
                f"(confirmation required)."
            )
        
        # Tool analysis
        tools_used = set(step.tool for step in intent.steps)
        reasoning.append(f"Using: {', '.join(tools_used)}")
        
        return " ".join(reasoning)
    
    def confirm(self, prompt: str = "Proceed with execution?") -> bool:
        """Ask user for confirmation"""
        response = console.input(f"\n[bold yellow]{prompt}[/bold yellow] (y/n): ")
        return response.lower() in ('y', 'yes')


class Explainer:
    """
    Explains Zenus's reasoning and decisions
    
    Capabilities:
    - Show goal breakdown
    - Explain each step
    - Display risk assessment
    - Show alternative approaches
    - Interactive approval
    """
    
    def __init__(self):
        pass
    
    def explain_intent(self, user_input: str, intent: IntentIR) -> None:
        """
        Explain how user input was translated to intent
        
        Args:
            user_input: Original user command
            intent: Translated IntentIR
        """
        console.print("\n")
        console.print(Panel.fit(
            "[bold cyan]🤔 Decision Explanation[/bold cyan]",
            border_style="cyan"
        ))
        
        # User's request
        console.print(f"\n[bold]Your Request:[/bold]")
        console.print(f"  {user_input}")
        
        # Goal interpretation
        console.print(f"\n[bold]Goal Interpretation:[/bold]")
        console.print(f"  {intent.goal}")
        
        # Step breakdown
        self._explain_steps(intent.steps)
        
        # Risk assessment
        self._explain_risks(intent)
        
        # Confirmation requirement
        if intent.requires_confirmation:
            console.print(f"\n[yellow]⚠️  This operation requires confirmation (destructive changes)[/yellow]")
    
    def _explain_steps(self, steps: List[Step]) -> None:
        """Explain execution steps"""
        console.print(f"\n[bold]Execution Plan:[/bold]")
        
        tree = Tree("📋 Steps")
        
        for i, step in enumerate(steps, 1):
            # Format args nicely
            args_str = ", ".join([f"{k}={v}" for k, v in step.args.items()])
            
            # Risk emoji
            risk_emoji = {
                0: "🟢",  # Read-only
                1: "🟡",  # Safe modifications
                2: "🟠",  # Data changes
                3: "🔴"   # Destructive
            }.get(step.risk, "⚪")
            
            # Risk label
            risk_label = {
                0: "read-only",
                1: "safe modification",
                2: "data change",
                3: "destructive"
            }.get(step.risk, "unknown")
            
            step_text = f"{risk_emoji} {step.tool}.{step.action}({args_str}) [{risk_label}]"
            tree.add(step_text)
        
        console.print(tree)
    
    def _explain_risks(self, intent: IntentIR) -> None:
        """Explain risk assessment"""
        max_risk = max([step.risk for step in intent.steps])
        
        console.print(f"\n[bold]Risk Assessment:[/bold]")
        
        if max_risk == 0:
            console.print("  🟢 [green]Safe - Read-only operations[/green]")
        elif max_risk == 1:
            console.print("  🟡 [yellow]Low - Creates or moves files[/yellow]")
        elif max_risk == 2:
            console.print("  🟠 [orange1]Medium - Modifies existing data[/orange1]")
        else:
            console.print("  🔴 [red]High - Destructive operations (delete/kill)[/red]")
    
    def explain_task_complexity(
        self,
        user_input: str,
        needs_iteration: bool,
        confidence: float,
        reasoning: str,
        estimated_steps: int
    ) -> None:
        """
        Explain why task was classified as iterative or one-shot
        
        Args:
            user_input: User command
            needs_iteration: Whether iterative mode was chosen
            confidence: Confidence in classification
            reasoning: Reasoning for decision
            estimated_steps: Estimated number of iterations
        """
        console.print("\n")
        console.print(Panel.fit(
            "[bold cyan]🧠 Task Analysis[/bold cyan]",
            border_style="cyan"
        ))
        
        console.print(f"\n[bold]Your Request:[/bold]")
        console.print(f"  {user_input}")
        
        console.print(f"\n[bold]Complexity Assessment:[/bold]")
        
        if needs_iteration:
            console.print(f"  [yellow]→ Detected as ITERATIVE task[/yellow]")
            console.print(f"  Confidence: {confidence:.0%}")
            console.print(f"  Estimated iterations: ~{estimated_steps}")
        else:
            console.print(f"  [green]→ Detected as ONE-SHOT task[/green]")
            console.print(f"  Confidence: {confidence:.0%}")
        
        console.print(f"\n[bold]Reasoning:[/bold]")
        console.print(f"  {reasoning}")
    
    def explain_iteration(
        self,
        iteration: int,
        total: int,
        intent: IntentIR,
        observations: List[str]
    ) -> None:
        """
        Explain current iteration state
        
        Args:
            iteration: Current iteration number
            total: Total max iterations
            intent: Intent for this iteration
            observations: Observations so far
        """
        console.print(f"\n[bold cyan]═══ Iteration {iteration}/{total} Explanation ═══[/bold cyan]")
        
        console.print(f"\n[bold]Current Goal:[/bold]")
        console.print(f"  {intent.goal}")
        
        if observations:
            console.print(f"\n[bold]Observations So Far:[/bold]")
            for i, obs in enumerate(observations[-3:], 1):  # Last 3
                console.print(f"  {i}. {obs}")
        
        console.print(f"\n[bold]Next Actions:[/bold]")
        for i, step in enumerate(intent.steps, 1):
            console.print(f"  {i}. {step.tool}.{step.action}")
    
    def explain_context(self, context: Dict) -> None:
        """
        Explain environmental context
        
        Args:
            context: Context dictionary from ContextManager
        """
        console.print("\n")
        console.print(Panel.fit(
            "[bold cyan]📍 Environmental Context[/bold cyan]",
            border_style="cyan"
        ))
        
        # Directory
        if "directory" in context:
            dir_ctx = context["directory"]
            console.print(f"\n[bold]Location:[/bold]")
            console.print(f"  Path: {dir_ctx['path']}")
            if dir_ctx['project_type']:
                console.print(f"  Project: {dir_ctx['project_type']} ({dir_ctx['project_name']})")
        
        # Git
        if "git" in context and context["git"]["is_repo"]:
            git_ctx = context["git"]
            console.print(f"\n[bold]Git Repository:[/bold]")
            console.print(f"  Branch: {git_ctx['branch']}")
            console.print(f"  Status: {git_ctx['status']}")
            if git_ctx["ahead_commits"] > 0:
                console.print(f"  Unpushed: {git_ctx['ahead_commits']} commits")
        
        # Time
        if "time" in context:
            time_ctx = context["time"]
            console.print(f"\n[bold]Time:[/bold]")
            console.print(f"  Current: {time_ctx['timestamp']}")
            console.print(f"  Time of day: {time_ctx['time_of_day']}")
            if time_ctx["is_weekend"]:
                console.print(f"  Weekend detected")
        
        # Processes
        if "processes" in context and context["processes"]["dev_tools"]:
            proc_ctx = context["processes"]
            console.print(f"\n[bold]Running Tools:[/bold]")
            console.print(f"  {', '.join(proc_ctx['dev_tools'])}")
    
    def confirm(self, prompt: str = "Proceed with execution?") -> bool:
        """
        Ask user for confirmation
        
        Args:
            prompt: Confirmation prompt
        
        Returns:
            True if user confirms, False otherwise
        """
        console.print(f"\n[bold cyan]{prompt}[/bold cyan]")
        response = input("Continue? [y/N]: ").strip().lower()
        
        return response in ['y', 'yes']
    
    def show_alternatives(self, alternatives: List[Dict]) -> None:
        """
        Show alternative approaches
        
        Args:
            alternatives: List of alternative approaches
        """
        console.print(f"\n[bold]Alternative Approaches:[/bold]")
        
        for i, alt in enumerate(alternatives, 1):
            console.print(f"\n  [cyan]{i}. {alt['name']}[/cyan]")
            console.print(f"     {alt['description']}")
            if 'pros' in alt:
                console.print(f"     Pros: {', '.join(alt['pros'])}")
            if 'cons' in alt:
                console.print(f"     Cons: {', '.join(alt['cons'])}")


# Global explainer
_explainer = None


def get_explainer() -> Explainer:
    """Get global explainer instance"""
    global _explainer
    if _explainer is None:
        _explainer = Explainer()
    return _explainer


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

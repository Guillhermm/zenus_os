"""
Explainer Module

Shows detailed reasoning and decision-making process before execution.
Provides transparency and allows interactive approval.
"""

from typing import Dict, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from zenus_core.brain.llm.schemas import IntentIR, Step


console = Console()


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

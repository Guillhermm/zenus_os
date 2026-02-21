"""
Explain Mode

Show reasoning and details before execution.
"""

from typing import List, Dict
from zenus_core.brain.llm.schemas import IntentIR
from zenus_core.cli.formatter import (
    print_explanation, 
    print_similar_commands,
    console
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

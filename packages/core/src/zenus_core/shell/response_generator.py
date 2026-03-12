"""
Conversational Feedback Generator

Generates natural language summaries of execution results.
"""

from typing import List
from zenus_core.brain.llm.schemas import IntentIR


class ResponseGenerator:
    """
    Generates conversational feedback from execution results
    
    Makes Zenus feel more natural and less robotic.
    """
    
    def __init__(self, llm):
        self.llm = llm
    
    def generate_summary(
        self, 
        user_input: str, 
        intent: IntentIR, 
        step_results: List[str]
    ) -> str:
        """
        Generate conversational summary of what was done
        
        Args:
            user_input: Original command
            intent: Executed intent
            step_results: Results from each step
        
        Returns:
            Natural language summary
        """
        
        # Build context for LLM
        "\n".join([
            f"- {step.tool}.{step.action}: {result}"
            for step, result in zip(intent.steps, step_results)
        ])
        
        
        try:
            # This is a simple text completion, not intent translation
            # For now, use a simplified approach
            return self._simple_summary(intent, step_results)
        except Exception:
            # Fallback to simple summary
            return self._simple_summary(intent, step_results)
    
    def _simple_summary(self, intent: IntentIR, step_results: List[str]) -> str:
        """Fallback simple summary without LLM"""
        
        if not step_results:
            return f"Completed: {intent.goal}"
        
        # Use last result as primary output
        last_result = step_results[-1]
        
        # Make it conversational
        if "created" in last_result.lower() or "wrote" in last_result.lower():
            return f"Done! {last_result}"
        elif "found" in last_result.lower():
            return f"{last_result}"
        else:
            return f"Completed: {last_result}"

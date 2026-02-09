"""
CLI Orchestrator

Manages the full pipeline: CLI input → Intent → Plan → Execution
Ensures clear separation of concerns and deterministic flow.
"""

from typing import Optional
from brain.llm.factory import get_llm
from brain.planner import execute_plan
from brain.llm.schemas import IntentIR


class Orchestrator:
    """
    Orchestrates the intent → plan → execution pipeline
    
    Responsibilities:
    - Translate natural language to IntentIR
    - Execute plans through the planner
    - Provide consistent interface for both interactive and direct modes
    """

    def __init__(self):
        self.llm = get_llm()

    def process(self, user_input: str, auto_confirm: bool = False) -> Optional[str]:
        """
        Process a single user command through the full pipeline
        
        Args:
            user_input: Natural language command
            auto_confirm: If True, skip confirmation prompts (for direct CLI mode)
        
        Returns:
            Status message or None
        """
        try:
            # Step 1: Translate intent
            intent = self.llm.translate_intent(user_input)
            
            # Step 2: Execute plan
            result = self._execute_with_confirmation(intent, auto_confirm)
            return result
            
        except Exception as e:
            return f"Error: {e}"

    def _execute_with_confirmation(self, intent: IntentIR, auto_confirm: bool) -> str:
        """Execute plan with optional confirmation"""
        
        # Display plan
        print(f"\nGoal: {intent.goal}\n")
        for i, step in enumerate(intent.steps, 1):
            risk_label = ["READ", "CREATE", "MODIFY", "DELETE"][step.risk]
            print(f"  [{risk_label}] Step {i}: {step.tool}.{step.action} {step.args}")
        
        # Confirmation handling
        if intent.requires_confirmation and not auto_confirm:
            confirm = input("\nExecute this plan? (y/n): ")
            if confirm.lower() != "y":
                return "Aborted by user"
        
        # Execute through planner
        try:
            execute_plan(intent)
            return "✓ Plan executed successfully"
        except Exception as e:
            return f"✗ Execution failed: {e}"

    def interactive_shell(self):
        """Run interactive REPL mode"""
        print("Zenus OS Interactive Shell")
        print("Type 'exit' or 'quit' to exit\n")
        
        while True:
            try:
                user_input = input("zenus > ").strip()
                
                if not user_input:
                    continue
                
                if user_input in ("exit", "quit"):
                    print("Goodbye!")
                    break
                
                self.process(user_input, auto_confirm=False)
                print()  # Blank line for readability
                
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except EOFError:
                print("\nGoodbye!")
                break

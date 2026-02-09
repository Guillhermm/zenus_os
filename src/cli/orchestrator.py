"""
CLI Orchestrator

Manages the full pipeline: CLI input to Intent to Plan to Execution.
Ensures clear separation of concerns and deterministic flow.
"""

from typing import Optional
from brain.llm.factory import get_llm
from brain.planner import execute_plan
from brain.adaptive_planner import AdaptivePlanner
from brain.llm.schemas import IntentIR
from audit.logger import get_logger


class OrchestratorError(Exception):
    """Base exception for orchestrator errors"""
    pass


class IntentTranslationError(OrchestratorError):
    """Failed to translate user input to intent"""
    pass


class ExecutionError(OrchestratorError):
    """Failed to execute plan"""
    pass


class Orchestrator:
    """
    Orchestrates the intent to plan to execution pipeline
    
    Responsibilities:
    - Translate natural language to IntentIR
    - Execute plans through the planner
    - Log all operations for audit
    - Provide consistent interface for both interactive and direct modes
    """

    def __init__(self, adaptive: bool = True):
        self.llm = get_llm()
        self.logger = get_logger()
        self.adaptive = adaptive
        if adaptive:
            self.adaptive_planner = AdaptivePlanner(self.logger)

    def process(
        self, 
        user_input: str, 
        auto_confirm: bool = False,
        dry_run: bool = False
    ) -> Optional[str]:
        """
        Process a single user command through the full pipeline
        
        Args:
            user_input: Natural language command
            auto_confirm: If True, skip confirmation prompts (for direct CLI mode)
            dry_run: If True, show plan but do not execute
        
        Returns:
            Status message or None
        """
        try:
            # Step 1: Translate intent
            try:
                intent = self.llm.translate_intent(user_input)
            except Exception as e:
                error_msg = f"Failed to understand command: {str(e)}"
                self.logger.log_error(error_msg, {"user_input": user_input})
                raise IntentTranslationError(error_msg) from e
            
            # Log intent
            mode = "direct" if auto_confirm else "interactive"
            if dry_run:
                mode = f"{mode}_dry_run"
            self.logger.log_intent(user_input, intent, mode)
            
            # Step 2: Show plan and execute
            result = self._execute_with_confirmation(
                intent, 
                auto_confirm, 
                dry_run
            )
            return result
            
        except OrchestratorError:
            # Re-raise our own errors
            raise
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.logger.log_error(error_msg, {"user_input": user_input})
            raise OrchestratorError(error_msg) from e

    def _execute_with_confirmation(
        self, 
        intent: IntentIR, 
        auto_confirm: bool,
        dry_run: bool
    ) -> str:
        """Execute plan with optional confirmation"""
        
        # Display plan
        print(f"\nGoal: {intent.goal}\n")
        for i, step in enumerate(intent.steps, 1):
            risk_labels = ["READ", "CREATE", "MODIFY", "DELETE"]
            risk_label = risk_labels[step.risk] if step.risk < len(risk_labels) else "UNKNOWN"
            print(f"  [{risk_label}] Step {i}: {step.tool}.{step.action} {step.args}")
        
        # Dry run mode stops here
        if dry_run:
            print("\n[DRY RUN] Plan not executed")
            return "Dry run complete"
        
        # Confirmation handling
        if intent.requires_confirmation and not auto_confirm:
            confirm = input("\nExecute this plan? (y/n): ")
            if confirm.lower() != "y":
                self.logger.log_execution_end(False, "User aborted")
                return "Aborted by user"
        
        # Execute through planner (adaptive or basic)
        self.logger.log_execution_start(intent)
        try:
            if self.adaptive:
                # Use adaptive planner with retry and observation
                success = self.adaptive_planner.execute_adaptive(intent)
                if success:
                    summary = self.adaptive_planner.get_execution_summary()
                    result_msg = "Plan executed successfully"
                    if summary["retried_steps"] > 0:
                        result_msg += f" ({summary['retried_steps']} steps retried)"
                    return result_msg
                else:
                    raise ExecutionError("Plan execution failed")
            else:
                # Use basic planner (legacy)
                execute_plan(intent, self.logger)
                self.logger.log_execution_end(True)
                return "Plan executed successfully"
        except Exception as e:
            error_msg = f"Execution failed: {e}"
            self.logger.log_execution_end(False, error_msg)
            raise ExecutionError(error_msg) from e

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
                
                # Check for dry run flag
                dry_run = False
                if user_input.startswith("--dry-run "):
                    dry_run = True
                    user_input = user_input[10:]  # Remove flag
                
                result = self.process(user_input, auto_confirm=False, dry_run=dry_run)
                if result:
                    print(f"\n{result}")
                print()  # Blank line for readability
                
            except IntentTranslationError as e:
                print(f"\nError: {e}\n")
            except ExecutionError as e:
                print(f"\nError: {e}\n")
            except OrchestratorError as e:
                print(f"\nError: {e}\n")
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except EOFError:
                print("\nGoodbye!")
                break

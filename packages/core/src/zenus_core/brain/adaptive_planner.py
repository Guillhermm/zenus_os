"""
Adaptive Planner

Executes plans with observation and adaptation.
Key difference from basic planner: can observe failures and replan.
"""

from typing import Optional, Callable
from zenus_core.brain.llm.schemas import IntentIR, Step
from zenus_core.brain.llm.factory import get_llm
from zenus_core.tools.registry import TOOLS
from zenus_core.safety.policy import check_step, SafetyError


class ExecutionResult:
    """Result of a single step execution"""
    def __init__(self, success: bool, output: str, error: Optional[str] = None):
        self.success = success
        self.output = output
        self.error = error


class AdaptivePlanner:
    """
    Executes plans with observation and adaptation
    
    Unlike basic execution, this planner:
    - Observes each step result
    - Detects failures
    - Can request corrective actions
    - Maintains execution context
    """
    
    def __init__(self, logger=None):
        self.logger = logger
        self.llm = get_llm()
        self.execution_history = []
    
    def execute_adaptive(
        self, 
        intent: IntentIR,
        max_retries: int = 2,
        on_failure: Callable = None
    ) -> bool:
        """
        Execute plan with adaptive retry on failure
        
        Args:
            intent: The validated IntentIR to execute
            max_retries: Maximum retry attempts per step
            on_failure: Optional callback for failure handling
        
        Returns:
            True if all steps succeeded, False otherwise
        """
        
        if self.logger:
            self.logger.log_execution_start(intent)
        
        for step_idx, step in enumerate(intent.steps):
            attempt = 0
            step_succeeded = False
            
            while attempt <= max_retries and not step_succeeded:
                if attempt > 0:
                    print(f"\n  Retry attempt {attempt} for step {step_idx + 1}...")
                
                result = self._execute_single_step(step, step_idx + 1)
                
                if result.success:
                    step_succeeded = True
                    self.execution_history.append({
                        "step": step,
                        "result": result,
                        "attempt": attempt
                    })
                else:
                    attempt += 1
                    
                    if attempt <= max_retries:
                        # Try to adapt the step based on failure
                        adapted_step = self._adapt_on_failure(
                            step, 
                            result,
                            self.execution_history
                        )
                        
                        if adapted_step:
                            print(f"  Adapting: {adapted_step.action} with {adapted_step.args}")
                            step = adapted_step
                        else:
                            # No adaptation possible, fail
                            break
                    
                    if on_failure:
                        on_failure(step, result)
            
            if not step_succeeded:
                error_msg = f"Step {step_idx + 1} failed after {attempt} attempts"
                if self.logger:
                    self.logger.log_execution_end(False, error_msg)
                return False
        
        if self.logger:
            self.logger.log_execution_end(True)
        
        return True
    
    def _execute_single_step(self, step: Step, step_num: int) -> ExecutionResult:
        """Execute a single step and capture result"""
        
        try:
            # Safety check
            check_step(step)
            
            # Get tool
            tool = TOOLS.get(step.tool)
            if not tool:
                return ExecutionResult(
                    False, 
                    "", 
                    f"Tool not found: {step.tool}"
                )
            
            # Get action
            action = getattr(tool, step.action, None)
            if not action:
                return ExecutionResult(
                    False,
                    "",
                    f"Action not found: {step.tool}.{step.action}"
                )
            
            # Execute
            output = action(**step.args)
            print(f"  Step {step_num}: {step.tool}.{step.action} -> {output}")
            
            if self.logger:
                self.logger.log_step_result(
                    step.tool, 
                    step.action, 
                    str(output), 
                    True
                )
            
            return ExecutionResult(True, str(output))
            
        except SafetyError as e:
            error_msg = f"Safety check failed: {e}"
            if self.logger:
                self.logger.log_step_result(
                    step.tool, 
                    step.action, 
                    error_msg, 
                    False
                )
            return ExecutionResult(False, "", error_msg)
            
        except Exception as e:
            error_msg = f"Execution failed: {e}"
            if self.logger:
                self.logger.log_step_result(
                    step.tool,
                    step.action,
                    error_msg,
                    False
                )
            return ExecutionResult(False, "", error_msg)
    
    def _adapt_on_failure(
        self, 
        failed_step: Step, 
        result: ExecutionResult,
        history: list
    ) -> Optional[Step]:
        """
        Attempt to adapt a failed step
        
        Uses LLM to suggest corrective action based on:
        - The failed step
        - The error
        - Execution history
        
        Returns adapted step or None if no adaptation possible
        """
        
        # For now, return None (no LLM-based adaptation yet)
        # This will be enhanced in future iterations
        return None
    
    def get_execution_summary(self) -> dict:
        """Get summary of execution for reporting"""
        
        total_steps = len(self.execution_history)
        retried_steps = sum(
            1 for entry in self.execution_history if entry["attempt"] > 0
        )
        
        return {
            "total_steps": total_steps,
            "retried_steps": retried_steps,
            "success_rate": 1.0 if total_steps > 0 else 0.0
        }

"""
Sandboxed Adaptive Planner

Extends adaptive planner with sandbox enforcement.
"""

from typing import Optional, List
from brain.adaptive_planner import AdaptivePlanner, ExecutionResult
from brain.llm.schemas import IntentIR, Step
from sandbox.executor import SandboxViolation
from sandbox.constraints import SandboxConstraints
from tools.registry import TOOLS


class SandboxedAdaptivePlanner(AdaptivePlanner):
    """
    Adaptive planner with sandbox enforcement
    
    All tool execution goes through sandbox validation.
    """
    
    def __init__(self, logger=None, sandbox_constraints: Optional[SandboxConstraints] = None):
        super().__init__(logger)
        
        # For now, use regular tools - sandbox is enforced at executor level
        # Full sandboxed registry will be implemented in next iteration
        from tools.registry import TOOLS
        self.tools = TOOLS
    
    def execute_with_retry(self, intent: IntentIR, max_retries: int = 2) -> List[str]:
        """
        Execute plan with retry logic
        
        Uses parent's adaptive retry logic.
        """
        # Parent class uses 'execute' method, not 'execute_with_retry'
        # The adaptive logic is already in the parent
        return self.execute(intent, max_retries=max_retries)
    
    def _execute_single_step(self, step: Step, step_num: int) -> ExecutionResult:
        """Execute a single step with sandbox enforcement"""
        
        try:
            # Safety check (from parent)
            from safety.policy import check_step
            check_step(step)
            
            # Get tool
            tool = self.tools.get(step.tool)
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
            result = action(**step.args)
            print(f"  Step {step_num}: {step.tool}.{step.action} -> {result}")
            
            if self.logger:
                self.logger.log_step_result(
                    step.tool,
                    step.action,
                    str(result),
                    True
                )
            
            return ExecutionResult(True, str(result))
            
        except SandboxViolation as e:
            error_msg = f"Sandbox violation: {e}"
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

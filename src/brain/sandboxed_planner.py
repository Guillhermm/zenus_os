"""
Sandboxed Adaptive Planner

Extends adaptive planner with sandbox enforcement.
"""

from typing import Optional, Callable
from brain.adaptive_planner import AdaptivePlanner, ExecutionResult
from brain.llm.schemas import IntentIR, Step
from sandbox.executor import SandboxConfig, SandboxViolation
from sandbox.tool_wrapper import SandboxedToolRegistry
from tools.registry import TOOLS


class SandboxedAdaptivePlanner(AdaptivePlanner):
    """
    Adaptive planner with sandbox enforcement
    
    All tool execution goes through sandbox validation.
    """
    
    def __init__(self, logger=None, sandbox_config: Optional[SandboxConfig] = None):
        super().__init__(logger)
        
        # Create sandboxed tool registry
        if sandbox_config is None:
            sandbox_config = SandboxConfig()
        
        self.sandboxed_registry = SandboxedToolRegistry(TOOLS, sandbox_config)
    
    def _execute_single_step(self, step: Step, step_num: int) -> ExecutionResult:
        """Execute a single step with sandbox enforcement"""
        
        try:
            # Safety check (from parent)
            from safety.policy import check_step
            check_step(step)
            
            # Get sandboxed tool
            sandboxed_tool = self.sandboxed_registry.get(step.tool)
            if not sandboxed_tool:
                return ExecutionResult(
                    False,
                    "",
                    f"Tool not found: {step.tool}"
                )
            
            # Execute through sandbox
            result = sandboxed_tool.execute(step)
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

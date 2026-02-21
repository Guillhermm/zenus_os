"""
Plan Executor

Executes IntentIR plans by dispatching steps to registered tools.
Does NOT handle display or confirmation, that is the orchestrator's job.
"""

from typing import Optional
from zenus_core.tools.registry import TOOLS
from zenus_core.safety.policy import check_step, SafetyError
from zenus_core.brain.llm.schemas import IntentIR


def execute_plan(intent: IntentIR, logger=None) -> None:
    """
    Execute a validated IntentIR plan
    
    Responsibilities:
    - Safety checks (via policy)
    - Tool dispatch
    - Step by step execution
    
    Does NOT:
    - Display plan details (orchestrator's job)
    - Ask for confirmation (orchestrator's job)
    - Handle high level errors (orchestrator catches them)
    
    Args:
        intent: The validated IntentIR to execute
        logger: Optional audit logger for recording step results
    """
    
    for step in intent.steps:
        # Safety check
        try:
            check_step(step)
        except SafetyError as e:
            error_msg = f"Safety check failed for {step.tool}.{step.action}: {e}"
            if logger:
                logger.log_step_result(step.tool, step.action, error_msg, False)
            raise
        
        # Get tool
        tool = TOOLS.get(step.tool)
        if not tool:
            error_msg = f"Tool not found: {step.tool}"
            if logger:
                logger.log_step_result(step.tool, step.action, error_msg, False)
            raise ValueError(error_msg)
        
        # Get action method
        action = getattr(tool, step.action, None)
        if not action:
            error_msg = f"Action not found: {step.tool}.{step.action}"
            if logger:
                logger.log_step_result(step.tool, step.action, error_msg, False)
            raise ValueError(error_msg)
        
        # Execute
        try:
            result = action(**step.args)
            print(f"  Done: {step.tool}.{step.action}: {result}")
            
            if logger:
                logger.log_step_result(step.tool, step.action, str(result), True)
                
        except Exception as e:
            error_msg = f"Step failed: {e}"
            if logger:
                logger.log_step_result(step.tool, step.action, error_msg, False)
            raise

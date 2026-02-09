"""
Plan Executor

Executes IntentIR plans by dispatching steps to registered tools.
Does NOT handle display or confirmation — that's the orchestrator's job.
"""

from tools.registry import TOOLS
from safety.policy import check_step
from brain.llm.schemas import IntentIR


def execute_plan(intent: IntentIR) -> None:
    """
    Execute a validated IntentIR plan
    
    Responsibilities:
    - Safety checks (via policy)
    - Tool dispatch
    - Step-by-step execution
    
    Does NOT:
    - Display plan details (orchestrator's job)
    - Ask for confirmation (orchestrator's job)
    - Handle high-level errors (orchestrator catches them)
    """
    
    for step in intent.steps:
        # Safety check
        check_step(step)
        
        # Get tool
        tool = TOOLS.get(step.tool)
        if not tool:
            raise ValueError(f"Tool not found: {step.tool}")
        
        # Get action method
        action = getattr(tool, step.action, None)
        if not action:
            raise ValueError(f"Action not found: {step.tool}.{step.action}")
        
        # Execute
        result = action(**step.args)
        
        # Log result (simple for now, can be enhanced)
        print(f"  ✓ {step.tool}.{step.action}: {result}")

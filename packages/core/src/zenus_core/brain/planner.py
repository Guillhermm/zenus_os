"""
Plan Executor

Executes IntentIR plans by dispatching steps to registered tools.
Does NOT handle display or confirmation, that is the orchestrator's job.
"""

from typing import Optional, List
from zenus_core.tools.registry import TOOLS
from zenus_core.safety.policy import check_step, SafetyError
from zenus_core.brain.llm.schemas import IntentIR


def execute_plan(intent: IntentIR, logger=None, parallel: bool = True) -> List[str]:
    """
    Execute a validated IntentIR plan
    
    Responsibilities:
    - Safety checks (via policy)
    - Tool dispatch
    - Step by step execution (or parallel if enabled)
    
    Does NOT:
    - Display plan details (orchestrator's job)
    - Ask for confirmation (orchestrator's job)
    - Handle high level errors (orchestrator catches them)
    
    Args:
        intent: The validated IntentIR to execute
        logger: Optional audit logger for recording step results
        parallel: Enable parallel execution for independent steps
    
    Returns:
        List of step results (one per step)
    """
    from zenus_core.execution.error_recovery import get_error_recovery
    
    # Try parallel execution if enabled and multiple steps
    if parallel and len(intent.steps) > 1:
        try:
            from zenus_core.execution.parallel_executor import ParallelExecutor
            from zenus_core.brain.dependency_analyzer import DependencyAnalyzer
            
            # Analyze dependencies
            analyzer = DependencyAnalyzer()
            graph = analyzer.build_dependency_graph(intent.steps)
            
            # Execute in parallel if there are independent steps
            if analyzer.can_parallelize(graph):
                executor = ParallelExecutor()
                results = executor.execute_parallel(intent.steps, graph)
                
                # Log results
                if logger:
                    for step, result in zip(intent.steps, results):
                        logger.log_step_result(step.tool, step.action, str(result), True)
                
                return results
        except ImportError:
            # Parallel executor not available, fall back to sequential
            pass
        except Exception as e:
            # Parallel execution failed, fall back to sequential
            print(f"  [Parallel execution failed, using sequential: {e}]")
    
    # Sequential execution (fallback or by choice)
    results = []
    error_recovery = get_error_recovery()
    
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
        
        # Execute with error recovery
        try:
            result = action(**step.args)
            print(f"  Done: {step.tool}.{step.action}: {result}")
            
            if logger:
                logger.log_step_result(step.tool, step.action, str(result), True)
            
            results.append(str(result))
                
        except Exception as e:
            # Attempt error recovery
            context = {
                "tool": step.tool,
                "action": step.action,
                "args": step.args
            }
            
            recovery_result = error_recovery.recover(
                e, context, action, **step.args
            )
            
            if recovery_result.success:
                # Recovery succeeded
                result_msg = f"Recovered: {recovery_result.message}"
                print(f"  {result_msg}")
                results.append(result_msg)
                
                if logger:
                    logger.log_step_result(step.tool, step.action, result_msg, True)
            else:
                # Recovery failed
                error_msg = f"Step failed: {recovery_result.message}"
                if logger:
                    logger.log_step_result(step.tool, step.action, error_msg, False)
                raise RuntimeError(error_msg) from e
    
    return results

"""
Safety Policy

Defines rules for what operations are allowed and enforces them.
"""

from brain.llm.schemas import Step


class SafetyError(Exception):
    """Raised when a step violates safety policy"""
    pass


def check_step(step: Step) -> bool:
    """
    Verify that a step is safe to execute
    
    Args:
        step: The step to validate
    
    Returns:
        True if safe
    
    Raises:
        SafetyError: If step violates policy
    """
    if step.risk >= 3:
        raise SafetyError(
            f"High risk operation blocked: {step.tool}.{step.action} (risk={step.risk}). "
            "Delete operations require explicit user confirmation."
        )
    
    return True

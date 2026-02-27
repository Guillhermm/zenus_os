"""
Retry Budget System

Prevents infinite retries by allocating a budget for retry attempts.
Tracks success rates and adjusts retry behavior accordingly.
"""

import time
from typing import Callable, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_attempts: int = 3               # Maximum retry attempts
    initial_delay_seconds: float = 1.0  # Initial delay between retries
    max_delay_seconds: float = 30.0     # Maximum delay between retries
    exponential_base: float = 2.0       # Exponential backoff base
    jitter: bool = True                 # Add jitter to delays


@dataclass
class RetryBudget:
    """
    Retry budget tracker
    
    Tracks retry attempts and success rates to prevent
    excessive retries when service is consistently failing.
    """
    total_budget: int = 100             # Total retry budget per window
    window_seconds: float = 600.0       # Budget window (10 minutes)
    budget_used: int = 0
    window_start: datetime = None
    
    def __post_init__(self):
        if self.window_start is None:
            self.window_start = datetime.now()
    
    def can_retry(self) -> bool:
        """Check if retry budget is available"""
        self._reset_if_expired()
        return self.budget_used < self.total_budget
    
    def consume(self, amount: int = 1):
        """Consume retry budget"""
        self._reset_if_expired()
        self.budget_used += amount
    
    def _reset_if_expired(self):
        """Reset budget if window expired"""
        elapsed = (datetime.now() - self.window_start).total_seconds()
        if elapsed >= self.window_seconds:
            self.budget_used = 0
            self.window_start = datetime.now()
    
    def get_remaining(self) -> int:
        """Get remaining budget"""
        self._reset_if_expired()
        return max(0, self.total_budget - self.budget_used)
    
    def get_usage_percentage(self) -> float:
        """Get budget usage percentage"""
        self._reset_if_expired()
        return (self.budget_used / self.total_budget) * 100


class RetryExhaustedError(Exception):
    """Raised when all retry attempts are exhausted"""
    pass


class RetryBudgetExceededError(Exception):
    """Raised when retry budget is exceeded"""
    pass


def retry_with_budget(
    func: Callable,
    *args,
    config: Optional[RetryConfig] = None,
    budget: Optional[RetryBudget] = None,
    retry_on: tuple = (Exception,),
    **kwargs
) -> Any:
    """
    Execute function with retry logic and budget tracking
    
    Args:
        func: Function to execute
        config: Retry configuration
        budget: Retry budget tracker
        retry_on: Tuple of exceptions to retry on
        *args, **kwargs: Arguments to pass to function
    
    Returns:
        Result from function
    
    Raises:
        RetryExhaustedError: If all retries exhausted
        RetryBudgetExceededError: If retry budget exceeded
    """
    config = config or RetryConfig()
    budget = budget or RetryBudget()
    
    attempt = 0
    last_exception = None
    
    while attempt < config.max_attempts:
        # Check budget before retry
        if attempt > 0 and not budget.can_retry():
            raise RetryBudgetExceededError(
                f"Retry budget exceeded. "
                f"Used {budget.budget_used}/{budget.total_budget} in current window."
            )
        
        try:
            result = func(*args, **kwargs)
            return result  # Success!
        
        except retry_on as e:
            last_exception = e
            attempt += 1
            
            # Consume budget for retry
            if attempt < config.max_attempts:
                budget.consume()
            
            # Don't sleep after last attempt
            if attempt >= config.max_attempts:
                break
            
            # Calculate delay with exponential backoff
            delay = min(
                config.initial_delay_seconds * (config.exponential_base ** (attempt - 1)),
                config.max_delay_seconds
            )
            
            # Add jitter to prevent thundering herd
            if config.jitter:
                import random
                delay = delay * (0.5 + random.random())
            
            time.sleep(delay)
    
    # All retries exhausted
    raise RetryExhaustedError(
        f"All {config.max_attempts} retry attempts exhausted. "
        f"Last error: {last_exception}"
    ) from last_exception


# Global retry budgets for different operation types
_retry_budgets = {}


def get_retry_budget(operation_type: str) -> RetryBudget:
    """Get or create a retry budget for an operation type"""
    if operation_type not in _retry_budgets:
        _retry_budgets[operation_type] = RetryBudget()
    return _retry_budgets[operation_type]


def reset_all_budgets():
    """Reset all retry budgets (for testing)"""
    _retry_budgets.clear()


def get_budget_stats() -> dict:
    """Get statistics for all retry budgets"""
    return {
        name: {
            "used": budget.budget_used,
            "total": budget.total_budget,
            "remaining": budget.get_remaining(),
            "usage_percentage": budget.get_usage_percentage()
        }
        for name, budget in _retry_budgets.items()
    }

"""
Error Handling System

Comprehensive error handling with:
- Circuit breakers (prevent cascade failures)
- Retry budgets (prevent infinite retries)
- Fallback chains (graceful degradation)
- Better error messages (actionable errors)
"""

from zenus_core.error.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    get_circuit_breaker,
    reset_all_circuit_breakers
)

from zenus_core.error.retry_budget import (
    RetryBudget,
    RetryConfig,
    RetryExhaustedError,
    RetryBudgetExceededError,
    retry_with_budget,
    get_retry_budget,
    reset_all_budgets,
    get_budget_stats
)

from zenus_core.error.fallback import (
    Fallback,
    FallbackStrategy,
    FallbackOption,
    AllFallbacksFailedError,
    create_llm_fallback,
    get_fallback,
    register_fallback
)


__all__ = [
    # Circuit Breaker
    "CircuitBreaker",
    "CircuitState",
    "CircuitBreakerConfig",
    "CircuitBreakerOpenError",
    "get_circuit_breaker",
    "reset_all_circuit_breakers",
    
    # Retry Budget
    "RetryBudget",
    "RetryConfig",
    "RetryExhaustedError",
    "RetryBudgetExceededError",
    "retry_with_budget",
    "get_retry_budget",
    "reset_all_budgets",
    "get_budget_stats",
    
    # Fallback
    "Fallback",
    "FallbackStrategy",
    "FallbackOption",
    "AllFallbacksFailedError",
    "create_llm_fallback",
    "get_fallback",
    "register_fallback",
]

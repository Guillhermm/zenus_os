"""
Circuit Breaker Pattern

Prevents cascade failures by detecting failing services and stopping requests temporarily.
"""

import time
from enum import Enum
from typing import Callable, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"       # Normal operation
    OPEN = "open"           # Failure detected, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5          # Failures before opening
    timeout_seconds: float = 60.0       # Time to wait before half-open
    success_threshold: int = 2          # Successes in half-open to close
    window_seconds: float = 300.0       # Rolling window for failure count


@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker"""
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    total_requests: int = 0
    total_failures: int = 0
    total_successes: int = 0
    opened_at: Optional[datetime] = None


class CircuitBreaker:
    """
    Circuit Breaker for external services
    
    Prevents cascade failures by:
    - Tracking failure rates
    - Opening circuit after threshold failures
    - Testing recovery periodically
    - Closing circuit when service recovers
    
    States:
    - CLOSED: Normal operation, all requests go through
    - OPEN: Service failing, reject requests immediately
    - HALF_OPEN: Testing recovery, allow limited requests
    """
    
    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.stats = CircuitBreakerStats()
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection
        
        Raises:
            CircuitBreakerOpenError: If circuit is open
        """
        self.stats.total_requests += 1
        
        # Check if circuit is open
        if self.stats.state == CircuitState.OPEN:
            # Check if timeout expired (try half-open)
            if self._should_attempt_reset():
                self.stats.state = CircuitState.HALF_OPEN
                self.stats.success_count = 0
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is OPEN. "
                    f"Service unavailable. Try again later."
                )
        
        # Try to execute function
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Handle successful execution"""
        self.stats.total_successes += 1
        self.stats.last_success_time = datetime.now()
        
        if self.stats.state == CircuitState.HALF_OPEN:
            self.stats.success_count += 1
            
            # Close circuit if enough successes
            if self.stats.success_count >= self.config.success_threshold:
                self._close_circuit()
        
        elif self.stats.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.stats.failure_count = 0
    
    def _on_failure(self):
        """Handle failed execution"""
        self.stats.total_failures += 1
        self.stats.last_failure_time = datetime.now()
        
        if self.stats.state == CircuitState.HALF_OPEN:
            # Failure in half-open → reopen circuit
            self._open_circuit()
        
        elif self.stats.state == CircuitState.CLOSED:
            self.stats.failure_count += 1
            
            # Open circuit if threshold reached
            if self.stats.failure_count >= self.config.failure_threshold:
                self._open_circuit()
    
    def _open_circuit(self):
        """Open the circuit"""
        self.stats.state = CircuitState.OPEN
        self.stats.opened_at = datetime.now()
        self.stats.failure_count = 0
        self.stats.success_count = 0
    
    def _close_circuit(self):
        """Close the circuit"""
        self.stats.state = CircuitState.CLOSED
        self.stats.failure_count = 0
        self.stats.success_count = 0
        self.stats.opened_at = None
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit should try to reset"""
        if not self.stats.opened_at:
            return False
        
        elapsed = (datetime.now() - self.stats.opened_at).total_seconds()
        return elapsed >= self.config.timeout_seconds
    
    def reset(self):
        """Manually reset circuit breaker"""
        self._close_circuit()
    
    def get_state(self) -> CircuitState:
        """Get current circuit state"""
        return self.stats.state
    
    def get_stats(self) -> dict:
        """Get circuit breaker statistics"""
        return {
            "name": self.name,
            "state": self.stats.state.value,
            "failure_count": self.stats.failure_count,
            "success_count": self.stats.success_count,
            "total_requests": self.stats.total_requests,
            "total_failures": self.stats.total_failures,
            "total_successes": self.stats.total_successes,
            "failure_rate": (
                self.stats.total_failures / self.stats.total_requests
                if self.stats.total_requests > 0 else 0.0
            ),
            "last_failure": (
                self.stats.last_failure_time.isoformat()
                if self.stats.last_failure_time else None
            ),
            "last_success": (
                self.stats.last_success_time.isoformat()
                if self.stats.last_success_time else None
            )
        }


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass


# Global circuit breakers for different services
_circuit_breakers = {}


def get_circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
    """Get or create a circuit breaker for a service"""
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name, config)
    return _circuit_breakers[name]


def reset_all_circuit_breakers():
    """Reset all circuit breakers (for testing)"""
    for cb in _circuit_breakers.values():
        cb.reset()

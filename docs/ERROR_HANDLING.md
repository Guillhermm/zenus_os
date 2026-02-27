# Error Handling Guide

**Status**: ✅ Complete | **Phase**: Foundation Hardening

Production-grade error handling with circuit breakers, retry budgets, and graceful fallbacks.

## 🎯 Goals

1. **Prevent cascade failures** - Circuit breakers stop requests to failing services
2. **Prevent infinite retries** - Retry budgets limit retry attempts
3. **Graceful degradation** - Fallback chains provide alternatives when services fail
4. **Better error messages** - Clear, actionable error messages

## 🔌 Circuit Breakers

Circuit breakers prevent cascade failures by detecting failing services and temporarily stopping requests.

### States

```
CLOSED ──failure threshold──> OPEN ──timeout──> HALF_OPEN ──success──> CLOSED
   │                            │                     │
   │                            │                     └──failure──> OPEN
   │                            └──immediate failure for all requests
   └──normal operation
```

- **CLOSED**: Normal operation, all requests go through
- **OPEN**: Service failing, reject requests immediately (fast-fail)
- **HALF_OPEN**: Testing recovery, allow limited requests

### Usage

```python
from zenus_core.error import get_circuit_breaker, CircuitBreakerOpenError

# Get circuit breaker for a service
cb = get_circuit_breaker("anthropic_api")

try:
    result = cb.call(call_anthropic_api, prompt="Hello")
except CircuitBreakerOpenError:
    # Circuit is open - service unavailable
    print("Anthropic API unavailable, using fallback")
    result = call_fallback_llm(prompt="Hello")
```

### Configuration

```python
from zenus_core.error import CircuitBreakerConfig, get_circuit_breaker

config = CircuitBreakerConfig(
    failure_threshold=5,        # Open after 5 failures
    timeout_seconds=60.0,       # Try reset after 60s
    success_threshold=2,        # Close after 2 successes in half-open
    window_seconds=300.0        # 5-minute rolling window
)

cb = get_circuit_breaker("my_service", config)
```

### Monitoring

```python
# Get circuit breaker stats
stats = cb.get_stats()
print(f"State: {stats['state']}")
print(f"Failure rate: {stats['failure_rate']:.2%}")
print(f"Total requests: {stats['total_requests']}")
```

## ⚡ Retry Budgets

Retry budgets prevent infinite retries by allocating a budget for retry attempts per time window.

### Usage

```python
from zenus_core.error import retry_with_budget, RetryConfig, get_retry_budget

# Get retry budget for operation type
budget = get_retry_budget("llm_calls")

# Configure retry behavior
config = RetryConfig(
    max_attempts=3,               # Max 3 attempts
    initial_delay_seconds=1.0,    # Start with 1s delay
    max_delay_seconds=30.0,       # Cap at 30s
    exponential_base=2.0,         # Double delay each time
    jitter=True                   # Add randomness to prevent thundering herd
)

# Execute with retry
result = retry_with_budget(
    call_api,
    url="https://api.example.com",
    config=config,
    budget=budget,
    retry_on=(ConnectionError, TimeoutError)  # Only retry these
)
```

### Delay Calculation

With exponential backoff:
- Attempt 1: 0s (immediate)
- Attempt 2: ~1s (1.0 * 2^0 * jitter)
- Attempt 3: ~2s (1.0 * 2^1 * jitter)
- Attempt 4: ~4s (1.0 * 2^2 * jitter)

Jitter adds 50-150% randomness to prevent synchronized retries (thundering herd).

### Budget Tracking

```python
from zenus_core.error import get_budget_stats

# Get statistics for all budgets
stats = get_budget_stats()

for name, budget_stats in stats.items():
    print(f"{name}:")
    print(f"  Used: {budget_stats['used']}/{budget_stats['total']}")
    print(f"  Remaining: {budget_stats['remaining']}")
    print(f"  Usage: {budget_stats['usage_percentage']:.1f}%")
```

### Budget Exhaustion

```python
from zenus_core.error import retry_with_budget, RetryBudgetExceededError

try:
    result = retry_with_budget(call_api, ...)
except RetryBudgetExceededError as e:
    # Retry budget exhausted - too many retries in window
    print("Retry budget exceeded - service may be down")
    # Use fallback or alert
```

## 🔄 Fallback Chains

Graceful degradation with automatic fallback to alternative implementations.

### Usage

```python
from zenus_core.error import Fallback, FallbackStrategy

# Create fallback chain
fallback = Fallback("llm", FallbackStrategy.CASCADE)

# Add options (highest priority first)
fallback.add_option("claude", call_claude, priority=3)
fallback.add_option("deepseek", call_deepseek, priority=2)
fallback.add_option("local", call_local_model, priority=1)

# Execute with automatic fallback
result = fallback.execute(prompt="Hello, world!")
# Tries: Claude → DeepSeek → Local (stops at first success)
```

### LLM Fallback Chain

Built-in LLM fallback:

```python
from zenus_core.error import get_fallback

llm_fallback = get_fallback("llm")
result = llm_fallback.execute(prompt="Translate Python to Rust")

# Automatically tries:
# 1. Claude (best quality)
# 2. DeepSeek (fast and cheap)
# 3. Rule-based (keyword matching, always works)
```

### Custom Fallbacks

```python
fallback = Fallback("database", FallbackStrategy.CASCADE)

# Primary: PostgreSQL
fallback.add_option(
    "postgres",
    lambda query: postgres.execute(query),
    priority=3
)

# Secondary: SQLite
fallback.add_option(
    "sqlite",
    lambda query: sqlite.execute(query),
    priority=2
)

# Tertiary: In-memory cache
fallback.add_option(
    "cache",
    lambda query: cache.get(query_hash(query)),
    priority=1
)

result = fallback.execute("SELECT * FROM users")
```

### Monitoring Fallbacks

```python
stats = fallback.get_stats()
print(f"Strategy: {stats['strategy']}")
print(f"Options: {stats['options']}")
print(f"Last successful: {stats['last_successful']}")
```

## 🔗 Combining Patterns

Use all three patterns together for maximum resilience:

```python
from zenus_core.error import (
    get_circuit_breaker,
    retry_with_budget,
    get_fallback,
    RetryConfig,
    get_retry_budget
)

def robust_llm_call(prompt: str) -> str:
    """
    Ultra-robust LLM call with:
    - Circuit breaker (prevent cascade failures)
    - Retry budget (prevent infinite retries)
    - Fallback chain (graceful degradation)
    """
    
    # Get circuit breaker
    cb = get_circuit_breaker("llm_api")
    
    # Get retry budget
    budget = get_retry_budget("llm_calls")
    config = RetryConfig(max_attempts=3)
    
    # Get fallback chain
    fallback = get_fallback("llm")
    
    try:
        # Try primary with circuit breaker + retry
        return retry_with_budget(
            lambda p: cb.call(fallback.execute, prompt=p),
            prompt,
            config=config,
            budget=budget
        )
    
    except Exception as e:
        # Last resort: rule-based fallback
        return f"Error: {e}. Please rephrase your request."
```

## 📊 Error Messages

### Bad Error Messages
```python
# ❌ Not actionable
raise Exception("Error")

# ❌ No context
raise ValueError("Invalid value")

# ❌ Technical jargon
raise RuntimeError("ECONNREFUSED 127.0.0.1:5432")
```

### Good Error Messages
```python
# ✅ Clear, actionable, with context
raise ValueError(
    f"Invalid file path: '{path}'. "
    f"Path must be absolute and exist. "
    f"Try using os.path.abspath() or check if file exists."
)

# ✅ User-friendly
raise ConnectionError(
    "Cannot connect to PostgreSQL database. "
    "Check that:\n"
    "  1. PostgreSQL is running (sudo systemctl status postgresql)\n"
    "  2. Connection details are correct in .env\n"
    "  3. Firewall allows connections (sudo ufw status)"
)

# ✅ With recovery suggestions
raise RetryBudgetExceededError(
    f"Retry budget exceeded for 'llm_calls'. "
    f"Used {budget.budget_used}/{budget.total_budget} retries in {budget.window_seconds}s window. "
    f"The service may be down. Try again later or use a different provider."
)
```

## 🎯 Best Practices

### 1. Use Circuit Breakers for External Services
```python
# Good: Protect external API calls
cb = get_circuit_breaker("github_api")
result = cb.call(call_github_api, repo="zenus")

# Bad: No protection against failures
result = call_github_api(repo="zenus")  # Might hang forever
```

### 2. Set Retry Budgets by Operation Type
```python
# Good: Separate budgets for different operations
llm_budget = get_retry_budget("llm_calls")
db_budget = get_retry_budget("db_queries")

# Bad: Global retry count (affects all operations)
retry_count = 0  # Global counter
```

### 3. Chain Fallbacks by Quality/Speed
```python
# Good: Best quality first, fastest last
fallback.add_option("claude", call_claude, priority=3)    # Slow, best
fallback.add_option("deepseek", call_deepseek, priority=2)  # Fast, good
fallback.add_option("local", call_local, priority=1)      # Instant, okay

# Bad: Random order
fallback.add_option("local", call_local, priority=3)  # Why is worst first?
```

### 4. Fail Fast with Circuit Breakers
```python
# Good: Check circuit state before expensive operation
if cb.get_state() == CircuitState.OPEN:
    return use_fallback()

# Bad: Always try expensive operation
try:
    return expensive_api_call()  # Might timeout
except:
    return use_fallback()
```

## 🚨 Common Pitfalls

### 1. Retrying Non-Transient Errors
```python
# Bad: Retrying validation errors (won't succeed)
retry_with_budget(
    parse_json,
    data=malformed_json,
    retry_on=(Exception,)  # Includes ValueError!
)

# Good: Only retry transient errors
retry_with_budget(
    call_api,
    url=endpoint,
    retry_on=(ConnectionError, TimeoutError)  # Transient only
)
```

### 2. No Circuit Breaker Timeout
```python
# Bad: Circuit never resets
config = CircuitBreakerConfig(timeout_seconds=float('inf'))

# Good: Reset after reasonable time
config = CircuitBreakerConfig(timeout_seconds=60.0)
```

### 3. Unlimited Retry Budget
```python
# Bad: Can retry forever
budget = RetryBudget(total_budget=999999)

# Good: Reasonable limit
budget = RetryBudget(total_budget=100, window_seconds=600)
```

## 📈 Monitoring

### Circuit Breaker Dashboard
```python
from zenus_core.error import _circuit_breakers

for name, cb in _circuit_breakers.items():
    stats = cb.get_stats()
    print(f"{name}:")
    print(f"  State: {stats['state']}")
    print(f"  Failure rate: {stats['failure_rate']:.2%}")
```

### Retry Budget Dashboard
```python
from zenus_core.error import get_budget_stats

for name, stats in get_budget_stats().items():
    if stats['usage_percentage'] > 80:
        print(f"⚠️  {name} budget at {stats['usage_percentage']:.1f}%")
```

---

**Production Checklist:**
- ✅ Circuit breakers for all external services
- ✅ Retry budgets for all retry logic
- ✅ Fallback chains for critical paths
- ✅ Actionable error messages
- ✅ Monitoring dashboards
- ✅ Alerting on high failure rates

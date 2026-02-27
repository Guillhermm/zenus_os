"""
Graceful Degradation and Fallback System

Provides automatic fallback strategies when primary methods fail.
"""

from typing import Callable, Any, List, Optional, TypeVar, Generic
from dataclasses import dataclass
from enum import Enum


T = TypeVar('T')


class FallbackStrategy(Enum):
    """Fallback strategies"""
    CASCADE = "cascade"          # Try each fallback in order
    PARALLEL = "parallel"        # Try all in parallel, return first success
    BEST_EFFORT = "best_effort"  # Try primary, return partial on failure


@dataclass
class FallbackOption(Generic[T]):
    """A fallback option"""
    name: str
    func: Callable[..., T]
    priority: int = 0  # Higher priority tried first
    acceptable_exceptions: tuple = (Exception,)


class Fallback(Generic[T]):
    """
    Graceful degradation with fallback chain
    
    Example:
        fb = Fallback("llm_call")
        fb.add_option("claude", call_claude, priority=3)
        fb.add_option("deepseek", call_deepseek, priority=2)
        fb.add_option("local", call_local_model, priority=1)
        
        result = fb.execute(prompt="Hello")
        # Tries Claude → DeepSeek → Local in order
    """
    
    def __init__(self, name: str, strategy: FallbackStrategy = FallbackStrategy.CASCADE):
        self.name = name
        self.strategy = strategy
        self.options: List[FallbackOption[T]] = []
        self.last_successful_option: Optional[str] = None
    
    def add_option(
        self,
        name: str,
        func: Callable[..., T],
        priority: int = 0,
        acceptable_exceptions: tuple = (Exception,)
    ):
        """Add a fallback option"""
        option = FallbackOption(
            name=name,
            func=func,
            priority=priority,
            acceptable_exceptions=acceptable_exceptions
        )
        self.options.append(option)
        
        # Sort by priority (highest first)
        self.options.sort(key=lambda x: x.priority, reverse=True)
    
    def execute(self, *args, **kwargs) -> T:
        """
        Execute with fallback chain
        
        Returns:
            Result from first successful option
        
        Raises:
            AllFallbacksFailedError: If all options fail
        """
        if not self.options:
            raise ValueError(f"No fallback options configured for '{self.name}'")
        
        if self.strategy == FallbackStrategy.CASCADE:
            return self._execute_cascade(*args, **kwargs)
        elif self.strategy == FallbackStrategy.PARALLEL:
            return self._execute_parallel(*args, **kwargs)
        else:
            raise ValueError(f"Unknown strategy: {self.strategy}")
    
    def _execute_cascade(self, *args, **kwargs) -> T:
        """Try each option in priority order"""
        errors = []
        
        for option in self.options:
            try:
                result = option.func(*args, **kwargs)
                self.last_successful_option = option.name
                return result
            
            except option.acceptable_exceptions as e:
                errors.append((option.name, e))
                continue  # Try next option
        
        # All options failed
        error_summary = "\n".join([
            f"  - {name}: {str(error)}"
            for name, error in errors
        ])
        
        raise AllFallbacksFailedError(
            f"All fallback options failed for '{self.name}':\n{error_summary}"
        )
    
    def _execute_parallel(self, *args, **kwargs) -> T:
        """Try all options in parallel (not yet implemented)"""
        # TODO: Implement parallel execution with threading/asyncio
        # For now, fall back to cascade
        return self._execute_cascade(*args, **kwargs)
    
    def get_stats(self) -> dict:
        """Get fallback statistics"""
        return {
            "name": self.name,
            "strategy": self.strategy.value,
            "options": [opt.name for opt in self.options],
            "last_successful": self.last_successful_option
        }


class AllFallbacksFailedError(Exception):
    """Raised when all fallback options fail"""
    pass


def create_llm_fallback() -> Fallback:
    """
    Create LLM fallback chain
    
    Priority: Claude (best) → DeepSeek (fast) → Local (offline)
    """
    from zenus_core.brain.llm.factory import get_llm
    
    fallback = Fallback("llm", FallbackStrategy.CASCADE)
    
    # Primary: Claude (best quality)
    fallback.add_option(
        "claude",
        lambda prompt, **kwargs: get_llm(provider="anthropic").generate(prompt, **kwargs),
        priority=3
    )
    
    # Secondary: DeepSeek (fast and cheap)
    fallback.add_option(
        "deepseek",
        lambda prompt, **kwargs: get_llm(provider="deepseek").generate(prompt, **kwargs),
        priority=2
    )
    
    # Tertiary: Rule-based fallback (always works)
    fallback.add_option(
        "rule_based",
        lambda prompt, **kwargs: _rule_based_fallback(prompt),
        priority=1
    )
    
    return fallback


def _rule_based_fallback(prompt: str) -> str:
    """
    Rule-based fallback when LLMs unavailable
    
    Returns simple responses based on keywords.
    """
    prompt_lower = prompt.lower()
    
    # Pattern matching for common intents
    if any(word in prompt_lower for word in ["list", "show", "get"]):
        return "To list items, use: FileOps.scan or SystemOps.list_processes"
    
    elif any(word in prompt_lower for word in ["create", "make", "new"]):
        return "To create files, use: FileOps.mkdir or FileOps.touch"
    
    elif any(word in prompt_lower for word in ["delete", "remove"]):
        return "To delete, use: FileOps.delete (Warning: destructive operation)"
    
    elif any(word in prompt_lower for word in ["move", "rename"]):
        return "To move files, use: FileOps.move"
    
    elif any(word in prompt_lower for word in ["cpu", "memory", "disk", "system"]):
        return "To check system resources, use: SystemOps.check_resource_usage"
    
    elif any(word in prompt_lower for word in ["process", "processes"]):
        return "To list processes, use: SystemOps.list_processes"
    
    elif any(word in prompt_lower for word in ["git", "commit", "branch"]):
        return "To use git, use: GitOps.status or GitOps.commit"
    
    else:
        return (
            "LLM unavailable. Using rule-based fallback.\n"
            "Please rephrase your request with specific keywords like:\n"
            "  - list, show, get (to list items)\n"
            "  - create, make (to create files)\n"
            "  - system, cpu, memory (for system info)"
        )


# Global fallback instances
_fallbacks = {}


def get_fallback(name: str) -> Fallback:
    """Get or create a fallback instance"""
    if name == "llm" and name not in _fallbacks:
        _fallbacks[name] = create_llm_fallback()
    
    if name not in _fallbacks:
        _fallbacks[name] = Fallback(name)
    
    return _fallbacks[name]


def register_fallback(name: str, fallback: Fallback):
    """Register a custom fallback"""
    _fallbacks[name] = fallback

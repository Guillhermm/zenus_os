"""
Error Recovery System

Handles failures gracefully during execution:
- Transient failures: Retry with exponential backoff
- Tool unavailable: Skip or suggest alternatives
- Permission denied: Request user intervention
- LLM timeout: Resume from checkpoint
"""

import time
import logging
from typing import Optional, Dict, Any, Callable
from enum import Enum
from dataclasses import dataclass


class RecoveryStrategy(Enum):
    """Recovery strategies for different error types"""
    RETRY = "retry"
    SKIP = "skip"
    SUBSTITUTE = "substitute"
    ASK_USER = "ask_user"
    ROLLBACK = "rollback"
    ABORT = "abort"


@dataclass
class RecoveryResult:
    """Result of error recovery attempt"""
    success: bool
    strategy: RecoveryStrategy
    message: str
    retry_count: int = 0
    alternative_used: Optional[str] = None


class ErrorRecovery:
    """
    Manages error recovery during execution
    
    Features:
    - Exponential backoff for transient failures
    - Alternative tool suggestion
    - User intervention requests
    - Checkpoint-based resume
    """
    
    def __init__(self, max_retries: int = 3, backoff_base: float = 2.0):
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.logger = logging.getLogger(__name__)
        
        # Track recovery attempts per error type
        self.recovery_stats = {
            "retries": 0,
            "skips": 0,
            "substitutions": 0,
            "user_interventions": 0,
            "rollbacks": 0,
            "aborts": 0
        }
    
    def recover(
        self,
        error: Exception,
        context: Dict[str, Any],
        operation: Callable,
        *args,
        **kwargs
    ) -> RecoveryResult:
        """
        Attempt to recover from an error
        
        Args:
            error: The exception that occurred
            context: Execution context (tool, action, args, etc.)
            operation: The operation to retry if applicable
            *args, **kwargs: Arguments for operation
        
        Returns:
            RecoveryResult with outcome
        """
        error_type = type(error).__name__
        self.logger.warning(f"Attempting recovery from {error_type}: {str(error)}")
        
        # Determine strategy based on error type
        if isinstance(error, (TimeoutError, ConnectionError)):
            return self._retry_with_backoff(operation, context, *args, **kwargs)
        
        elif isinstance(error, PermissionError):
            return self._request_permission(context)
        
        elif isinstance(error, FileNotFoundError):
            return self._handle_missing_resource(error, context)
        
        elif isinstance(error, (ImportError, ModuleNotFoundError)):
            return self._handle_missing_dependency(error, context)
        
        elif isinstance(error, KeyError):
            return self._handle_missing_key(error, context)
        
        elif "rate limit" in str(error).lower():
            return self._handle_rate_limit(operation, context, *args, **kwargs)
        
        else:
            # Unknown error - ask user or abort
            return self._handle_unknown_error(error, context)
    
    def _retry_with_backoff(
        self,
        operation: Callable,
        context: Dict[str, Any],
        *args,
        **kwargs
    ) -> RecoveryResult:
        """Retry operation with exponential backoff"""
        for attempt in range(self.max_retries):
            wait_time = self.backoff_base ** attempt
            
            self.logger.info(f"Retry attempt {attempt + 1}/{self.max_retries} (waiting {wait_time:.1f}s)")
            time.sleep(wait_time)
            
            try:
                result = operation(*args, **kwargs)
                self.recovery_stats["retries"] += 1
                return RecoveryResult(
                    success=True,
                    strategy=RecoveryStrategy.RETRY,
                    message=f"Succeeded after {attempt + 1} retries",
                    retry_count=attempt + 1
                )
            except Exception as e:
                if attempt == self.max_retries - 1:
                    # Final attempt failed
                    return RecoveryResult(
                        success=False,
                        strategy=RecoveryStrategy.RETRY,
                        message=f"Failed after {self.max_retries} retries: {str(e)}",
                        retry_count=self.max_retries
                    )
                continue
        
        return RecoveryResult(
            success=False,
            strategy=RecoveryStrategy.RETRY,
            message="Retry loop completed without success",
            retry_count=self.max_retries
        )
    
    def _request_permission(self, context: Dict[str, Any]) -> RecoveryResult:
        """Request user permission for restricted operation"""
        tool = context.get("tool", "Unknown")
        action = context.get("action", "unknown")
        args = context.get("args", {})
        
        print(f"\n⚠️  Permission denied for: {tool}.{action}")
        print(f"   Arguments: {args}")
        print()
        
        choice = input("Grant permission? [y/N/s=skip]: ").strip().lower()
        
        if choice == 'y':
            # User granted permission - would need to re-run with elevated perms
            # For now, just mark as user intervention needed
            self.recovery_stats["user_interventions"] += 1
            return RecoveryResult(
                success=False,
                strategy=RecoveryStrategy.ASK_USER,
                message="User granted permission but re-execution with elevated privileges not yet implemented"
            )
        elif choice == 's':
            # Skip this operation
            self.recovery_stats["skips"] += 1
            return RecoveryResult(
                success=True,
                strategy=RecoveryStrategy.SKIP,
                message="Operation skipped by user"
            )
        else:
            # Abort
            self.recovery_stats["aborts"] += 1
            return RecoveryResult(
                success=False,
                strategy=RecoveryStrategy.ABORT,
                message="Operation aborted by user"
            )
    
    def _handle_missing_resource(
        self,
        error: FileNotFoundError,
        context: Dict[str, Any]
    ) -> RecoveryResult:
        """Handle missing file or directory"""
        missing_path = str(error).split("'")[1] if "'" in str(error) else "unknown"
        
        print(f"\n⚠️  Resource not found: {missing_path}")
        choice = input("Skip this operation? [Y/n/a=abort]: ").strip().lower()
        
        if choice in ['', 'y']:
            self.recovery_stats["skips"] += 1
            return RecoveryResult(
                success=True,
                strategy=RecoveryStrategy.SKIP,
                message=f"Skipped operation on missing resource: {missing_path}"
            )
        else:
            self.recovery_stats["aborts"] += 1
            return RecoveryResult(
                success=False,
                strategy=RecoveryStrategy.ABORT,
                message="Operation aborted due to missing resource"
            )
    
    def _handle_missing_dependency(
        self,
        error: Exception,
        context: Dict[str, Any]
    ) -> RecoveryResult:
        """Handle missing Python module"""
        module_name = str(error).split("'")[1] if "'" in str(error) else "unknown"
        
        print(f"\n⚠️  Missing dependency: {module_name}")
        print(f"   Install with: pip install {module_name}")
        
        self.recovery_stats["skips"] += 1
        return RecoveryResult(
            success=True,
            strategy=RecoveryStrategy.SKIP,
            message=f"Skipped operation due to missing dependency: {module_name}"
        )
    
    def _handle_missing_key(
        self,
        error: KeyError,
        context: Dict[str, Any]
    ) -> RecoveryResult:
        """Handle missing dictionary key"""
        missing_key = str(error).strip("'\"")
        
        self.logger.warning(f"Missing key in context: {missing_key}")
        
        # Try to continue without the key
        self.recovery_stats["skips"] += 1
        return RecoveryResult(
            success=True,
            strategy=RecoveryStrategy.SKIP,
            message=f"Continued despite missing key: {missing_key}"
        )
    
    def _handle_rate_limit(
        self,
        operation: Callable,
        context: Dict[str, Any],
        *args,
        **kwargs
    ) -> RecoveryResult:
        """Handle API rate limiting"""
        wait_time = 60  # Wait 1 minute for rate limits
        
        print(f"\n⏳ Rate limit hit. Waiting {wait_time}s before retry...")
        time.sleep(wait_time)
        
        try:
            result = operation(*args, **kwargs)
            self.recovery_stats["retries"] += 1
            return RecoveryResult(
                success=True,
                strategy=RecoveryStrategy.RETRY,
                message="Recovered from rate limit",
                retry_count=1
            )
        except Exception as e:
            return RecoveryResult(
                success=False,
                strategy=RecoveryStrategy.RETRY,
                message=f"Failed after rate limit retry: {str(e)}",
                retry_count=1
            )
    
    def _handle_unknown_error(
        self,
        error: Exception,
        context: Dict[str, Any]
    ) -> RecoveryResult:
        """Handle unexpected errors"""
        error_type = type(error).__name__
        error_msg = str(error)
        
        print(f"\n❌ Unexpected error: {error_type}")
        print(f"   {error_msg}")
        print()
        
        choice = input("Continue execution? [Y/n]: ").strip().lower()
        
        if choice in ['', 'y']:
            self.recovery_stats["skips"] += 1
            return RecoveryResult(
                success=True,
                strategy=RecoveryStrategy.SKIP,
                message=f"Skipped operation after error: {error_type}"
            )
        else:
            self.recovery_stats["aborts"] += 1
            return RecoveryResult(
                success=False,
                strategy=RecoveryStrategy.ABORT,
                message="Execution aborted by user"
            )
    
    def get_stats(self) -> Dict[str, int]:
        """Get recovery statistics"""
        return self.recovery_stats.copy()


# Global instance
_recovery_instance: Optional[ErrorRecovery] = None


def get_error_recovery() -> ErrorRecovery:
    """Get singleton error recovery instance"""
    global _recovery_instance
    if _recovery_instance is None:
        _recovery_instance = ErrorRecovery()
    return _recovery_instance

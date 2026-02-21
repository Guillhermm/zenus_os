"""
Sandboxed Executor

Executes operations within defined constraints.
Currently provides constraint validation; future versions will
add process isolation via containers/namespaces.
"""

import time
import signal
from typing import Callable, Any, Optional
from contextlib import contextmanager
from zenus_core.sandbox.constraints import SandboxConstraints, get_safe_defaults


class SandboxViolation(Exception):
    """Raised when operation violates sandbox constraints"""
    pass


class SandboxTimeout(SandboxViolation):
    """Raised when operation exceeds time limit"""
    pass


class SandboxExecutor:
    """
    Execute operations within sandbox constraints
    
    Current implementation: validation layer
    Future: process isolation via firejail/bubblewrap/containers
    """
    
    def __init__(self, constraints: Optional[SandboxConstraints] = None):
        self.constraints = constraints or get_safe_defaults()
        self.execution_start = None
    
    def execute(
        self, 
        func: Callable, 
        *args,
        check_paths: bool = True,
        **kwargs
    ) -> Any:
        """
        Execute function within sandbox constraints
        
        Args:
            func: Function to execute
            *args, **kwargs: Function arguments
            check_paths: Whether to validate path arguments
        
        Returns:
            Function result
        
        Raises:
            SandboxViolation: If constraints are violated
        """
        
        # Pre-execution validation
        if check_paths:
            self._validate_path_arguments(args, kwargs)
        
        # Set up timeout if specified
        if self.constraints.max_execution_time:
            with self._timeout_context(self.constraints.max_execution_time):
                return func(*args, **kwargs)
        else:
            return func(*args, **kwargs)
    
    def _validate_path_arguments(self, args: tuple, kwargs: dict):
        """
        Validate path arguments against constraints
        
        Looks for common path argument names and validates them
        """
        # Check common path parameter names
        path_params = ["path", "source", "destination", "src", "dst", "file", "directory"]
        
        for param in path_params:
            if param in kwargs:
                path = kwargs[param]
                if isinstance(path, str):
                    # Determine if this is read or write operation
                    # Heuristic: source/file -> read, destination/dst -> write
                    is_write = param in ["destination", "dst"]
                    self.validate_path_access(path, is_write)
    
    def validate_path_access(self, path: str, is_write: bool = False):
        """
        Validate that path access is allowed
        
        Args:
            path: Path to validate
            is_write: Whether this is a write operation
        
        Raises:
            SandboxViolation: If access is not allowed
        """
        if is_write:
            if not self.constraints.can_write(path):
                raise SandboxViolation(
                    f"Write access denied: {path}\n"
                    f"Allowed write paths: {self.constraints.allowed_write_paths}"
                )
        else:
            if not self.constraints.can_read(path):
                raise SandboxViolation(
                    f"Read access denied: {path}\n"
                    f"Allowed read paths: {self.constraints.allowed_read_paths or 'any'}"
                )
    
    def validate_network_access(self, host: Optional[str] = None):
        """Validate network access is allowed"""
        if not self.constraints.allow_network:
            raise SandboxViolation("Network access not allowed in this sandbox")
        
        if host and self.constraints.allowed_hosts:
            if host not in self.constraints.allowed_hosts:
                raise SandboxViolation(
                    f"Access to host {host} not allowed. "
                    f"Allowed: {self.constraints.allowed_hosts}"
                )
    
    def validate_subprocess(self):
        """Validate subprocess execution is allowed"""
        if not self.constraints.allow_subprocess:
            raise SandboxViolation("Subprocess execution not allowed in this sandbox")
    
    @contextmanager
    def _timeout_context(self, timeout_seconds: int):
        """Context manager for execution timeout"""
        
        def timeout_handler(signum, frame):
            raise SandboxTimeout(
                f"Operation exceeded time limit of {timeout_seconds}s"
            )
        
        # Set alarm
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout_seconds)
        
        try:
            yield
        finally:
            # Cancel alarm
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
    
    def get_remaining_time(self) -> Optional[float]:
        """Get remaining execution time in seconds"""
        if not self.constraints.max_execution_time or not self.execution_start:
            return None
        
        elapsed = time.time() - self.execution_start
        remaining = self.constraints.max_execution_time - elapsed
        return max(0, remaining)


class SandboxedTool:
    """
    Base class for sandboxed tools
    
    Tools that inherit from this get automatic sandboxing
    """
    
    def __init__(self, constraints: Optional[SandboxConstraints] = None):
        self.sandbox = SandboxExecutor(constraints)
    
    def execute_safe(self, method: Callable, *args, **kwargs) -> Any:
        """Execute method with sandbox constraints"""
        return self.sandbox.execute(method, *args, **kwargs)

"""
Parallel Executor

Executes independent operations concurrently for performance.

Responsibilities:
- Execute steps in parallel where safe
- Manage thread/process pools
- Handle partial failures gracefully
- Respect resource limits
"""

import concurrent.futures
from typing import List, Dict, Any, Optional, Callable
from zenus_core.brain.llm.schemas import IntentIR, Step
from zenus_core.brain.dependency_analyzer import DependencyAnalyzer
from zenus_core.audit.logger import get_logger
from zenus_core.cli.formatter import console
import time
from dataclasses import dataclass


@dataclass
class ExecutionResult:
    """Result of executing a step"""
    step_index: int
    success: bool
    result: Any
    error: Optional[Exception] = None
    duration_ms: int = 0


class ParallelExecutor:
    """
    Executes steps in parallel while respecting dependencies
    
    Features:
    - Concurrent execution of independent steps
    - Dependency-aware scheduling
    - Resource management
    - Graceful error handling
    """
    
    def __init__(
        self,
        max_workers: int = 4,
        timeout_seconds: int = 300
    ):
        """
        Initialize parallel executor
        
        Args:
            max_workers: Maximum concurrent operations
            timeout_seconds: Timeout for each operation
        """
        self.max_workers = max_workers
        self.timeout_seconds = timeout_seconds
        self.analyzer = DependencyAnalyzer()
        self.logger = get_logger()
    
    def execute(
        self,
        intent: IntentIR,
        executor_func: Callable[[Step], Any]
    ) -> List[Any]:
        """
        Execute intent with parallel execution where possible
        
        Args:
            intent: Intent IR to execute
            executor_func: Function to execute a single step
        
        Returns:
            List of results (one per step, in original order)
        """
        steps = intent.steps
        n = len(steps)
        
        if n == 0:
            return []
        
        if n == 1:
            # Single step - no parallelization needed
            return [executor_func(steps[0])]
        
        # Analyze dependencies
        execution_order = self.analyzer.get_execution_order(intent)
        
        # Check if parallelization would help
        if not any(len(level) > 1 for level in execution_order):
            # All sequential - no benefit from parallelization
            self.logger.log_info("All steps sequential - executing without parallelization")
            return [executor_func(step) for step in steps]
        
        # Show parallel execution plan
        speedup = self.analyzer.estimate_speedup(intent)
        console.print(f"[dim]Using parallel execution (estimated {speedup:.1f}x speedup)[/dim]")
        
        # Execute level by level
        results = [None] * n  # Pre-allocate results array
        
        for level_idx, level in enumerate(execution_order, 1):
            if len(level) == 1:
                # Single step in this level - execute directly
                step_idx = level[0]
                step = steps[step_idx]
                
                try:
                    result = executor_func(step)
                    results[step_idx] = result
                except Exception as e:
                    self.logger.log_error(f"Step {step_idx} failed: {e}")
                    results[step_idx] = {"error": str(e)}
            else:
                # Multiple steps in this level - execute in parallel
                console.print(f"[dim]  Level {level_idx}: executing {len(level)} steps in parallel[/dim]")
                
                level_results = self._execute_level_parallel(
                    level,
                    steps,
                    executor_func
                )
                
                # Store results
                for step_idx, result in level_results.items():
                    results[step_idx] = result
        
        return results
    
    def _execute_level_parallel(
        self,
        level: List[int],
        steps: List[Step],
        executor_func: Callable[[Step], Any]
    ) -> Dict[int, Any]:
        """
        Execute a level of steps in parallel
        
        Args:
            level: List of step indices to execute
            steps: All steps
            executor_func: Function to execute a step
        
        Returns:
            Dictionary mapping step_index -> result
        """
        results = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            futures = {}
            for step_idx in level:
                step = steps[step_idx]
                future = executor.submit(self._execute_step_safe, step, executor_func)
                futures[future] = step_idx
            
            # Wait for completion
            for future in concurrent.futures.as_completed(futures, timeout=self.timeout_seconds):
                step_idx = futures[future]
                
                try:
                    result = future.result()
                    results[step_idx] = result
                except Exception as e:
                    self.logger.log_error(f"Step {step_idx} failed: {e}")
                    results[step_idx] = {"error": str(e)}
        
        return results
    
    def _execute_step_safe(
        self,
        step: Step,
        executor_func: Callable[[Step], Any]
    ) -> Any:
        """
        Execute a step with error handling
        
        Args:
            step: Step to execute
            executor_func: Execution function
        
        Returns:
            Execution result
        """
        start_time = time.time()
        
        try:
            result = executor_func(step)
            duration_ms = int((time.time() - start_time) * 1000)
            
            self.logger.log_info(
                f"Step completed: {step.tool}.{step.action} ({duration_ms}ms)"
            )
            
            return result
        
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            
            self.logger.log_error(
                f"Step failed: {step.tool}.{step.action} - {str(e)} ({duration_ms}ms)"
            )
            
            raise
    
    def should_use_parallel(self, intent: IntentIR) -> bool:
        """
        Determine if parallel execution would be beneficial
        
        Args:
            intent: Intent to analyze
        
        Returns:
            True if parallel execution recommended
        """
        # Need at least 2 steps
        if len(intent.steps) < 2:
            return False
        
        # Check if parallelizable
        if not self.analyzer.is_parallelizable(intent):
            return False
        
        # Check if speedup is significant
        speedup = self.analyzer.estimate_speedup(intent)
        if speedup < 1.3:  # Less than 30% speedup - not worth complexity
            return False
        
        return True
    
    def visualize_execution_plan(self, intent: IntentIR) -> str:
        """
        Generate visualization of parallel execution plan
        
        Args:
            intent: Intent to visualize
        
        Returns:
            Human-readable execution plan
        """
        return self.analyzer.visualize(intent)


class ResourceLimiter:
    """
    Manages resource limits for parallel execution
    
    Features:
    - CPU/memory limits
    - Operation prioritization
    - Rate limiting
    """
    
    def __init__(
        self,
        max_cpu_percent: float = 80.0,
        max_memory_mb: int = 1024,
        max_concurrent_io: int = 5
    ):
        """
        Initialize resource limiter
        
        Args:
            max_cpu_percent: Maximum CPU usage percentage
            max_memory_mb: Maximum memory usage in MB
            max_concurrent_io: Maximum concurrent I/O operations
        """
        self.max_cpu_percent = max_cpu_percent
        self.max_memory_mb = max_memory_mb
        self.max_concurrent_io = max_concurrent_io
        
        self.current_io_operations = 0
    
    def can_execute(self, step: Step) -> bool:
        """
        Check if step can be executed given current resources
        
        Args:
            step: Step to check
        
        Returns:
            True if resources available
        """
        # For now, simple implementation
        # Could be extended to check actual CPU/memory usage
        
        if self._is_io_intensive(step):
            return self.current_io_operations < self.max_concurrent_io
        
        return True
    
    def _is_io_intensive(self, step: Step) -> bool:
        """Check if step is I/O intensive"""
        io_operations = {
            "FileOps": ["read_file", "write_file", "copy_file", "move_file"],
            "NetworkOps": ["download", "upload", "curl"],
            "BrowserOps": ["screenshot", "download"]
        }
        
        if step.tool in io_operations:
            if step.action in io_operations[step.tool]:
                return True
        
        return False
    
    def acquire_io(self):
        """Acquire I/O slot"""
        self.current_io_operations += 1
    
    def release_io(self):
        """Release I/O slot"""
        self.current_io_operations = max(0, self.current_io_operations - 1)


def get_parallel_executor(
    max_workers: Optional[int] = None,
    timeout_seconds: Optional[int] = None
) -> ParallelExecutor:
    """
    Get parallel executor instance
    
    Args:
        max_workers: Maximum concurrent workers (default: 4)
        timeout_seconds: Timeout per operation (default: 300)
    
    Returns:
        ParallelExecutor instance
    """
    return ParallelExecutor(
        max_workers=max_workers or 4,
        timeout_seconds=timeout_seconds or 300
    )

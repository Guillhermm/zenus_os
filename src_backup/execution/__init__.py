"""
Execution module

Parallel and optimized execution capabilities.
"""

from execution.parallel_executor import ParallelExecutor, get_parallel_executor, ResourceLimiter

__all__ = ["ParallelExecutor", "get_parallel_executor", "ResourceLimiter"]

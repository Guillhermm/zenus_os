"""
Dependency Analyzer

Analyzes dependencies between execution steps to enable parallel execution.

Responsibilities:
- Build dependency graph
- Identify parallelizable operations
- Determine execution order
- Detect cycles and conflicts
"""

from typing import List, Set, Dict, Tuple
from brain.llm.schemas import IntentIR, Step
from dataclasses import dataclass


@dataclass
class DependencyGraph:
    """Represents step dependencies"""
    nodes: List[int]  # Step indices
    edges: Dict[int, Set[int]]  # node -> depends on
    levels: List[List[int]]  # Execution levels (can run in parallel within level)


class DependencyAnalyzer:
    """
    Analyzes dependencies between steps
    
    Determines:
    - Which steps must run sequentially
    - Which steps can run in parallel
    - Optimal execution order
    """
    
    def __init__(self):
        pass
    
    def analyze(self, intent: IntentIR) -> DependencyGraph:
        """
        Analyze dependencies in an intent
        
        Args:
            intent: Intent IR with steps
        
        Returns:
            Dependency graph with execution levels
        """
        steps = intent.steps
        n = len(steps)
        
        if n == 0:
            return DependencyGraph(nodes=[], edges={}, levels=[])
        
        if n == 1:
            return DependencyGraph(nodes=[0], edges={0: set()}, levels=[[0]])
        
        # Build dependency edges
        edges = {i: set() for i in range(n)}
        
        for i in range(n):
            for j in range(i):
                if self._depends_on(steps[i], steps[j]):
                    edges[i].add(j)
        
        # Calculate execution levels using topological sort
        levels = self._calculate_levels(n, edges)
        
        return DependencyGraph(
            nodes=list(range(n)),
            edges=edges,
            levels=levels
        )
    
    def _depends_on(self, step_a: Step, step_b: Step) -> bool:
        """
        Check if step_a depends on step_b
        
        Dependencies exist when:
        1. Both operate on the same file/resource
        2. step_a reads what step_b writes
        3. step_a writes what step_b reads/writes
        4. Order matters for safety
        """
        
        # Same tool operations usually have implicit ordering
        if step_a.tool == step_b.tool:
            # Check for resource conflicts
            if self._has_resource_conflict(step_a, step_b):
                return True
        
        # File operation dependencies
        if self._has_file_dependency(step_a, step_b):
            return True
        
        # Package operations - generally sequential
        if step_a.tool == "PackageOps" and step_b.tool == "PackageOps":
            return True  # Package manager operations should be sequential
        
        # Git operations - generally sequential
        if step_a.tool == "GitOps" and step_b.tool == "GitOps":
            return True  # Git operations have implicit ordering
        
        # Service operations on same service
        if step_a.tool == "ServiceOps" and step_b.tool == "ServiceOps":
            if step_a.args.get("service") == step_b.args.get("service"):
                return True
        
        return False
    
    def _has_resource_conflict(self, step_a: Step, step_b: Step) -> bool:
        """Check if steps operate on the same resource"""
        
        # File operations
        if step_a.tool == "FileOps" and step_b.tool == "FileOps":
            path_a = step_a.args.get("path") or step_a.args.get("source") or step_a.args.get("dest")
            path_b = step_b.args.get("path") or step_b.args.get("source") or step_b.args.get("dest")
            
            if path_a and path_b:
                # Same path or overlapping directories
                if path_a == path_b:
                    return True
                # Check if one is parent of other
                if path_a.startswith(path_b) or path_b.startswith(path_a):
                    return True
        
        # Package operations on same package
        if step_a.tool == "PackageOps" and step_b.tool == "PackageOps":
            if step_a.args.get("package") == step_b.args.get("package"):
                return True
        
        # Network operations on same URL/host
        if step_a.tool == "NetworkOps" and step_b.tool == "NetworkOps":
            url_a = step_a.args.get("url")
            url_b = step_b.args.get("url")
            if url_a and url_b and url_a == url_b:
                return True
        
        return False
    
    def _has_file_dependency(self, step_a: Step, step_b: Step) -> bool:
        """Check if step_a depends on file written by step_b"""
        
        # step_b writes a file, step_a reads/uses it
        if step_b.action in ("create_file", "write_file", "copy_file", "move_file"):
            write_path = step_b.args.get("path") or step_b.args.get("dest")
            
            if write_path:
                # Check if step_a uses this file
                read_path = step_a.args.get("path") or step_a.args.get("source")
                if read_path and read_path == write_path:
                    return True
        
        return False
    
    def _calculate_levels(self, n: int, edges: Dict[int, Set[int]]) -> List[List[int]]:
        """
        Calculate execution levels using modified topological sort
        
        Returns list of levels, where each level can execute in parallel
        """
        # Calculate in-degree (number of dependencies)
        in_degree = {i: len(edges[i]) for i in range(n)}
        
        levels = []
        processed = set()
        
        while len(processed) < n:
            # Find all nodes with no remaining dependencies
            current_level = []
            for i in range(n):
                if i not in processed and in_degree[i] == 0:
                    current_level.append(i)
            
            if not current_level:
                # Cycle detected or error - fall back to sequential
                remaining = [i for i in range(n) if i not in processed]
                for i in remaining:
                    levels.append([i])
                    processed.add(i)
                break
            
            levels.append(current_level)
            processed.update(current_level)
            
            # Update in-degrees
            for node in current_level:
                for i in range(n):
                    if i not in processed and node in edges[i]:
                        in_degree[i] -= 1
        
        return levels
    
    def is_parallelizable(self, intent: IntentIR) -> bool:
        """
        Quick check if intent has parallelizable steps
        
        Returns:
            True if parallel execution would help
        """
        if len(intent.steps) < 2:
            return False
        
        graph = self.analyze(intent)
        
        # Parallelizable if we have multiple steps in any level
        return any(len(level) > 1 for level in graph.levels)
    
    def estimate_speedup(self, intent: IntentIR) -> float:
        """
        Estimate speedup from parallel execution
        
        Returns:
            Speedup factor (1.0 = no speedup, 2.0 = 2x faster)
        """
        if len(intent.steps) < 2:
            return 1.0
        
        graph = self.analyze(intent)
        
        # Sequential time = number of steps
        sequential_time = len(intent.steps)
        
        # Parallel time = number of levels (assuming infinite parallelism)
        parallel_time = len(graph.levels)
        
        if parallel_time == 0:
            return 1.0
        
        return sequential_time / parallel_time
    
    def get_execution_order(self, intent: IntentIR) -> List[List[int]]:
        """
        Get optimal execution order
        
        Returns:
            List of execution levels (indices into intent.steps)
        """
        graph = self.analyze(intent)
        return graph.levels
    
    def visualize(self, intent: IntentIR) -> str:
        """
        Generate human-readable visualization of dependencies
        
        Returns:
            String representation of execution plan
        """
        graph = self.analyze(intent)
        
        lines = ["Execution Plan:"]
        lines.append(f"  Total steps: {len(intent.steps)}")
        lines.append(f"  Execution levels: {len(graph.levels)}")
        lines.append(f"  Estimated speedup: {self.estimate_speedup(intent):.1f}x")
        lines.append("")
        
        for level_idx, level in enumerate(graph.levels, 1):
            if len(level) == 1:
                step_idx = level[0]
                step = intent.steps[step_idx]
                lines.append(f"  Level {level_idx} (sequential):")
                lines.append(f"    [{step_idx}] {step.tool}.{step.action}")
            else:
                lines.append(f"  Level {level_idx} (parallel - {len(level)} steps):")
                for step_idx in level:
                    step = intent.steps[step_idx]
                    lines.append(f"    [{step_idx}] {step.tool}.{step.action}")
        
        return "\n".join(lines)

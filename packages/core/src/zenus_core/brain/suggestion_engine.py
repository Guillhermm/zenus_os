"""
Suggestion Engine

Generates proactive suggestions for optimization and improvement.

Responsibilities:
- Analyze command patterns
- Detect inefficiencies
- Suggest better approaches
- Learn user preferences
"""

from typing import List, Dict, Optional
from zenus_core.brain.llm.schemas import IntentIR, Step
from zenus_core.memory.failure_logger import get_failure_logger
from zenus_core.memory.intent_history import IntentHistory
from dataclasses import dataclass


@dataclass
class Suggestion:
    """Represents a proactive suggestion"""
    type: str  # optimization, alternative, warning, tip
    title: str
    description: str
    reason: str
    confidence: float  # 0.0-1.0
    accept_rate: float = 0.0  # Historical acceptance rate


class SuggestionEngine:
    """
    Generates proactive suggestions
    
    Features:
    - Pattern-based suggestions
    - Optimization detection
    - Alternative tool recommendations
    - Best practice tips
    """
    
    def __init__(self):
        self.failure_logger = get_failure_logger()
        
        # Suggestion rules
        self.optimization_rules = [
            self._suggest_batch_operations,
            self._suggest_parallel_execution,
            self._suggest_caching,
            self._suggest_tool_alternatives
        ]
        
        self.warning_rules = [
            self._warn_about_failures,
            self._warn_about_destructive_ops,
            self._warn_about_performance
        ]
    
    def analyze(
        self,
        user_input: str,
        intent: IntentIR,
        context: Optional[Dict] = None
    ) -> List[Suggestion]:
        """
        Analyze and generate suggestions
        
        Args:
            user_input: Original user command
            intent: Translated intent
            context: Execution context
        
        Returns:
            List of suggestions
        """
        suggestions = []
        
        # Run optimization rules
        for rule in self.optimization_rules:
            result = rule(user_input, intent, context or {})
            if result:
                suggestions.extend(result if isinstance(result, list) else [result])
        
        # Run warning rules
        for rule in self.warning_rules:
            result = rule(user_input, intent, context or {})
            if result:
                suggestions.extend(result if isinstance(result, list) else [result])
        
        # Sort by confidence and return top suggestions
        suggestions.sort(key=lambda s: s.confidence, reverse=True)
        return suggestions[:5]  # Top 5 suggestions
    
    def _suggest_batch_operations(
        self,
        user_input: str,
        intent: IntentIR,
        context: Dict
    ) -> Optional[Suggestion]:
        """Suggest batch operations with wildcards"""
        
        # Detect multiple similar operations
        file_ops = [s for s in intent.steps if s.tool == "FileOps"]
        
        if len(file_ops) >= 3:
            # Check if operating on similar files
            operations = set(s.action for s in file_ops)
            
            if len(operations) == 1:  # Same operation
                # Suggest wildcard usage
                return Suggestion(
                    type="optimization",
                    title="Use wildcard for batch operations",
                    description=f"Instead of processing {len(file_ops)} files individually, use wildcards like *.pdf or *.txt",
                    reason=f"Wildcards can reduce execution time by ~{int((len(file_ops)-1)/len(file_ops)*100)}%",
                    confidence=0.9
                )
        
        return None
    
    def _suggest_parallel_execution(
        self,
        user_input: str,
        intent: IntentIR,
        context: Dict
    ) -> Optional[Suggestion]:
        """Suggest parallel execution for independent operations"""
        
        if len(intent.steps) < 3:
            return None
        
        # Check if steps could run in parallel
        from brain.dependency_analyzer import DependencyAnalyzer
        analyzer = DependencyAnalyzer()
        
        if analyzer.is_parallelizable(intent):
            speedup = analyzer.estimate_speedup(intent)
            
            if speedup > 1.5:
                return Suggestion(
                    type="optimization",
                    title="Enable parallel execution",
                    description=f"These operations can run concurrently, potentially {speedup:.1f}x faster",
                    reason="Independent operations detected",
                    confidence=0.8
                )
        
        return None
    
    def _suggest_caching(
        self,
        user_input: str,
        intent: IntentIR,
        context: Dict
    ) -> Optional[Suggestion]:
        """Suggest caching for repeated operations"""
        
        # Detect repeated network/download operations
        network_ops = [s for s in intent.steps if s.tool == "NetworkOps"]
        
        if len(network_ops) >= 2:
            urls = [s.args.get("url") for s in network_ops]
            if len(urls) != len(set(urls)):  # Duplicate URLs
                return Suggestion(
                    type="optimization",
                    title="Cache repeated downloads",
                    description="Downloading the same resource multiple times - consider caching",
                    reason="Duplicate network requests detected",
                    confidence=0.85
                )
        
        return None
    
    def _suggest_tool_alternatives(
        self,
        user_input: str,
        intent: IntentIR,
        context: Dict
    ) -> Optional[List[Suggestion]]:
        """Suggest alternative tools that might work better"""
        
        suggestions = []
        
        # Check failure history for this tool
        for step in intent.steps:
            stats = self.failure_logger.get_failure_stats()
            tool_failures = stats.get("by_tool", {}).get(step.tool, 0)
            
            if tool_failures > 5:
                # Tool has failed multiple times - suggest alternatives
                alternatives = self._get_tool_alternatives(step.tool)
                
                if alternatives:
                    suggestions.append(Suggestion(
                        type="alternative",
                        title=f"Consider alternative to {step.tool}",
                        description=f"{step.tool} has failed {tool_failures} times recently. Alternatives: {', '.join(alternatives)}",
                        reason="High failure rate for this tool",
                        confidence=0.7
                    ))
        
        return suggestions if suggestions else None
    
    def _warn_about_failures(
        self,
        user_input: str,
        intent: IntentIR,
        context: Dict
    ) -> Optional[Suggestion]:
        """Warn about operations that have failed before"""
        
        from brain.failure_analyzer import FailureAnalyzer
        analyzer = FailureAnalyzer()
        
        analysis = analyzer.analyze_before_execution(user_input, intent)
        
        if analysis["success_probability"] < 0.6:
            return Suggestion(
                type="warning",
                title="High failure risk detected",
                description=f"This command has a {(1-analysis['success_probability'])*100:.0f}% failure rate based on history",
                reason=f"Similar commands failed {len(analysis['similar_failures'])} time(s) recently",
                confidence=0.9
            )
        
        return None
    
    def _warn_about_destructive_ops(
        self,
        user_input: str,
        intent: IntentIR,
        context: Dict
    ) -> Optional[Suggestion]:
        """Warn about destructive operations"""
        
        high_risk_steps = [s for s in intent.steps if s.risk >= 3]
        
        if high_risk_steps:
            return Suggestion(
                type="warning",
                title="Destructive operation detected",
                description=f"{len(high_risk_steps)} operation(s) cannot be undone without backup",
                reason="High-risk operations require extra caution",
                confidence=1.0
            )
        
        return None
    
    def _warn_about_performance(
        self,
        user_input: str,
        intent: IntentIR,
        context: Dict
    ) -> Optional[Suggestion]:
        """Warn about potentially slow operations"""
        
        # Detect operations that might be slow
        slow_operations = 0
        
        for step in intent.steps:
            if step.tool == "BrowserOps":
                slow_operations += 1
            elif step.tool == "NetworkOps" and "download" in step.action:
                slow_operations += 1
        
        if slow_operations >= 3:
            return Suggestion(
                type="warning",
                title="This might take a while",
                description=f"{slow_operations} potentially slow operation(s) detected (browser automation, downloads)",
                reason="Operations requiring external resources",
                confidence=0.8
            )
        
        return None
    
    def _get_tool_alternatives(self, tool: str) -> List[str]:
        """Get alternative tools for a given tool"""
        
        alternatives = {
            "BrowserOps": ["NetworkOps (for simple downloads)", "curl/wget"],
            "NetworkOps": ["BrowserOps (for JavaScript sites)"],
            "PackageOps": ["Manual installation", "Alternative package manager"],
            "GitOps": ["Manual git commands"],
        }
        
        return alternatives.get(tool, [])
    
    def should_show(self, suggestion: Suggestion, threshold: float = 0.6) -> bool:
        """
        Determine if suggestion should be shown to user
        
        Args:
            suggestion: Suggestion to evaluate
            threshold: Minimum confidence threshold
        
        Returns:
            True if should be shown
        """
        # Don't spam with low-confidence suggestions
        if suggestion.confidence < threshold:
            return False
        
        # Show warnings regardless of threshold
        if suggestion.type == "warning":
            return True
        
        # Consider historical accept rate
        if suggestion.accept_rate > 0 and suggestion.accept_rate < 0.2:
            return False  # User doesn't find this suggestion useful
        
        return True
    
    def format_suggestion(self, suggestion: Suggestion) -> str:
        """
        Format suggestion for display
        
        Args:
            suggestion: Suggestion to format
        
        Returns:
            Formatted string
        """
        icons = {
            "optimization": "⚡",
            "alternative": "🔄",
            "warning": "⚠️",
            "tip": "💡"
        }
        
        icon = icons.get(suggestion.type, "💡")
        
        lines = [
            f"{icon} {suggestion.title}",
            f"   {suggestion.description}",
            f"   Reason: {suggestion.reason}"
        ]
        
        return "\n".join(lines)


# Global instance
_suggestion_engine = None


def get_suggestion_engine() -> SuggestionEngine:
    """Get global suggestion engine instance"""
    global _suggestion_engine
    if _suggestion_engine is None:
        _suggestion_engine = SuggestionEngine()
    return _suggestion_engine

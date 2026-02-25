"""
Task Complexity Analyzer for Model Router

Analyzes task complexity to route to appropriate LLM:
- Simple tasks → Fast/cheap models (DeepSeek)
- Complex tasks → Powerful models (Claude)
"""

from dataclasses import dataclass
from typing import List
import re


@dataclass
class ComplexityScore:
    """Task complexity assessment"""
    score: float  # 0.0 (simple) to 1.0 (complex)
    reasons: List[str]
    recommended_model: str
    confidence: float
    
    @property
    def is_simple(self) -> bool:
        """Task is simple enough for cheap model"""
        return self.score < 0.3
    
    @property
    def is_complex(self) -> bool:
        """Task requires powerful model"""
        return self.score > 0.7


class TaskComplexityAnalyzer:
    """
    Analyzes task complexity using heuristics
    
    Factors considered:
    - Command length
    - Keywords (analyze, refactor, complex operations)
    - Multi-step indicators
    - Risk level
    - Iterative flag
    """
    
    # Keywords that indicate complexity
    COMPLEX_KEYWORDS = {
        'analyze', 'refactor', 'optimize', 'design', 'architecture',
        'explain', 'debug', 'troubleshoot', 'investigate', 'research',
        'compare', 'evaluate', 'recommend', 'suggest improvements',
        'best practices', 'review', 'audit', 'assess', 'plan',
        'strategy', 'approach', 'solution', 'alternatives'
    }
    
    # Keywords that indicate simplicity
    SIMPLE_KEYWORDS = {
        'list', 'show', 'display', 'get', 'check', 'status',
        'info', 'view', 'read', 'print', 'cat', 'ls', 'pwd',
        'echo', 'which', 'whereis', 'find file', 'locate'
    }
    
    # Operations that are always simple
    SIMPLE_OPERATIONS = {
        'list files', 'show status', 'check status', 'pwd',
        'whoami', 'date', 'uptime', 'df', 'du', 'free',
        'ps', 'top', 'ls', 'cat file'
    }
    
    def __init__(self, cheap_model: str = "deepseek", powerful_model: str = "anthropic"):
        self.cheap_model = cheap_model
        self.powerful_model = powerful_model
    
    def analyze(self, user_input: str, iterative: bool = False) -> ComplexityScore:
        """
        Analyze task complexity
        
        Args:
            user_input: Natural language command
            iterative: Whether iterative mode is requested
        
        Returns:
            ComplexityScore with recommendation
        """
        reasons = []
        score = 0.0
        
        # Normalize input
        normalized = user_input.lower().strip()
        
        # Factor 1: Iterative mode (strong signal for complexity)
        if iterative:
            score += 0.4
            reasons.append("Iterative mode requested (complex task)")
        
        # Factor 2: Length (longer = more complex)
        word_count = len(normalized.split())
        if word_count > 30:
            score += 0.3
            reasons.append(f"Long command ({word_count} words)")
        elif word_count > 15:
            score += 0.15
            reasons.append(f"Medium-length command ({word_count} words)")
        
        # Factor 3: Simple operation check (quick exit)
        for simple_op in self.SIMPLE_OPERATIONS:
            if simple_op in normalized:
                score = max(0.1, score - 0.3)
                reasons.append(f"Simple operation: '{simple_op}'")
                break
        
        # Factor 4: Complex keywords
        complex_found = []
        for keyword in self.COMPLEX_KEYWORDS:
            if keyword in normalized:
                complex_found.append(keyword)
        
        if complex_found:
            complexity_boost = min(0.4, len(complex_found) * 0.15)
            score += complexity_boost
            reasons.append(f"Complex keywords: {', '.join(complex_found[:3])}")
        
        # Factor 5: Simple keywords (reduce score)
        simple_found = []
        for keyword in self.SIMPLE_KEYWORDS:
            if keyword in normalized:
                simple_found.append(keyword)
        
        if simple_found and not complex_found:
            score = max(0.0, score - 0.2)
            reasons.append(f"Simple keywords: {', '.join(simple_found[:2])}")
        
        # Factor 6: Multiple steps indicator
        multi_step_patterns = [
            r'\band\b', r'\bthen\b', r'\bafter\b', r'\bnext\b',
            r'\bfirst\b.*\bsecond\b', r'\bstep \d+', r'\d+\)'
        ]
        
        multi_step_count = sum(
            1 for pattern in multi_step_patterns 
            if re.search(pattern, normalized)
        )
        
        if multi_step_count >= 2:
            score += 0.2
            reasons.append("Multi-step task detected")
        
        # Factor 7: Code/data patterns (complex)
        if any(indicator in normalized for indicator in ['codebase', 'repository', 'project', 'database']):
            score += 0.2
            reasons.append("Operating on large scope (codebase/project)")
        
        # Factor 8: Destructive operations (simple but need confirmation)
        if any(word in normalized for word in ['delete', 'remove', 'destroy', 'wipe']):
            # Don't increase complexity, but note it
            reasons.append("Destructive operation (not necessarily complex)")
        
        # Clamp score to [0.0, 1.0]
        score = max(0.0, min(1.0, score))
        
        # Calculate confidence based on number of factors
        confidence = min(0.95, 0.5 + (len(reasons) * 0.1))
        
        # Determine recommended model
        if score < 0.3:
            recommended_model = self.cheap_model
        elif score < 0.7:
            # Medium complexity - prefer cheap but accept powerful
            recommended_model = self.cheap_model
        else:
            recommended_model = self.powerful_model
        
        return ComplexityScore(
            score=score,
            reasons=reasons,
            recommended_model=recommended_model,
            confidence=confidence
        )
    
    def should_use_powerful_model(self, user_input: str, iterative: bool = False) -> bool:
        """
        Quick check: should we use powerful model?
        
        Args:
            user_input: Natural language command
            iterative: Whether iterative mode requested
        
        Returns:
            True if powerful model recommended
        """
        complexity = self.analyze(user_input, iterative)
        return complexity.recommended_model == self.powerful_model

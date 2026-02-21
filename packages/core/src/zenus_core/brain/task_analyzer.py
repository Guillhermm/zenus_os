"""
Task Analyzer

Determines if a task requires iterative execution or can be solved one-shot.
Uses heuristics and LLM analysis to classify task complexity.
"""

from typing import List
import re


class TaskComplexity:
    """Classification of task complexity"""
    
    def __init__(
        self,
        needs_iteration: bool,
        confidence: float,
        reasoning: str,
        estimated_steps: int = 1
    ):
        self.needs_iteration = needs_iteration
        self.confidence = confidence
        self.reasoning = reasoning
        self.estimated_steps = estimated_steps
    
    def __repr__(self):
        mode = "ITERATIVE" if self.needs_iteration else "ONE-SHOT"
        return f"TaskComplexity({mode}, confidence={self.confidence:.2f}, steps~{self.estimated_steps})"


class TaskAnalyzer:
    """
    Analyzes tasks to determine if they need iterative execution
    
    Uses both heuristics and LLM judgment to classify:
    - Simple one-shot tasks: "list files", "create folder"
    - Complex iterative tasks: "read project and improve", "organize by type and date"
    """
    
    # Keywords indicating need for iteration
    ITERATIVE_KEYWORDS = [
        # Analysis keywords
        'analyze', 'understand', 'examine', 'study', 'investigate',
        'explore', 'review', 'assess', 'evaluate', 'inspect',
        
        # Multi-step keywords
        'then', 'after', 'next', 'followed by', 'and then',
        'subsequently', 'afterwards',
        
        # Improvement/modification keywords
        'improve', 'enhance', 'optimize', 'refactor', 'fix',
        'update', 'modify', 'change', 'adjust', 'revise',
        
        # Context-dependent keywords
        'based on', 'depending on', 'according to', 'if',
        'when', 'where', 'which', 'that match',
        
        # Learning/discovery keywords
        'find out', 'discover', 'determine', 'figure out',
        'identify', 'detect', 'locate',
        
        # Complex organization
        'organize by', 'sort by', 'group by', 'categorize',
        'classify', 'arrange by'
    ]
    
    # Keywords indicating simple one-shot tasks
    ONESHOT_KEYWORDS = [
        # Simple listing
        'list', 'show', 'display', 'print',
        
        # Simple creation
        'create empty', 'make folder', 'touch',
        
        # Simple info queries
        'what is', 'how much', 'status of',
        'info about', 'details of'
    ]
    
    def __init__(self, llm=None):
        """
        Initialize TaskAnalyzer
        
        Args:
            llm: Optional LLM for advanced analysis (uses heuristics if None)
        """
        self.llm = llm
    
    def analyze(self, user_input: str) -> TaskComplexity:
        """
        Analyze if task needs iterative execution
        
        Args:
            user_input: User's natural language command
        
        Returns:
            TaskComplexity with recommendation
        """
        
        user_lower = user_input.lower()
        
        # Heuristic analysis
        heuristic_result = self._heuristic_analysis(user_lower)
        
        # If LLM available and heuristic is uncertain, ask LLM
        if self.llm and heuristic_result.confidence < 0.8:
            return self._llm_analysis(user_input)
        
        return heuristic_result
    
    def _heuristic_analysis(self, user_input: str) -> TaskComplexity:
        """Use heuristics to classify task complexity"""
        
        # Check for iterative keywords
        iterative_score = sum(
            1 for keyword in self.ITERATIVE_KEYWORDS
            if keyword in user_input
        )
        
        # Check for one-shot keywords
        oneshot_score = sum(
            1 for keyword in self.ONESHOT_KEYWORDS
            if keyword in user_input
        )
        
        # Check for multiple sentences/clauses
        sentence_count = len([s for s in re.split(r'[.!?;]', user_input) if s.strip()])
        clause_count = user_input.count(',') + user_input.count(' and ')
        
        # Check for file operations with conditions
        has_conditions = any(word in user_input for word in ['if', 'where', 'that', 'which'])
        has_file_ops = any(word in user_input for word in ['file', 'folder', 'directory'])
        
        # Scoring
        complexity_score = 0
        
        # Iterative keywords add to complexity
        complexity_score += iterative_score * 3  # Increased weight
        
        # One-shot keywords reduce complexity
        complexity_score -= oneshot_score * 3
        
        # Multiple steps increase complexity
        if sentence_count > 1:
            complexity_score += sentence_count
        
        if clause_count > 2:
            complexity_score += 2
        
        # Conditional file operations are complex
        if has_conditions and has_file_ops:
            complexity_score += 3
        
        # Word count heuristic (very long commands are often complex)
        word_count = len(user_input.split())
        if word_count > 15:
            complexity_score += 2
        elif word_count > 10:
            complexity_score += 1
        
        # Determine if needs iteration (lowered threshold)
        needs_iteration = complexity_score >= 2  # Was 3, now 2 for better sensitivity
        
        # Estimate confidence
        if complexity_score >= 5:
            confidence = 0.9  # Very complex
        elif complexity_score >= 2:
            confidence = 0.75  # Moderately complex
        elif complexity_score <= -2:
            confidence = 0.85  # Very confident it's simple
        else:
            confidence = 0.6  # Slightly uncertain
        
        # Estimate steps
        estimated_steps = max(1, min(10, complexity_score + 1))
        
        # Reasoning
        if needs_iteration:
            reasoning = f"Complex task detected: {iterative_score} iterative keywords, {sentence_count} sentences"
        else:
            reasoning = f"Simple task: {oneshot_score} simple keywords, low complexity score"
        
        return TaskComplexity(
            needs_iteration=needs_iteration,
            confidence=confidence,
            reasoning=reasoning,
            estimated_steps=estimated_steps
        )
    
    def _llm_analysis(self, user_input: str) -> TaskComplexity:
        """Use LLM to analyze task complexity (fallback for uncertain cases)"""
        
        prompt = f"""Analyze this user command for task complexity:

Command: "{user_input}"

Determine:
1. Does this need ITERATIVE execution (multiple plan-execute-observe cycles)?
2. Or can it be solved in ONE-SHOT (single plan and execution)?

ITERATIVE tasks:
- Require exploration or discovery (e.g., "read project and understand")
- Depend on intermediate results (e.g., "analyze code, then refactor")
- Need context building (e.g., "organize files by type and date")
- Have conditional logic (e.g., "find duplicates and move them")

ONE-SHOT tasks:
- Simple, well-defined actions (e.g., "list files in ~/Documents")
- No dependencies on observations (e.g., "create folder ~/test")
- Single-step operations (e.g., "show disk usage")

Respond with:
NEEDS_ITERATION: [Yes/No]
CONFIDENCE: [0.0-1.0]
ESTIMATED_STEPS: [1-10]
REASONING: [Brief explanation]
"""
        
        try:
            # This would call LLM's reflect_on_goal or similar
            # For now, fall back to heuristic
            return self._heuristic_analysis(user_input.lower())
        except:
            # If LLM fails, use heuristic
            return self._heuristic_analysis(user_input.lower())

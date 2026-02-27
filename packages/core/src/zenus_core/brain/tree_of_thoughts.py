"""
Tree of Thoughts - Generate and evaluate multiple solution paths

Instead of committing to one approach, explore multiple paths in parallel,
compare them, and select the best one. Revolutionary!

Key innovations:
- Parallel path generation (3-5 alternatives)
- Path evaluation with pros/cons
- Confidence scoring per path
- Automatic best-path selection
- Learning from explored alternatives
"""

import json
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from zenus_core.brain.llm.schemas import IntentIR
from zenus_core.audit.logger import AuditLogger


class PathQuality(Enum):
    """Quality rating for solution paths"""
    EXCELLENT = "excellent"  # >90% confidence
    GOOD = "good"            # 70-90%
    ACCEPTABLE = "acceptable"  # 50-70%
    RISKY = "risky"          # <50%


@dataclass
class SolutionPath:
    """A potential solution approach"""
    path_id: int
    description: str
    intent: IntentIR
    confidence: float  # 0.0 to 1.0
    pros: List[str]
    cons: List[str]
    estimated_steps: int
    estimated_time: str  # "fast", "medium", "slow"
    risk_level: str  # "low", "medium", "high"
    quality: PathQuality
    reasoning: str  # Why this approach?
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result['quality'] = self.quality.value
        result['intent'] = self.intent.to_dict()
        return result


@dataclass
class ThoughtTree:
    """Collection of explored solution paths"""
    user_input: str
    paths: List[SolutionPath]
    selected_path: Optional[SolutionPath]
    selection_reasoning: str
    exploration_time: float
    
    def get_best_path(self) -> SolutionPath:
        """Get the selected path (or best if not selected)"""
        if self.selected_path:
            return self.selected_path
        # Fallback: highest confidence
        return max(self.paths, key=lambda p: p.confidence)


class TreeOfThoughts:
    """
    Generate multiple solution paths and select the best one
    
    This is what makes Zenus revolutionary - it doesn't just give you
    one answer, it explores alternatives like a human would!
    """
    
    def __init__(self, llm, logger: AuditLogger):
        self.llm = llm
        self.logger = logger
        self.num_paths = 3  # Default: generate 3 alternatives
        self.enable_learning = True
    
    def explore(
        self, 
        user_input: str,
        context: str = "",
        num_paths: Optional[int] = None
    ) -> ThoughtTree:
        """
        Generate multiple solution paths and select the best
        
        Args:
            user_input: User's natural language command
            context: Additional context from memory
            num_paths: Number of alternatives to generate (default: 3)
        
        Returns:
            ThoughtTree with all explored paths and selection
        """
        import time
        start_time = time.time()
        
        paths_to_generate = num_paths or self.num_paths
        
        # Step 1: Generate multiple solution paths
        paths = self._generate_paths(user_input, context, paths_to_generate)
        
        # Step 2: Evaluate and select best path
        selected_path, reasoning = self._select_best_path(paths, user_input)
        
        exploration_time = time.time() - start_time
        
        # Step 3: Create thought tree
        tree = ThoughtTree(
            user_input=user_input,
            paths=paths,
            selected_path=selected_path,
            selection_reasoning=reasoning,
            exploration_time=exploration_time
        )
        
        # Step 4: Log for learning
        if self.enable_learning:
            self._log_exploration(tree)
        
        return tree
    
    def _generate_paths(
        self, 
        user_input: str, 
        context: str, 
        num_paths: int
    ) -> List[SolutionPath]:
        """Generate multiple alternative solution paths"""
        
        prompt = self._build_generation_prompt(user_input, context, num_paths)
        
        try:
            # Use streaming for better performance
            response = self.llm.generate(prompt, stream=True)
            
            # Parse JSON response
            paths_data = json.loads(response)
            
            # Convert to SolutionPath objects
            paths = []
            for i, path_dict in enumerate(paths_data.get("paths", [])):
                # Parse intent IR from path
                intent = self._parse_intent_from_path(path_dict)
                
                path = SolutionPath(
                    path_id=i + 1,
                    description=path_dict.get("description", ""),
                    intent=intent,
                    confidence=path_dict.get("confidence", 0.5),
                    pros=path_dict.get("pros", []),
                    cons=path_dict.get("cons", []),
                    estimated_steps=path_dict.get("estimated_steps", 1),
                    estimated_time=path_dict.get("estimated_time", "medium"),
                    risk_level=path_dict.get("risk_level", "medium"),
                    quality=self._determine_quality(path_dict.get("confidence", 0.5)),
                    reasoning=path_dict.get("reasoning", "")
                )
                paths.append(path)
            
            return paths
            
        except Exception as e:
            # Fallback: generate single path using standard method
            self.logger.log_error(f"Tree of Thoughts generation failed: {e}")
            
            # Create a single fallback path
            intent = self.llm.translate_intent(
                f"{user_input}\n{context}" if context else user_input,
                stream=True
            )
            
            return [SolutionPath(
                path_id=1,
                description="Standard approach (fallback)",
                intent=intent,
                confidence=0.7,
                pros=["Reliable", "Well-tested"],
                cons=["May not be optimal"],
                estimated_steps=len(intent.steps) if intent.steps else 1,
                estimated_time="medium",
                risk_level="low",
                quality=PathQuality.GOOD,
                reasoning="Fallback to standard execution"
            )]
    
    def _build_generation_prompt(
        self, 
        user_input: str, 
        context: str, 
        num_paths: int
    ) -> str:
        """Build prompt for generating multiple solution paths"""
        
        return f"""You are an expert system architect exploring multiple solution approaches.

User Request: {user_input}

{f"Context: {context}" if context else ""}

Generate {num_paths} DIFFERENT approaches to accomplish this task. For each approach:
1. Describe the approach clearly
2. Break it into executable steps (IntentIR format)
3. List pros and cons
4. Estimate complexity and risk
5. Assign confidence score (0.0 to 1.0)

Think like an engineer evaluating trade-offs. Consider:
- Performance (fast vs thorough)
- Safety (risky vs cautious)
- Complexity (simple vs feature-rich)
- Dependencies (minimal vs comprehensive)

Return JSON in this format:
{{
  "paths": [
    {{
      "description": "Quick approach using built-in tools",
      "steps": [
        {{"action": "file.read", "args": {{"path": "/etc/config"}}, "goal": "Read config"}}
      ],
      "confidence": 0.85,
      "pros": ["Fast", "Reliable", "No dependencies"],
      "cons": ["Less flexible", "Limited options"],
      "estimated_steps": 3,
      "estimated_time": "fast",
      "risk_level": "low",
      "reasoning": "Uses proven approach with minimal complexity"
    }},
    ...
  ]
}}

Generate {num_paths} truly DIFFERENT approaches. Make them distinct in philosophy!
"""
    
    def _parse_intent_from_path(self, path_dict: Dict) -> IntentIR:
        """Convert path steps to IntentIR"""
        from zenus_core.brain.llm.schemas import Step, Tool
        
        steps_data = path_dict.get("steps", [])
        steps = []
        
        for step_dict in steps_data:
            step = Step(
                action=step_dict.get("action", "unknown"),
                args=step_dict.get("args", {}),
                goal=step_dict.get("goal", "Execute step"),
                expected_output=step_dict.get("expected_output")
            )
            steps.append(step)
        
        # Create intent IR
        return IntentIR(
            goal=path_dict.get("description", "Execute task"),
            steps=steps,
            explanation=path_dict.get("reasoning", ""),
            expected_result=f"Complete task using: {path_dict.get('description', 'this approach')}"
        )
    
    def _select_best_path(
        self, 
        paths: List[SolutionPath],
        user_input: str
    ) -> Tuple[SolutionPath, str]:
        """
        Intelligently select the best path from alternatives
        
        Scoring factors:
        - Confidence (40%)
        - Risk level (30%)
        - Estimated time (20%)
        - Number of pros vs cons (10%)
        """
        
        if len(paths) == 1:
            return paths[0], "Only one path available"
        
        # Score each path
        scored_paths = []
        for path in paths:
            score = self._calculate_path_score(path)
            scored_paths.append((path, score))
        
        # Sort by score (descending)
        scored_paths.sort(key=lambda x: x[1], reverse=True)
        
        best_path, best_score = scored_paths[0]
        second_best_score = scored_paths[1][1] if len(scored_paths) > 1 else 0
        
        # Generate selection reasoning
        reasoning = self._generate_selection_reasoning(
            best_path, 
            best_score,
            second_best_score,
            len(paths)
        )
        
        return best_path, reasoning
    
    def _calculate_path_score(self, path: SolutionPath) -> float:
        """Calculate composite score for path selection"""
        
        # Confidence (40%)
        confidence_score = path.confidence * 0.4
        
        # Risk level (30%) - inverted (lower risk = higher score)
        risk_scores = {"low": 1.0, "medium": 0.6, "high": 0.2}
        risk_score = risk_scores.get(path.risk_level, 0.5) * 0.3
        
        # Estimated time (20%) - faster is better
        time_scores = {"fast": 1.0, "medium": 0.7, "slow": 0.4}
        time_score = time_scores.get(path.estimated_time, 0.7) * 0.2
        
        # Pros vs Cons (10%)
        pros_cons_ratio = len(path.pros) / (len(path.cons) + 1)
        pros_cons_score = min(pros_cons_ratio / 3, 1.0) * 0.1
        
        total_score = confidence_score + risk_score + time_score + pros_cons_score
        
        return total_score
    
    def _generate_selection_reasoning(
        self,
        best_path: SolutionPath,
        best_score: float,
        second_best_score: float,
        total_paths: int
    ) -> str:
        """Generate human-readable explanation for path selection"""
        
        margin = best_score - second_best_score
        
        if margin > 0.2:
            confidence_level = "clearly"
        elif margin > 0.1:
            confidence_level = "moderately"
        else:
            confidence_level = "slightly"
        
        reasoning = f"Selected path {best_path.path_id} ({best_path.description}) as {confidence_level} "
        reasoning += f"the best among {total_paths} alternatives. "
        
        # Add key differentiators
        reasons = []
        if best_path.confidence > 0.8:
            reasons.append(f"high confidence ({best_path.confidence:.0%})")
        if best_path.risk_level == "low":
            reasons.append("low risk")
        if best_path.estimated_time == "fast":
            reasons.append("fast execution")
        if len(best_path.pros) >= 3:
            reasons.append(f"{len(best_path.pros)} advantages")
        
        if reasons:
            reasoning += "Key factors: " + ", ".join(reasons) + "."
        
        return reasoning
    
    def _determine_quality(self, confidence: float) -> PathQuality:
        """Determine quality rating from confidence score"""
        if confidence >= 0.9:
            return PathQuality.EXCELLENT
        elif confidence >= 0.7:
            return PathQuality.GOOD
        elif confidence >= 0.5:
            return PathQuality.ACCEPTABLE
        else:
            return PathQuality.RISKY
    
    def _log_exploration(self, tree: ThoughtTree):
        """Log thought tree for learning and debugging"""
        self.logger.log_info(
            "tree_of_thoughts_exploration",
            {
                "user_input": tree.user_input,
                "num_paths": len(tree.paths),
                "selected_path_id": tree.selected_path.path_id if tree.selected_path else None,
                "exploration_time": tree.exploration_time,
                "paths": [p.to_dict() for p in tree.paths]
            }
        )


# Singleton instance
_tot_instance = None


def get_tree_of_thoughts(llm, logger: AuditLogger) -> TreeOfThoughts:
    """Get or create Tree of Thoughts instance"""
    global _tot_instance
    if _tot_instance is None:
        _tot_instance = TreeOfThoughts(llm, logger)
    return _tot_instance

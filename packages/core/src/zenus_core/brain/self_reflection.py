"""
Self-Reflection System

Makes Zenus critique its own plans before execution.
Catches mistakes, validates assumptions, and knows when to ask for help.

Key features:
- Pre-execution plan critique
- Confidence estimation per step
- Assumption validation
- Smart help requests
- Risk assessment
"""

import json
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from zenus_core.brain.llm.schemas import IntentIR, Step


class ConfidenceLevel(Enum):
    """Confidence in execution success"""
    VERY_HIGH = "very_high"  # >90%
    HIGH = "high"            # 70-90%
    MEDIUM = "medium"        # 50-70%
    LOW = "low"              # 30-50%
    VERY_LOW = "very_low"    # <30%


class ReflectionIssue(Enum):
    """Types of issues found during reflection"""
    AMBIGUITY = "ambiguity"              # Unclear intent
    MISSING_INFO = "missing_info"         # Need more information
    RISKY_OPERATION = "risky_operation"   # High-risk action
    INVALID_ASSUMPTION = "invalid_assumption"  # Bad assumption
    BETTER_APPROACH = "better_approach"   # Suboptimal method
    PREREQUISITE = "prerequisite"         # Missing requirement


@dataclass
class StepReflection:
    """Reflection on a single step"""
    step_index: int
    step_description: str
    confidence: ConfidenceLevel
    confidence_score: float  # 0.0-1.0
    issues: List[str]
    assumptions: List[str]
    risks: List[str]
    alternatives: List[str]
    prerequisites: List[str]
    reasoning: str


@dataclass
class PlanReflection:
    """Complete reflection on execution plan"""
    overall_confidence: ConfidenceLevel
    overall_confidence_score: float
    step_reflections: List[StepReflection]
    critical_issues: List[Dict]
    should_ask_user: bool
    questions_for_user: List[str]
    suggested_improvements: List[str]
    risk_assessment: str
    estimated_success_probability: float
    reasoning: str


class SelfReflection:
    """
    Self-reflection system that critiques plans before execution
    
    Makes Zenus smarter by:
    - Identifying potential problems before execution
    - Validating assumptions
    - Estimating confidence per step
    - Knowing when to ask for help
    """
    
    def __init__(self, llm, logger):
        self.llm = llm
        self.logger = logger
        
        # Thresholds
        self.low_confidence_threshold = 0.5
        self.ask_user_threshold = 0.4
    
    def reflect_on_plan(
        self, 
        user_input: str, 
        intent: IntentIR,
        context: Optional[Dict] = None
    ) -> PlanReflection:
        """
        Reflect on execution plan before running it
        
        Args:
            user_input: Original user command
            intent: Planned execution intent
            context: Additional context
        
        Returns:
            PlanReflection with analysis and recommendations
        """
        try:
            # Build reflection prompt
            prompt = self._build_reflection_prompt(user_input, intent, context)
            
            # Get reflection from LLM
            response = self.llm.generate(prompt, stream=False)
            reflection_data = json.loads(response)
            
            # Parse into PlanReflection
            reflection = self._parse_reflection(reflection_data, intent)
            
            # Log reflection
            self.logger.log_info("self_reflection", {
                "user_input": user_input,
                "overall_confidence": reflection.overall_confidence.value,
                "should_ask_user": reflection.should_ask_user,
                "critical_issues": len(reflection.critical_issues)
            })
            
            return reflection
            
        except Exception as e:
            self.logger.log_error(f"Self-reflection failed: {e}")
            
            # Return default reflection with low confidence
            return self._create_fallback_reflection(intent)
    
    def should_proceed(self, reflection: PlanReflection) -> Tuple[bool, str]:
        """
        Determine if execution should proceed based on reflection
        
        Returns:
            (should_proceed, reason)
        """
        # Critical issues -> don't proceed
        if reflection.critical_issues:
            critical_count = len(reflection.critical_issues)
            return False, f"Found {critical_count} critical issue(s) that must be resolved first"
        
        # Very low confidence -> ask user
        if reflection.overall_confidence in [ConfidenceLevel.VERY_LOW, ConfidenceLevel.LOW]:
            return False, f"Low confidence ({reflection.overall_confidence_score:.0%}) - need user confirmation"
        
        # Should ask user -> don't proceed automatically
        if reflection.should_ask_user:
            return False, "Need user input on clarifying questions"
        
        # All good!
        return True, "Reflection looks good, safe to proceed"
    
    def _build_reflection_prompt(
        self, 
        user_input: str, 
        intent: IntentIR,
        context: Optional[Dict]
    ) -> str:
        """Build prompt for self-reflection"""
        
        # Format steps
        steps_text = ""
        for i, step in enumerate(intent.steps, 1):
            steps_text += f"{i}. {step.action}({step.args})\n"
            steps_text += f"   Goal: {step.goal}\n"
            if step.risk:
                steps_text += f"   Risk: {step.risk}\n"
        
        context_text = ""
        if context:
            context_text = f"\nAdditional Context:\n{json.dumps(context, indent=2)}"
        
        return f"""You are a critical thinking assistant. Review this execution plan and identify potential issues BEFORE execution.

User Request: {user_input}

Planned Execution:
Goal: {intent.goal}

Steps:
{steps_text}
{context_text}

Critically analyze this plan:
1. What could go wrong?
2. What assumptions are being made?
3. What information is missing?
4. Are there better approaches?
5. What are the risks?
6. What prerequisites are needed?

For EACH step, estimate:
- Confidence level (0.0-1.0)
- Potential issues
- Assumptions being made
- Risks
- Alternative approaches

Then assess:
- Overall plan confidence
- Should we ask the user for clarification?
- What questions should we ask?
- Suggested improvements

Be CRITICAL but CONSTRUCTIVE. It's better to catch problems now than fail during execution.

Return JSON:
{{
  "overall_confidence": 0.85,
  "step_reflections": [
    {{
      "step_index": 0,
      "confidence": 0.9,
      "issues": ["Might fail if file doesn't exist"],
      "assumptions": ["File path is valid", "Have read permissions"],
      "risks": ["File might be very large"],
      "alternatives": ["Could check file exists first"],
      "prerequisites": ["Read permissions on file"],
      "reasoning": "Step is straightforward but needs validation"
    }},
    ...
  ],
  "critical_issues": [
    {{"type": "risky_operation", "description": "Deletes files without backup", "severity": "high"}}
  ],
  "should_ask_user": false,
  "questions_for_user": [],
  "suggested_improvements": ["Add file existence check", "Validate permissions first"],
  "risk_assessment": "Medium risk - destructive operation without safeguards",
  "reasoning": "Plan is mostly sound but needs safety checks"
}}

Be thorough - this is the last chance to catch problems!
"""
    
    def _parse_reflection(self, data: Dict, intent: IntentIR) -> PlanReflection:
        """Parse reflection data into PlanReflection object"""
        
        # Parse step reflections
        step_reflections = []
        for step_data in data.get("step_reflections", []):
            confidence_score = step_data.get("confidence", 0.5)
            
            step_ref = StepReflection(
                step_index=step_data.get("step_index", 0),
                step_description=intent.steps[step_data.get("step_index", 0)].action if step_data.get("step_index", 0) < len(intent.steps) else "unknown",
                confidence=self._score_to_level(confidence_score),
                confidence_score=confidence_score,
                issues=step_data.get("issues", []),
                assumptions=step_data.get("assumptions", []),
                risks=step_data.get("risks", []),
                alternatives=step_data.get("alternatives", []),
                prerequisites=step_data.get("prerequisites", []),
                reasoning=step_data.get("reasoning", "")
            )
            step_reflections.append(step_ref)
        
        # Overall confidence
        overall_score = data.get("overall_confidence", 0.5)
        
        # Determine if should ask user
        should_ask = data.get("should_ask_user", False)
        
        # If confidence is very low, always ask
        if overall_score < self.ask_user_threshold:
            should_ask = True
        
        reflection = PlanReflection(
            overall_confidence=self._score_to_level(overall_score),
            overall_confidence_score=overall_score,
            step_reflections=step_reflections,
            critical_issues=data.get("critical_issues", []),
            should_ask_user=should_ask,
            questions_for_user=data.get("questions_for_user", []),
            suggested_improvements=data.get("suggested_improvements", []),
            risk_assessment=data.get("risk_assessment", "Unknown risk"),
            estimated_success_probability=overall_score,
            reasoning=data.get("reasoning", "")
        )
        
        return reflection
    
    def _score_to_level(self, score: float) -> ConfidenceLevel:
        """Convert confidence score to level"""
        if score >= 0.9:
            return ConfidenceLevel.VERY_HIGH
        elif score >= 0.7:
            return ConfidenceLevel.HIGH
        elif score >= 0.5:
            return ConfidenceLevel.MEDIUM
        elif score >= 0.3:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW
    
    def _create_fallback_reflection(self, intent: IntentIR) -> PlanReflection:
        """Create fallback reflection if LLM fails"""
        
        step_reflections = []
        for i, step in enumerate(intent.steps):
            step_ref = StepReflection(
                step_index=i,
                step_description=step.action,
                confidence=ConfidenceLevel.MEDIUM,
                confidence_score=0.5,
                issues=["Reflection unavailable - proceed with caution"],
                assumptions=[],
                risks=[],
                alternatives=[],
                prerequisites=[],
                reasoning="Fallback reflection - LLM unavailable"
            )
            step_reflections.append(step_ref)
        
        return PlanReflection(
            overall_confidence=ConfidenceLevel.MEDIUM,
            overall_confidence_score=0.5,
            step_reflections=step_reflections,
            critical_issues=[],
            should_ask_user=False,
            questions_for_user=[],
            suggested_improvements=[],
            risk_assessment="Unable to assess - reflection system unavailable",
            estimated_success_probability=0.5,
            reasoning="Fallback reflection due to system error"
        )
    
    def format_reflection_for_user(self, reflection: PlanReflection) -> str:
        """Format reflection for display to user"""
        from rich.console import Console
        from io import StringIO
        
        buffer = StringIO()
        console = Console(file=buffer, force_terminal=True)
        
        # Overall assessment
        confidence_color = {
            ConfidenceLevel.VERY_HIGH: "green",
            ConfidenceLevel.HIGH: "green",
            ConfidenceLevel.MEDIUM: "yellow",
            ConfidenceLevel.LOW: "red",
            ConfidenceLevel.VERY_LOW: "red"
        }.get(reflection.overall_confidence, "white")
        
        console.print(f"\n[bold]🤔 Self-Reflection:[/bold]")
        console.print(f"Overall Confidence: [{confidence_color}]{reflection.overall_confidence_score:.0%}[/{confidence_color}]")
        console.print(f"Risk: {reflection.risk_assessment}")
        
        # Critical issues
        if reflection.critical_issues:
            console.print(f"\n[red bold]⚠️  Critical Issues ({len(reflection.critical_issues)}):[/red bold]")
            for issue in reflection.critical_issues:
                console.print(f"  • {issue.get('description', 'Unknown issue')}")
        
        # Questions for user
        if reflection.questions_for_user:
            console.print(f"\n[cyan bold]❓ Questions:[/cyan bold]")
            for q in reflection.questions_for_user:
                console.print(f"  • {q}")
        
        # Suggested improvements
        if reflection.suggested_improvements:
            console.print(f"\n[cyan]💡 Suggestions:[/cyan]")
            for suggestion in reflection.suggested_improvements[:3]:  # Top 3
                console.print(f"  • {suggestion}")
        
        # Step-by-step confidence
        low_confidence_steps = [s for s in reflection.step_reflections if s.confidence_score < 0.7]
        if low_confidence_steps:
            console.print(f"\n[yellow]⚠️  Low Confidence Steps:[/yellow]")
            for step in low_confidence_steps:
                console.print(f"  Step {step.step_index + 1}: {step.step_description}")
                console.print(f"    Confidence: {step.confidence_score:.0%}")
                if step.issues:
                    console.print(f"    Issues: {', '.join(step.issues[:2])}")
        
        return buffer.getvalue()


# Singleton instance
_self_reflection_instance = None


def get_self_reflection(llm, logger):
    """Get or create self-reflection instance"""
    global _self_reflection_instance
    if _self_reflection_instance is None:
        _self_reflection_instance = SelfReflection(llm, logger)
    return _self_reflection_instance

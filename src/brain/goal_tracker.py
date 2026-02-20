"""
Goal Tracker

Determines when a goal has been achieved based on observations.
Uses LLM to reflect on execution results and decide if task is complete.
"""

from typing import List, Dict, Any
from brain.llm.factory import get_llm
from brain.llm.schemas import IntentIR


class GoalStatus:
    """Status of goal achievement"""
    
    def __init__(
        self,
        achieved: bool,
        confidence: float,
        reasoning: str,
        next_steps: List[str] = None
    ):
        self.achieved = achieved
        self.confidence = confidence
        self.reasoning = reasoning
        self.next_steps = next_steps or []
    
    def __repr__(self):
        status = "ACHIEVED" if self.achieved else "IN PROGRESS"
        return f"GoalStatus({status}, confidence={self.confidence:.2f})"


class GoalTracker:
    """
    Tracks goal achievement through iterative execution
    
    Responsibilities:
    1. Check if goal is achieved after each iteration
    2. Provide reasoning for status
    3. Suggest next steps if goal not achieved
    4. Prevent infinite loops with iteration limits
    """
    
    def __init__(self, max_iterations: int = 10):
        self.llm = get_llm()
        self.max_iterations = max_iterations
        self.current_iteration = 0
        self.observation_history = []
    
    def check_goal(
        self,
        user_goal: str,
        original_intent: IntentIR,
        observations: List[str]
    ) -> GoalStatus:
        """
        Check if goal has been achieved
        
        Args:
            user_goal: Original user goal in natural language
            original_intent: The IntentIR that was executed
            observations: List of observations from execution
        
        Returns:
            GoalStatus indicating if goal is achieved
        """
        
        # Increment iteration counter
        self.current_iteration += 1
        
        # Store observations
        self.observation_history.extend(observations)
        
        # Safety: prevent infinite loops
        if self.current_iteration >= self.max_iterations:
            return GoalStatus(
                achieved=False,
                confidence=0.0,
                reasoning=f"Maximum iterations ({self.max_iterations}) reached. Task may be too complex or ill-defined.",
                next_steps=["Break down task into smaller steps", "Clarify requirements"]
            )
        
        # Build reflection prompt
        reflection_prompt = self._build_reflection_prompt(
            user_goal,
            original_intent,
            self.observation_history
        )
        
        # Ask LLM to reflect
        try:
            reflection = self.llm.reflect_on_goal(
                reflection_prompt,
                user_goal,
                observations
            )
            
            return self._parse_reflection(reflection)
            
        except Exception as e:
            # Fallback: assume not achieved and continue
            return GoalStatus(
                achieved=False,
                confidence=0.5,
                reasoning=f"Could not determine goal status: {e}",
                next_steps=["Continue with next logical step"]
            )
    
    def _build_reflection_prompt(
        self,
        user_goal: str,
        original_intent: IntentIR,
        observations: List[str]
    ) -> str:
        """Build prompt for LLM reflection"""
        
        # Format observations
        obs_text = "\n".join([f"{i+1}. {obs}" for i, obs in enumerate(observations)])
        
        # Format original plan
        plan_text = "\n".join([
            f"{i+1}. {step.tool}.{step.action}({step.args})"
            for i, step in enumerate(original_intent.steps)
        ])
        
        prompt = f"""
# Goal Achievement Reflection

**User's Goal:**
{user_goal}

**Original Plan Executed:**
{plan_text}

**Observations from Execution:**
{obs_text}

**Your Task:**
Reflect on whether the user's goal has been achieved based on the observations.

Answer these questions:
1. Has the goal been fully achieved? (Yes/No)
2. What is your confidence level? (0.0 to 1.0)
3. Why do you believe this? (reasoning)
4. If not achieved, what are the next logical steps?

Format your response as:
ACHIEVED: [Yes/No]
CONFIDENCE: [0.0-1.0]
REASONING: [Your explanation]
NEXT_STEPS: [Comma-separated list of next actions, or "None" if achieved]
"""
        
        return prompt
    
    def _parse_reflection(self, reflection: str) -> GoalStatus:
        """Parse LLM reflection into GoalStatus"""
        
        lines = reflection.strip().split("\n")
        
        achieved = False
        confidence = 0.5
        reasoning = "Unknown"
        next_steps = []
        
        for line in lines:
            line = line.strip()
            
            if line.startswith("ACHIEVED:"):
                achieved = "yes" in line.lower()
            
            elif line.startswith("CONFIDENCE:"):
                try:
                    confidence = float(line.split(":")[1].strip())
                except:
                    confidence = 0.5
            
            elif line.startswith("REASONING:"):
                reasoning = line.split(":", 1)[1].strip()
            
            elif line.startswith("NEXT_STEPS:"):
                steps_text = line.split(":", 1)[1].strip()
                if steps_text.lower() != "none":
                    next_steps = [s.strip() for s in steps_text.split(",")]
        
        return GoalStatus(
            achieved=achieved,
            confidence=confidence,
            reasoning=reasoning,
            next_steps=next_steps
        )
    
    def reset(self):
        """Reset tracker for new goal"""
        self.current_iteration = 0
        self.observation_history = []

from abc import ABC, abstractmethod
from typing import List, Optional, Iterator
from brain.llm.schemas import IntentIR


class LLM(ABC):
    @abstractmethod
    def translate_intent(self, user_input: str, stream: bool = False) -> IntentIR:
        """
        Translate user input to Intent IR
        
        Args:
            user_input: Natural language command
            stream: Enable streaming output (if supported)
        
        Returns:
            IntentIR object
        """
        pass
    
    @abstractmethod
    def reflect_on_goal(
        self,
        reflection_prompt: str,
        user_goal: str,
        observations: List[str]
    ) -> str:
        """
        Reflect on whether a goal has been achieved
        
        Args:
            reflection_prompt: Full prompt for reflection
            user_goal: Original user goal
            observations: List of observations from execution
        
        Returns:
            Structured reflection text with ACHIEVED, CONFIDENCE, REASONING, NEXT_STEPS
        """
        pass
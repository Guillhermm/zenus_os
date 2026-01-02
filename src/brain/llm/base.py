from abc import ABC, abstractmethod
from brain.llm.schemas import IntentIR


class LLM(ABC):
    @abstractmethod
    def translate_intent(self, user_input: str) -> IntentIR:
        pass
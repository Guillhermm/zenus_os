"""
Session Memory

Short-term memory for current session.
Tracks recent intents, execution results, and context.
"""

from typing import Optional, List, Dict
from datetime import datetime
from brain.llm.schemas import IntentIR


class SessionMemory:
    """
    Manages short-term memory for current session
    
    Stores:
    - Recent intents and results
    - File/directory references
    - Execution context
    """
    
    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self.intent_history: List[Dict] = []
        self.context_refs: Dict[str, str] = {}
        self.session_start = datetime.now()
    
    def add_intent(self, user_input: str, intent: IntentIR, result: str):
        """Record an intent and its result"""
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "goal": intent.goal,
            "steps_count": len(intent.steps),
            "result": result,
            "duration_seconds": 0  # Can be enhanced later
        }
        
        self.intent_history.append(entry)
        
        # Keep only recent history
        if len(self.intent_history) > self.max_history:
            self.intent_history.pop(0)
    
    def add_context_ref(self, key: str, value: str):
        """
        Store a context reference for later use
        
        Examples:
        - "last_directory" -> "/home/user/Downloads"
        - "that_file" -> "/home/user/document.pdf"
        - "those_images" -> "/home/user/Pictures/*.jpg"
        """
        self.context_refs[key] = value
    
    def get_context_ref(self, key: str) -> Optional[str]:
        """Retrieve a context reference"""
        return self.context_refs.get(key)
    
    def get_recent_intents(self, count: int = 5) -> List[Dict]:
        """Get N most recent intents"""
        return self.intent_history[-count:]
    
    def get_context_summary(self) -> str:
        """
        Get a text summary of current session context
        
        Useful for passing to LLM for context-aware intent translation
        """
        
        if not self.intent_history:
            return "No recent activity in this session."
        
        lines = ["Recent session context:"]
        
        for entry in self.intent_history[-3:]:
            lines.append(
                f"- {entry['timestamp']}: {entry['goal']} -> {entry['result']}"
            )
        
        if self.context_refs:
            lines.append("\nContext references:")
            for key, value in self.context_refs.items():
                lines.append(f"- {key}: {value}")
        
        return "\n".join(lines)
    
    def clear(self):
        """Clear session memory"""
        self.intent_history.clear()
        self.context_refs.clear()
    
    def get_session_stats(self) -> Dict:
        """Get session statistics"""
        
        duration = (datetime.now() - self.session_start).total_seconds()
        
        return {
            "session_duration_seconds": duration,
            "total_intents": len(self.intent_history),
            "context_refs": len(self.context_refs)
        }

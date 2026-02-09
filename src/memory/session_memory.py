"""
Session Memory

Short-term memory for the current session.
Tracks context that helps resolve ambiguous references like:
- "that folder" -> which folder?
- "those files" -> which files?
- "the last result" -> what was it?
"""

from typing import Dict, List, Optional, Any
from datetime import datetime


class SessionMemory:
    """
    Short-term context memory for current session
    
    Maintains:
    - Recent intents and outcomes
    - Referenced entities (files, directories, processes)
    - Conversation context
    """
    
    def __init__(self):
        self.intents = []
        self.entities = {}
        self.context = {}
        self.session_start = datetime.now()
    
    def add_intent(self, user_input: str, intent_ir: dict, result: str):
        """Record an executed intent"""
        self.intents.append({
            "timestamp": datetime.now().isoformat(),
            "input": user_input,
            "intent": intent_ir,
            "result": result
        })
        
        # Keep only last 10 intents in memory
        if len(self.intents) > 10:
            self.intents.pop(0)
    
    def remember_entity(self, entity_type: str, name: str, metadata: Dict[str, Any]):
        """
        Remember an entity (file, directory, process, etc.)
        
        Args:
            entity_type: "file", "directory", "process", etc.
            name: Entity identifier
            metadata: Additional context (path, pid, etc.)
        """
        if entity_type not in self.entities:
            self.entities[entity_type] = {}
        
        self.entities[entity_type][name] = {
            "metadata": metadata,
            "last_accessed": datetime.now().isoformat()
        }
    
    def get_entity(self, entity_type: str, name: str) -> Optional[Dict]:
        """Retrieve entity metadata"""
        if entity_type in self.entities and name in self.entities[entity_type]:
            return self.entities[entity_type][name]["metadata"]
        return None
    
    def get_recent_entities(self, entity_type: str, limit: int = 5) -> List[str]:
        """Get recently accessed entities of a type"""
        if entity_type not in self.entities:
            return []
        
        entities = list(self.entities[entity_type].items())
        entities.sort(
            key=lambda x: x[1]["last_accessed"],
            reverse=True
        )
        
        return [name for name, _ in entities[:limit]]
    
    def set_context(self, key: str, value: Any):
        """Set a context variable"""
        self.context[key] = value
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """Get a context variable"""
        return self.context.get(key, default)
    
    def get_last_intent(self) -> Optional[Dict]:
        """Get the most recent intent"""
        return self.intents[-1] if self.intents else None
    
    def get_last_result(self) -> Optional[str]:
        """Get the result of the last intent"""
        last = self.get_last_intent()
        return last["result"] if last else None
    
    def resolve_reference(self, reference: str) -> Optional[Any]:
        """
        Attempt to resolve ambiguous references
        
        Examples:
        - "that folder" -> last mentioned directory
        - "those files" -> last scanned files
        - "the result" -> last command output
        """
        reference_lower = reference.lower()
        
        # Reference to last result
        if reference_lower in ["the result", "that result", "it"]:
            return self.get_last_result()
        
        # Reference to last directory
        if reference_lower in ["that folder", "that directory", "there"]:
            recent_dirs = self.get_recent_entities("directory", limit=1)
            if recent_dirs:
                return self.get_entity("directory", recent_dirs[0])
        
        # Reference to last file
        if reference_lower in ["that file", "this file"]:
            recent_files = self.get_recent_entities("file", limit=1)
            if recent_files:
                return self.get_entity("file", recent_files[0])
        
        return None
    
    def get_session_duration(self) -> str:
        """Get human-readable session duration"""
        duration = datetime.now() - self.session_start
        minutes = int(duration.total_seconds() / 60)
        return f"{minutes} minutes"
    
    def summarize(self) -> Dict:
        """Get session summary"""
        return {
            "duration": self.get_session_duration(),
            "intents_executed": len(self.intents),
            "entities_tracked": sum(len(e) for e in self.entities.values()),
            "context_keys": len(self.context)
        }
    
    def clear(self):
        """Clear session memory"""
        self.intents.clear()
        self.entities.clear()
        self.context.clear()

"""
Pattern Suggestion Memory

Tracks which patterns have been suggested to avoid repeating suggestions.
"""

import json
import os
from pathlib import Path
from typing import Set, Optional


class PatternMemory:
    """
    Remembers which patterns have been suggested
    
    Prevents annoying repeated suggestions of the same pattern.
    """
    
    def __init__(self, memory_file: Optional[str] = None):
        if memory_file is None:
            memory_dir = Path.home() / ".zenus"
            memory_dir.mkdir(exist_ok=True)
            memory_file = str(memory_dir / "pattern_suggestions.json")
        
        self.memory_file = memory_file
        self.suggested_patterns: Set[str] = self._load()
    
    def _load(self) -> Set[str]:
        """Load suggested patterns from disk"""
        if not os.path.exists(self.memory_file):
            return set()
        
        try:
            with open(self.memory_file, 'r') as f:
                data = json.load(f)
                return set(data.get('suggested', []))
        except Exception:
            return set()
    
    def _save(self) -> None:
        """Save suggested patterns to disk"""
        try:
            with open(self.memory_file, 'w') as f:
                json.dump({
                    'suggested': list(self.suggested_patterns)
                }, f, indent=2)
        except Exception:
            pass
    
    def has_suggested(self, pattern_key: str) -> bool:
        """Check if pattern has been suggested before"""
        return pattern_key in self.suggested_patterns
    
    def mark_suggested(self, pattern_key: str) -> None:
        """Mark pattern as suggested"""
        self.suggested_patterns.add(pattern_key)
        self._save()
    
    def clear(self) -> None:
        """Clear all suggestion memory"""
        self.suggested_patterns.clear()
        self._save()


# Global instance
_pattern_memory: Optional[PatternMemory] = None


def get_pattern_memory() -> PatternMemory:
    """Get singleton pattern memory"""
    global _pattern_memory
    if _pattern_memory is None:
        _pattern_memory = PatternMemory()
    return _pattern_memory

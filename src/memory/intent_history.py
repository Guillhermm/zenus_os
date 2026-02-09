"""
Intent History

Persistent log of past intents and outcomes.
Enables learning from history and pattern recognition.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta


class IntentHistory:
    """
    Manages persistent intent history
    
    Stores all intents across sessions with:
    - User input
    - Generated plan
    - Execution outcome
    - Timestamp
    """
    
    def __init__(self, storage_dir: Optional[str] = None):
        if storage_dir is None:
            storage_dir = os.path.expanduser("~/.zenus/history")
        
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        
        # Current month file
        self.current_file = self._get_current_file()
    
    def _get_current_file(self) -> str:
        """Get path to current month's history file"""
        
        year_month = datetime.now().strftime("%Y-%m")
        return os.path.join(self.storage_dir, f"history_{year_month}.jsonl")
    
    def record(
        self, 
        user_input: str, 
        goal: str, 
        steps_count: int,
        success: bool,
        duration_seconds: float = 0
    ):
        """Record an intent execution"""
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "goal": goal,
            "steps_count": steps_count,
            "success": success,
            "duration_seconds": duration_seconds
        }
        
        with open(self.current_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')
    
    def search(
        self, 
        query: str, 
        limit: int = 10,
        days_back: int = 30
    ) -> List[Dict]:
        """
        Search intent history
        
        Args:
            query: Search term (matches user_input or goal)
            limit: Maximum results
            days_back: How many days to search back
        
        Returns:
            List of matching history entries
        """
        
        cutoff = datetime.now() - timedelta(days=days_back)
        matches = []
        
        # Search current and recent files
        for file_path in self._get_recent_files(days_back):
            if not os.path.exists(file_path):
                continue
            
            with open(file_path, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        entry_time = datetime.fromisoformat(entry["timestamp"])
                        
                        if entry_time < cutoff:
                            continue
                        
                        # Simple substring search
                        if (query.lower() in entry["user_input"].lower() or
                            query.lower() in entry["goal"].lower()):
                            matches.append(entry)
                            
                            if len(matches) >= limit:
                                return matches
                    except:
                        continue
        
        return matches
    
    def _get_recent_files(self, days_back: int) -> List[str]:
        """Get list of history files covering the time range"""
        
        files = []
        current_date = datetime.now()
        
        # Get current and previous months
        for i in range(3):  # Cover up to 3 months back
            year_month = (current_date - timedelta(days=30 * i)).strftime("%Y-%m")
            file_path = os.path.join(self.storage_dir, f"history_{year_month}.jsonl")
            files.append(file_path)
        
        return files
    
    def get_recent(self, count: int = 10) -> List[Dict]:
        """Get N most recent intents"""
        
        recent = []
        
        if not os.path.exists(self.current_file):
            return recent
        
        # Read file in reverse (simple implementation)
        with open(self.current_file, 'r') as f:
            lines = f.readlines()
        
        for line in reversed(lines[-count:]):
            try:
                recent.append(json.loads(line))
            except:
                continue
        
        return recent
    
    def get_stats(self, days: int = 7) -> Dict:
        """Get statistics for recent period"""
        
        cutoff = datetime.now() - timedelta(days=days)
        total = 0
        successful = 0
        
        for file_path in self._get_recent_files(days):
            if not os.path.exists(file_path):
                continue
            
            with open(file_path, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        entry_time = datetime.fromisoformat(entry["timestamp"])
                        
                        if entry_time < cutoff:
                            continue
                        
                        total += 1
                        if entry.get("success"):
                            successful += 1
                    except:
                        continue
        
        success_rate = (successful / total * 100) if total > 0 else 0
        
        return {
            "period_days": days,
            "total_intents": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": success_rate
        }

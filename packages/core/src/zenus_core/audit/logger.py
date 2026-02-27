"""
Audit Logger

Records all intent translation and execution flows for review and debugging.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from zenus_core.brain.llm.schemas import IntentIR


class AuditLogger:
    """Logs all operations to structured audit files"""

    def __init__(self, log_dir: Optional[str] = None):
        if log_dir is None:
            log_dir = os.path.expanduser("~/.zenus/logs")
        
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Current session log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_file = self.log_dir / f"session_{timestamp}.jsonl"

    def log_intent(self, user_input: str, intent: IntentIR, mode: str = "execution"):
        """Log intent translation"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "intent",
            "mode": mode,
            "user_input": user_input,
            "goal": intent.goal,
            "requires_confirmation": intent.requires_confirmation,
            "steps": [
                {
                    "tool": step.tool,
                    "action": step.action,
                    "args": step.args,
                    "risk": step.risk
                }
                for step in intent.steps
            ]
        }
        self._write(entry)

    def log_execution_start(self, intent: IntentIR):
        """Log execution start"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "execution_start",
            "goal": intent.goal
        }
        self._write(entry)

    def log_step_result(self, tool: str, action: str, result: str, success: bool):
        """Log individual step result"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "step_result",
            "tool": tool,
            "action": action,
            "result": result,
            "success": success
        }
        self._write(entry)

    def log_execution_end(self, success: bool, message: Optional[str] = None):
        """Log execution completion"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "execution_end",
            "success": success,
            "message": message
        }
        self._write(entry)

    def log_error(self, error: str, context: Optional[dict] = None):
        """Log error"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "error",
            "error": error,
            "context": context or {}
        }
        self._write(entry)
    
    def log_info(self, event_type: str, data: Optional[dict] = None):
        """Log informational event"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "info",
            "event": event_type,
            "data": data or {}
        }
        self._write(entry)

    def _write(self, entry: dict):
        """Write entry to log file"""
        with open(self.session_file, "a") as f:
            f.write(json.dumps(entry) + "\n")


# Global logger instance
_logger: Optional[AuditLogger] = None


def get_logger() -> AuditLogger:
    """Get or create global logger"""
    global _logger
    if _logger is None:
        _logger = AuditLogger()
    return _logger

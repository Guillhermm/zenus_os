"""
Workflow Recorder

Record command sequences as reusable workflows/macros.

Features:
- Record command sequences
- Save/load workflows
- Replay with parameters
- Share workflows
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class WorkflowStep:
    """Single step in a workflow"""
    command: str
    result: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    duration: float = 0.0


@dataclass
class Workflow:
    """Recorded workflow"""
    name: str
    description: str
    steps: List[WorkflowStep]
    created: str = field(default_factory=lambda: datetime.now().isoformat())
    last_used: Optional[str] = None
    use_count: int = 0
    parameters: List[str] = field(default_factory=list)  # Parameterizable fields
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "description": self.description,
            "steps": [asdict(step) for step in self.steps],
            "created": self.created,
            "last_used": self.last_used,
            "use_count": self.use_count,
            "parameters": self.parameters
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Workflow':
        """Create from dictionary"""
        steps = [WorkflowStep(**step) for step in data.get('steps', [])]
        return Workflow(
            name=data['name'],
            description=data.get('description', ''),
            steps=steps,
            created=data.get('created', datetime.now().isoformat()),
            last_used=data.get('last_used'),
            use_count=data.get('use_count', 0),
            parameters=data.get('parameters', [])
        )


class WorkflowRecorder:
    """
    Workflow recorder for command sequences
    
    Features:
    - Start/stop recording
    - Save workflows
    - Replay workflows
    - Parameterize workflows
    """
    
    def __init__(self, workflows_dir: Optional[str] = None):
        if workflows_dir is None:
            workflows_dir = str(Path.home() / ".zenus" / "workflows")
        
        self.workflows_dir = Path(workflows_dir)
        self.workflows_dir.mkdir(parents=True, exist_ok=True)
        
        # Recording state
        self.recording = False
        self.current_workflow: Optional[Workflow] = None
        self.current_steps: List[WorkflowStep] = []
    
    def start_recording(self, name: str, description: str = "") -> str:
        """
        Start recording a workflow
        
        Args:
            name: Workflow name
            description: Workflow description
        
        Returns:
            Status message
        """
        if self.recording:
            return "Already recording. Stop current recording first."
        
        self.recording = True
        self.current_workflow = Workflow(
            name=name,
            description=description,
            steps=[]
        )
        self.current_steps = []
        
        return f"Recording workflow: {name}\nType commands, then call stop_recording()"
    
    def record_step(self, command: str, result: str = "", duration: float = 0.0) -> None:
        """Record a single step"""
        if not self.recording:
            return
        
        step = WorkflowStep(
            command=command,
            result=result,
            duration=duration
        )
        self.current_steps.append(step)
    
    def stop_recording(self) -> str:
        """
        Stop recording and save workflow
        
        Returns:
            Status message
        """
        if not self.recording:
            return "Not currently recording"
        
        if not self.current_steps:
            self.recording = False
            return "No steps recorded. Workflow discarded."
        
        # Save workflow
        self.current_workflow.steps = self.current_steps
        self.save_workflow(self.current_workflow)
        
        workflow_name = self.current_workflow.name
        step_count = len(self.current_steps)
        
        # Reset state
        self.recording = False
        self.current_workflow = None
        self.current_steps = []
        
        return f"✓ Workflow saved: {workflow_name} ({step_count} steps)"
    
    def cancel_recording(self) -> str:
        """Cancel current recording"""
        if not self.recording:
            return "Not currently recording"
        
        self.recording = False
        self.current_workflow = None
        self.current_steps = []
        
        return "Recording cancelled"
    
    def save_workflow(self, workflow: Workflow) -> None:
        """Save workflow to disk"""
        file_path = self.workflows_dir / f"{workflow.name}.json"
        
        with open(file_path, 'w') as f:
            json.dump(workflow.to_dict(), f, indent=2)
    
    def load_workflow(self, name: str) -> Optional[Workflow]:
        """Load workflow from disk"""
        file_path = self.workflows_dir / f"{name}.json"
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                return Workflow.from_dict(data)
        except Exception:
            return None
    
    def list_workflows(self) -> List[str]:
        """List all saved workflows"""
        workflows = []
        
        for file_path in self.workflows_dir.glob("*.json"):
            workflows.append(file_path.stem)
        
        return sorted(workflows)
    
    def delete_workflow(self, name: str) -> str:
        """Delete a workflow"""
        file_path = self.workflows_dir / f"{name}.json"
        
        if not file_path.exists():
            return f"Workflow not found: {name}"
        
        file_path.unlink()
        return f"✓ Deleted workflow: {name}"
    
    def get_workflow_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get workflow information"""
        workflow = self.load_workflow(name)
        
        if not workflow:
            return None
        
        return {
            "name": workflow.name,
            "description": workflow.description,
            "steps": len(workflow.steps),
            "created": workflow.created,
            "last_used": workflow.last_used,
            "use_count": workflow.use_count,
            "parameters": workflow.parameters
        }
    
    def replay_workflow(
        self,
        name: str,
        parameters: Optional[Dict[str, str]] = None,
        dry_run: bool = False
    ) -> List[str]:
        """
        Replay a saved workflow
        
        Args:
            name: Workflow name
            parameters: Parameter substitutions (key -> value)
            dry_run: If True, show what would be executed
        
        Returns:
            List of commands to execute (or results if not dry_run)
        """
        workflow = self.load_workflow(name)
        
        if not workflow:
            return [f"Workflow not found: {name}"]
        
        # Update usage stats
        if not dry_run:
            workflow.last_used = datetime.now().isoformat()
            workflow.use_count += 1
            self.save_workflow(workflow)
        
        # Build command list with parameter substitution
        commands = []
        
        for step in workflow.steps:
            command = step.command
            
            # Substitute parameters
            if parameters:
                for param_name, param_value in parameters.items():
                    placeholder = f"{{{param_name}}}"
                    if placeholder in command:
                        command = command.replace(placeholder, param_value)
            
            commands.append(command)
        
        return commands
    
    def parameterize_workflow(self, name: str, parameters: List[str]) -> str:
        """
        Mark workflow as parameterizable
        
        Args:
            name: Workflow name
            parameters: List of parameter names (e.g., ["folder", "date"])
        
        Returns:
            Status message
        
        Example:
            # Original: "backup Documents to ~/Backups/Documents_2024-02-21"
            # Parameterized: "backup {folder} to ~/Backups/{folder}_{date}"
            parameterize_workflow("backup", ["folder", "date"])
        """
        workflow = self.load_workflow(name)
        
        if not workflow:
            return f"Workflow not found: {name}"
        
        workflow.parameters = parameters
        self.save_workflow(workflow)
        
        return f"✓ Workflow parameterized: {name}\nParameters: {', '.join(parameters)}"
    
    def export_workflow(self, name: str, export_path: str) -> str:
        """Export workflow to file for sharing"""
        workflow = self.load_workflow(name)
        
        if not workflow:
            return f"Workflow not found: {name}"
        
        try:
            with open(export_path, 'w') as f:
                json.dump(workflow.to_dict(), f, indent=2)
            
            return f"✓ Workflow exported to {export_path}"
        
        except Exception as e:
            return f"Export failed: {str(e)}"
    
    def import_workflow(self, import_path: str) -> str:
        """Import workflow from file"""
        try:
            with open(import_path, 'r') as f:
                data = json.load(f)
            
            workflow = Workflow.from_dict(data)
            self.save_workflow(workflow)
            
            return f"✓ Workflow imported: {workflow.name}"
        
        except Exception as e:
            return f"Import failed: {str(e)}"


# Global instance
_recorder: Optional[WorkflowRecorder] = None


def get_workflow_recorder() -> WorkflowRecorder:
    """Get singleton workflow recorder"""
    global _recorder
    if _recorder is None:
        _recorder = WorkflowRecorder()
    return _recorder

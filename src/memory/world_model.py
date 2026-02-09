"""
World Model

Long-term knowledge about the user's system and preferences.
Helps Zenus understand context without repeated queries.
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional, Any, List
from datetime import datetime


class WorldModel:
    """
    Persistent world model
    
    Stores:
    - User preferences
    - Frequently used paths
    - Known applications and their locations
    - System configuration
    - Project locations
    """
    
    def __init__(self, model_path: Optional[str] = None):
        if model_path is None:
            model_path = os.path.expanduser("~/.zenus/world_model.json")
        
        self.model_path = Path(model_path)
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load or initialize
        if self.model_path.exists():
            with open(self.model_path, "r") as f:
                self.data = json.load(f)
        else:
            self.data = self._initialize_model()
            self._save()
    
    def _initialize_model(self) -> Dict:
        """Initialize empty world model"""
        return {
            "preferences": {},
            "frequent_paths": {},
            "applications": {},
            "projects": {},
            "system": {},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    
    def _save(self):
        """Save world model to disk"""
        self.data["updated_at"] = datetime.now().isoformat()
        with open(self.model_path, "w") as f:
            json.dump(self.data, f, indent=2)
    
    def set_preference(self, key: str, value: Any):
        """Set a user preference"""
        self.data["preferences"][key] = value
        self._save()
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference"""
        return self.data["preferences"].get(key, default)
    
    def remember_path(self, alias: str, path: str, path_type: str = "directory"):
        """
        Remember a frequently used path
        
        Args:
            alias: Human-friendly name (e.g., "downloads", "projects")
            path: Absolute path
            path_type: "directory" or "file"
        """
        self.data["frequent_paths"][alias] = {
            "path": path,
            "type": path_type,
            "last_accessed": datetime.now().isoformat()
        }
        self._save()
    
    def get_path(self, alias: str) -> Optional[str]:
        """Resolve path alias to actual path"""
        path_data = self.data["frequent_paths"].get(alias)
        return path_data["path"] if path_data else None
    
    def remember_application(
        self, 
        name: str, 
        executable: str,
        metadata: Optional[Dict] = None
    ):
        """Remember an application location"""
        self.data["applications"][name] = {
            "executable": executable,
            "metadata": metadata or {},
            "last_used": datetime.now().isoformat()
        }
        self._save()
    
    def get_application(self, name: str) -> Optional[Dict]:
        """Get application info"""
        return self.data["applications"].get(name)
    
    def remember_project(
        self,
        name: str,
        path: str,
        project_type: str,
        metadata: Optional[Dict] = None
    ):
        """
        Remember a project location and details
        
        Args:
            name: Project name
            path: Project root path
            project_type: "python", "javascript", "rust", etc.
            metadata: Additional details (venv, dependencies, etc.)
        """
        self.data["projects"][name] = {
            "path": path,
            "type": project_type,
            "metadata": metadata or {},
            "last_accessed": datetime.now().isoformat()
        }
        self._save()
    
    def get_project(self, name: str) -> Optional[Dict]:
        """Get project details"""
        return self.data["projects"].get(name)
    
    def get_all_projects(self, project_type: Optional[str] = None) -> List[Dict]:
        """Get all known projects, optionally filtered by type"""
        projects = []
        for name, data in self.data["projects"].items():
            if project_type is None or data["type"] == project_type:
                projects.append({"name": name, **data})
        return projects
    
    def set_system_info(self, key: str, value: Any):
        """Store system configuration info"""
        self.data["system"][key] = value
        self._save()
    
    def get_system_info(self, key: str, default: Any = None) -> Any:
        """Retrieve system configuration info"""
        return self.data["system"].get(key, default)
    
    def infer_user_intent(self, context: Dict) -> Dict[str, Any]:
        """
        Use world model to infer likely user intent
        
        Example: If user says "organize my downloads",
        check if we know their Downloads path preference
        """
        inferences = {}
        
        # Common path inferences
        if "downloads" in self.data["frequent_paths"]:
            inferences["downloads_path"] = self.get_path("downloads")
        
        if "documents" in self.data["frequent_paths"]:
            inferences["documents_path"] = self.get_path("documents")
        
        # Project inference
        if context.get("mentions_project"):
            inferences["known_projects"] = list(self.data["projects"].keys())
        
        return inferences
    
    def suggest_completions(self, partial: str, category: str) -> List[str]:
        """
        Suggest completions based on world model
        
        Args:
            partial: Partial input
            category: "paths", "applications", "projects"
        
        Returns:
            List of matching suggestions
        """
        partial_lower = partial.lower()
        suggestions = []
        
        if category == "paths":
            for alias in self.data["frequent_paths"]:
                if partial_lower in alias.lower():
                    suggestions.append(alias)
        
        elif category == "applications":
            for app in self.data["applications"]:
                if partial_lower in app.lower():
                    suggestions.append(app)
        
        elif category == "projects":
            for project in self.data["projects"]:
                if partial_lower in project.lower():
                    suggestions.append(project)
        
        return suggestions
    
    def get_statistics(self) -> Dict:
        """Get world model statistics"""
        return {
            "preferences": len(self.data["preferences"]),
            "frequent_paths": len(self.data["frequent_paths"]),
            "applications": len(self.data["applications"]),
            "projects": len(self.data["projects"]),
            "created": self.data["created_at"],
            "updated": self.data["updated_at"]
        }

"""
Context Manager

Tracks and provides environmental context to enhance Zenus's decision-making.

Context includes:
- Current directory and git status
- Time and date awareness
- Running processes
- Recently edited files
- System state
"""

import os
import subprocess
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class ContextManager:
    """
    Central context tracking and provision
    
    Responsibilities:
    - Track current working directory
    - Detect git repository and status
    - Monitor time and user activity patterns
    - Track recently accessed files
    - Provide contextual hints for LLM
    """
    
    def __init__(self):
        self.cwd = os.getcwd()
        self.recent_files = []
        self.max_recent_files = 10
    
    def get_full_context(self) -> Dict:
        """
        Get complete context snapshot
        
        Returns:
            Dictionary with all context information
        """
        return {
            "directory": self.get_directory_context(),
            "git": self.get_git_context(),
            "time": self.get_time_context(),
            "processes": self.get_process_context(),
            "recent_files": self.get_recent_files(),
            "system": self.get_system_context()
        }
    
    def get_contextual_prompt(self) -> str:
        """
        Generate contextual prompt for LLM
        
        Returns:
            Human-readable context string
        """
        parts = []
        
        # Directory context
        dir_ctx = self.get_directory_context()
        parts.append(f"Working directory: {dir_ctx['path']}")
        if dir_ctx['project_name']:
            parts.append(f"Project: {dir_ctx['project_name']}")
        
        # Git context
        git_ctx = self.get_git_context()
        if git_ctx['is_repo']:
            parts.append(f"Git: {git_ctx['branch']} ({git_ctx['status']})")
        
        # Time context
        time_ctx = self.get_time_context()
        parts.append(f"Time: {time_ctx['time_of_day']} ({time_ctx['timestamp']})")
        
        # Recent files
        recent = self.get_recent_files()
        if recent:
            parts.append(f"Recent files: {', '.join(recent[:3])}")
        
        return "\n".join(parts)
    
    def get_directory_context(self) -> Dict:
        """Get current directory context"""
        cwd = os.getcwd()
        home = os.path.expanduser("~")
        
        # Relative path from home
        try:
            rel_path = os.path.relpath(cwd, home)
            if rel_path.startswith(".."):
                display_path = cwd
            else:
                display_path = f"~/{rel_path}"
        except ValueError:
            display_path = cwd
        
        # Project name (directory name)
        project_name = os.path.basename(cwd)
        
        # Detect project type
        project_type = self._detect_project_type(cwd)
        
        return {
            "path": display_path,
            "absolute_path": cwd,
            "project_name": project_name,
            "project_type": project_type,
            "is_home": cwd == home
        }
    
    def get_git_context(self) -> Dict:
        """Get git repository context"""
        try:
            # Check if in git repo
            subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                capture_output=True,
                check=True,
                timeout=2
            )
            
            # Get branch
            branch_result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                timeout=2
            )
            branch = branch_result.stdout.strip() or "detached HEAD"
            
            # Get status
            status_result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            status_lines = status_result.stdout.strip().split("\n")
            modified = sum(1 for line in status_lines if line.strip())
            
            if modified == 0:
                status = "clean"
            elif modified < 5:
                status = f"{modified} changes"
            else:
                status = f"{modified} changes"
            
            # Check for unpushed commits
            try:
                ahead_result = subprocess.run(
                    ["git", "rev-list", "--count", "@{u}..HEAD"],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                ahead = int(ahead_result.stdout.strip() or 0)
            except:
                ahead = 0
            
            return {
                "is_repo": True,
                "branch": branch,
                "status": status,
                "modified_files": modified,
                "ahead_commits": ahead
            }
        
        except:
            return {
                "is_repo": False,
                "branch": None,
                "status": None,
                "modified_files": 0,
                "ahead_commits": 0
            }
    
    def get_time_context(self) -> Dict:
        """Get time and date context"""
        now = datetime.now()
        hour = now.hour
        
        # Time of day
        if 5 <= hour < 12:
            time_of_day = "morning"
        elif 12 <= hour < 17:
            time_of_day = "afternoon"
        elif 17 <= hour < 21:
            time_of_day = "evening"
        else:
            time_of_day = "night"
        
        # Day of week
        day_name = now.strftime("%A")
        is_weekend = day_name in ["Saturday", "Sunday"]
        
        return {
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            "time_of_day": time_of_day,
            "hour": hour,
            "day_of_week": day_name,
            "is_weekend": is_weekend,
            "is_work_hours": 9 <= hour < 18 and not is_weekend
        }
    
    def get_process_context(self) -> Dict:
        """Get running process context"""
        try:
            # Get process count
            result = subprocess.run(
                ["ps", "aux"],
                capture_output=True,
                text=True,
                timeout=2
            )
            process_count = len(result.stdout.strip().split("\n")) - 1  # -1 for header
            
            # Check for common dev tools
            dev_tools = {
                "vscode": "code" in result.stdout,
                "pycharm": "pycharm" in result.stdout,
                "docker": "docker" in result.stdout,
                "node": "node" in result.stdout,
                "python": "python" in result.stdout
            }
            
            active_tools = [name for name, active in dev_tools.items() if active]
            
            return {
                "total": process_count,
                "dev_tools": active_tools
            }
        
        except:
            return {
                "total": 0,
                "dev_tools": []
            }
    
    def get_recent_files(self) -> List[str]:
        """Get recently accessed files in current directory"""
        try:
            cwd = os.getcwd()
            
            # Get files modified in last 24 hours
            now = time.time()
            recent = []
            
            for root, dirs, files in os.walk(cwd):
                # Skip hidden directories
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                # Only check files in current and immediate subdirectories
                depth = root[len(cwd):].count(os.sep)
                if depth > 2:
                    continue
                
                for file in files:
                    if file.startswith('.'):
                        continue
                    
                    file_path = os.path.join(root, file)
                    try:
                        mtime = os.path.getmtime(file_path)
                        if now - mtime < 86400:  # 24 hours
                            rel_path = os.path.relpath(file_path, cwd)
                            recent.append((rel_path, mtime))
                    except:
                        continue
            
            # Sort by modification time (newest first)
            recent.sort(key=lambda x: x[1], reverse=True)
            
            return [path for path, _ in recent[:self.max_recent_files]]
        
        except:
            return []
    
    def get_system_context(self) -> Dict:
        """Get system state context"""
        try:
            # Load average
            load_avg = os.getloadavg()
            
            # Disk space
            stat = os.statvfs(os.getcwd())
            disk_usage = 1 - (stat.f_bavail / stat.f_blocks)
            
            return {
                "load_average": load_avg[0],
                "disk_usage_percent": disk_usage * 100,
                "is_busy": load_avg[0] > 2.0,
                "low_disk": disk_usage > 0.9
            }
        
        except:
            return {
                "load_average": 0.0,
                "disk_usage_percent": 0.0,
                "is_busy": False,
                "low_disk": False
            }
    
    def _detect_project_type(self, path: str) -> Optional[str]:
        """Detect project type from common files"""
        indicators = {
            "Python": ["setup.py", "pyproject.toml", "requirements.txt"],
            "Node.js": ["package.json", "node_modules"],
            "Rust": ["Cargo.toml"],
            "Go": ["go.mod"],
            "Java": ["pom.xml", "build.gradle"],
            "C/C++": ["CMakeLists.txt", "Makefile"],
            "Ruby": ["Gemfile"],
            "PHP": ["composer.json"],
            "Docker": ["Dockerfile", "docker-compose.yml"]
        }
        
        for project_type, files in indicators.items():
            for file in files:
                if os.path.exists(os.path.join(path, file)):
                    return project_type
        
        return None
    
    def track_file_access(self, file_path: str):
        """Track file access for recent files list"""
        if file_path not in self.recent_files:
            self.recent_files.insert(0, file_path)
            if len(self.recent_files) > self.max_recent_files:
                self.recent_files.pop()


# Global context manager
_context_manager = None


def get_context_manager() -> ContextManager:
    """Get global context manager instance"""
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextManager()
    return _context_manager

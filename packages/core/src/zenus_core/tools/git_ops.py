"""
Git Operations

Advanced git operations beyond basic commands.
"""

import subprocess
import os
from typing import Optional, List
from zenus_core.tools.base import Tool


class GitOps(Tool):
    """
    Advanced git operations
    
    Capabilities:
    - Clone repositories
    - Commit with smart messages
    - Branch management
    - Push/pull operations
    - View history and diffs
    - Stash operations
    """
    
    def _run_git(self, args: List[str], cwd: Optional[str] = None) -> str:
        """Run git command"""
        cmd = ["git"] + args
        
        if cwd:
            cwd = os.path.expanduser(cwd)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=60
            )
            
            if result.returncode != 0:
                return f"Error: {result.stderr}"
            
            return result.stdout
        except Exception as e:
            return f"Error: {str(e)}"
    
    def clone(self, url: str, directory: Optional[str] = None) -> str:
        """Clone a repository"""
        args = ["clone", url]
        if directory:
            args.append(directory)
        return self._run_git(args)
    
    def status(self, path: str = ".") -> str:
        """Check repository status"""
        return self._run_git(["status"], cwd=path)
    
    def add(self, files: str, path: str = ".") -> str:
        """
        Stage files
        
        Args:
            files: Files to stage ("." for all, or specific paths)
            path: Repository path
        """
        return self._run_git(["add", files], cwd=path)
    
    def commit(self, message: str, path: str = ".") -> str:
        """Commit staged changes"""
        return self._run_git(["commit", "-m", message], cwd=path)
    
    def push(self, remote: str = "origin", branch: Optional[str] = None, path: str = ".") -> str:
        """Push to remote"""
        args = ["push", remote]
        if branch:
            args.append(branch)
        return self._run_git(args, cwd=path)
    
    def pull(self, remote: str = "origin", branch: Optional[str] = None, path: str = ".") -> str:
        """Pull from remote"""
        args = ["pull", remote]
        if branch:
            args.append(branch)
        return self._run_git(args, cwd=path)
    
    def branch(self, name: Optional[str] = None, delete: bool = False, path: str = ".") -> str:
        """
        Branch operations
        
        Args:
            name: Branch name (None to list branches)
            delete: Delete branch
            path: Repository path
        """
        if name is None:
            return self._run_git(["branch"], cwd=path)
        
        if delete:
            return self._run_git(["branch", "-d", name], cwd=path)
        
        return self._run_git(["branch", name], cwd=path)
    
    def checkout(self, branch: str, create: bool = False, path: str = ".") -> str:
        """
        Checkout branch
        
        Args:
            branch: Branch name
            create: Create new branch
            path: Repository path
        """
        args = ["checkout"]
        if create:
            args.append("-b")
        args.append(branch)
        return self._run_git(args, cwd=path)
    
    def log(self, lines: int = 10, path: str = ".") -> str:
        """View commit history"""
        return self._run_git(["log", f"-{lines}", "--oneline"], cwd=path)
    
    def diff(self, file: Optional[str] = None, path: str = ".") -> str:
        """Show changes"""
        args = ["diff"]
        if file:
            args.append(file)
        return self._run_git(args, cwd=path)
    
    def stash(self, action: str = "push", path: str = ".") -> str:
        """
        Stash operations
        
        Args:
            action: push, pop, list, apply
            path: Repository path
        """
        return self._run_git(["stash", action], cwd=path)
    
    def remote(self, action: str = "show", path: str = ".") -> str:
        """
        Remote operations
        
        Args:
            action: show, add, remove
            path: Repository path
        """
        args = ["remote"]
        if action != "show":
            args.append(action)
        args.append("-v")
        return self._run_git(args, cwd=path)

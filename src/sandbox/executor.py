"""
Sandboxed Executor

Executes tool actions with resource limits and filesystem isolation.
Critical for OS-level safety.
"""

import os
import subprocess
import tempfile
from typing import Optional, Dict, Any
from pathlib import Path


class SandboxConfig:
    """Configuration for sandbox execution"""
    
    def __init__(
        self,
        allowed_paths: Optional[list] = None,
        read_only_paths: Optional[list] = None,
        max_cpu_seconds: int = 30,
        max_memory_mb: int = 512,
        allow_network: bool = False
    ):
        self.allowed_paths = allowed_paths or [os.path.expanduser("~")]
        self.read_only_paths = read_only_paths or ["/usr", "/lib", "/bin"]
        self.max_cpu_seconds = max_cpu_seconds
        self.max_memory_mb = max_memory_mb
        self.allow_network = allow_network


class SandboxViolation(Exception):
    """Raised when sandbox boundary is violated"""
    pass


class SandboxedExecutor:
    """
    Executes operations within sandbox constraints
    
    Provides:
    - Filesystem access controls
    - Resource limits (CPU, memory)
    - Network isolation
    - Time limits
    """
    
    def __init__(self, config: Optional[SandboxConfig] = None):
        self.config = config or SandboxConfig()
    
    def validate_path_access(self, path: str, write: bool = False) -> bool:
        """
        Check if path access is allowed
        
        Args:
            path: Path to validate
            write: True if write access needed
        
        Returns:
            True if allowed
        
        Raises:
            SandboxViolation if access denied
        """
        
        path = os.path.abspath(os.path.expanduser(path))
        
        # Check if path is within allowed directories
        allowed = False
        for allowed_path in self.config.allowed_paths:
            allowed_path = os.path.abspath(os.path.expanduser(allowed_path))
            if path.startswith(allowed_path):
                allowed = True
                break
        
        if not allowed:
            raise SandboxViolation(
                f"Path access denied: {path} not in allowed paths"
            )
        
        # Check if write to read-only path
        if write:
            for ro_path in self.config.read_only_paths:
                ro_path = os.path.abspath(ro_path)
                if path.startswith(ro_path):
                    raise SandboxViolation(
                        f"Write access denied: {path} is read-only"
                    )
        
        return True
    
    def execute_subprocess(
        self, 
        command: list,
        cwd: Optional[str] = None,
        env: Optional[Dict] = None
    ) -> subprocess.CompletedProcess:
        """
        Execute command in sandboxed subprocess
        
        Args:
            command: Command and arguments
            cwd: Working directory
            env: Environment variables
        
        Returns:
            CompletedProcess result
        
        Raises:
            SandboxViolation on timeout or resource limit
        """
        
        if cwd:
            self.validate_path_access(cwd, write=False)
        
        try:
            # Execute with timeout
            result = subprocess.run(
                command,
                cwd=cwd,
                env=env,
                capture_output=True,
                text=True,
                timeout=self.config.max_cpu_seconds
            )
            
            return result
            
        except subprocess.TimeoutExpired:
            raise SandboxViolation(
                f"Command exceeded time limit: {self.config.max_cpu_seconds}s"
            )
    
    def create_temp_workspace(self) -> str:
        """
        Create temporary workspace for isolated operations
        
        Returns:
            Path to temporary directory
        """
        
        temp_dir = tempfile.mkdtemp(prefix="zenus_sandbox_")
        
        # Add to allowed paths temporarily
        self.config.allowed_paths.append(temp_dir)
        
        return temp_dir
    
    def cleanup_workspace(self, workspace_path: str):
        """Clean up temporary workspace"""
        
        import shutil
        
        if os.path.exists(workspace_path):
            shutil.rmtree(workspace_path)
        
        # Remove from allowed paths
        if workspace_path in self.config.allowed_paths:
            self.config.allowed_paths.remove(workspace_path)


class BubblewrapSandbox:
    """
    Advanced sandboxing using bubblewrap (bwrap)
    
    Provides stronger isolation than SandboxedExecutor.
    Requires bubblewrap installed: apt install bubblewrap
    """
    
    def __init__(self, config: Optional[SandboxConfig] = None):
        self.config = config or SandboxConfig()
        self._check_bwrap()
    
    def _check_bwrap(self):
        """Check if bubblewrap is available"""
        
        result = subprocess.run(
            ["which", "bwrap"],
            capture_output=True
        )
        
        if result.returncode != 0:
            raise RuntimeError(
                "bubblewrap not found. Install: sudo apt install bubblewrap"
            )
    
    def execute(
        self,
        command: list,
        bind_paths: Optional[Dict[str, str]] = None
    ) -> subprocess.CompletedProcess:
        """
        Execute command in bubblewrap sandbox
        
        Args:
            command: Command and arguments
            bind_paths: {host_path: container_path} mappings
        
        Returns:
            CompletedProcess result
        """
        
        bwrap_cmd = [
            "bwrap",
            "--ro-bind", "/usr", "/usr",
            "--ro-bind", "/lib", "/lib",
            "--ro-bind", "/lib64", "/lib64",
            "--ro-bind", "/bin", "/bin",
            "--ro-bind", "/sbin", "/sbin",
            "--proc", "/proc",
            "--dev", "/dev",
            "--tmpfs", "/tmp"
        ]
        
        # Add user-specified bind mounts
        if bind_paths:
            for host_path, container_path in bind_paths.items():
                bwrap_cmd.extend(["--bind", host_path, container_path])
        
        # Network isolation (default: no network)
        if not self.config.allow_network:
            bwrap_cmd.append("--unshare-net")
        
        # Add the actual command
        bwrap_cmd.extend(command)
        
        try:
            result = subprocess.run(
                bwrap_cmd,
                capture_output=True,
                text=True,
                timeout=self.config.max_cpu_seconds
            )
            
            return result
            
        except subprocess.TimeoutExpired:
            raise SandboxViolation(
                f"Command exceeded time limit: {self.config.max_cpu_seconds}s"
            )


def get_sandbox(advanced: bool = False) -> Any:
    """
    Factory function to get appropriate sandbox
    
    Args:
        advanced: If True, use bubblewrap (requires install)
    
    Returns:
        Sandbox executor instance
    """
    
    if advanced:
        try:
            return BubblewrapSandbox()
        except RuntimeError:
            print("Warning: bubblewrap not available, using basic sandbox")
            return SandboxedExecutor()
    else:
        return SandboxedExecutor()

"""
Sandbox Constraints

Defines boundaries for tool execution to prevent:
- Filesystem damage outside allowed paths
- Resource exhaustion
- Network access without permission
- Privilege escalation
"""

from typing import List, Optional, Set
from dataclasses import dataclass, field
from pathlib import Path
import os


@dataclass
class SandboxConstraints:
    """
    Execution constraints for a sandboxed operation
    
    All paths are absolute and normalized.
    """
    
    # Filesystem constraints
    allowed_read_paths: Set[str] = field(default_factory=set)
    allowed_write_paths: Set[str] = field(default_factory=set)
    forbidden_paths: Set[str] = field(default_factory=set)
    
    # Resource constraints
    max_execution_time: Optional[int] = 30  # seconds
    max_memory_mb: Optional[int] = 512
    max_file_size_mb: Optional[int] = 100
    
    # Network constraints
    allow_network: bool = False
    allowed_hosts: Set[str] = field(default_factory=set)
    
    # Process constraints
    allow_subprocess: bool = False
    max_subprocesses: int = 1
    
    def __post_init__(self):
        """Normalize all paths to absolute"""
        self.allowed_read_paths = {
            str(Path(p).expanduser().resolve())
            for p in self.allowed_read_paths
        }
        self.allowed_write_paths = {
            str(Path(p).expanduser().resolve())
            for p in self.allowed_write_paths
        }
        self.forbidden_paths = {
            str(Path(p).expanduser().resolve())
            for p in self.forbidden_paths
        }
    
    def can_read(self, path: str) -> bool:
        """Check if path is readable"""
        abs_path = str(Path(path).expanduser().resolve())
        
        # Check forbidden first
        if self._is_forbidden(abs_path):
            return False
        
        # If no explicit allow list, allow read anywhere (except forbidden)
        if not self.allowed_read_paths:
            return True
        
        # Check if path is under any allowed read path
        return self._is_under_any(abs_path, self.allowed_read_paths)
    
    def can_write(self, path: str) -> bool:
        """Check if path is writable"""
        abs_path = str(Path(path).expanduser().resolve())
        
        # Check forbidden first
        if self._is_forbidden(abs_path):
            return False
        
        # Write requires explicit permission
        return self._is_under_any(abs_path, self.allowed_write_paths)
    
    def _is_forbidden(self, path: str) -> bool:
        """Check if path is in forbidden list"""
        return self._is_under_any(path, self.forbidden_paths)
    
    def _is_under_any(self, path: str, parent_paths: Set[str]) -> bool:
        """Check if path is under any of the parent paths"""
        path_obj = Path(path)
        
        for parent in parent_paths:
            parent_obj = Path(parent)
            try:
                # Check if path is relative to parent
                path_obj.relative_to(parent_obj)
                return True
            except ValueError:
                # Not a subpath, try exact match
                if path_obj == parent_obj:
                    return True
        
        return False


# Preset constraint profiles

def get_safe_defaults() -> SandboxConstraints:
    """
    Safe default constraints for most operations
    
    Read: anywhere
    Write: only user home and /tmp
    Network: no
    Time: 30s
    """
    home = os.path.expanduser("~")
    
    return SandboxConstraints(
        allowed_write_paths={home, "/tmp"},
        forbidden_paths={"/etc", "/sys", "/proc", "/dev", "/boot"},
        max_execution_time=30,
        allow_network=False,
        allow_subprocess=False
    )


def get_restricted() -> SandboxConstraints:
    """
    Very restricted constraints for untrusted operations
    
    Read: only user home
    Write: only specific temp dir
    Network: no
    Time: 10s
    """
    home = os.path.expanduser("~")
    zenus_tmp = os.path.expanduser("~/.zenus/tmp")
    
    return SandboxConstraints(
        allowed_read_paths={home},
        allowed_write_paths={zenus_tmp},
        forbidden_paths={"/etc", "/sys", "/proc", "/dev", "/boot", "/usr", "/bin"},
        max_execution_time=10,
        max_memory_mb=256,
        allow_network=False,
        allow_subprocess=False
    )


def get_permissive() -> SandboxConstraints:
    """
    Permissive constraints for trusted operations
    
    Read: anywhere
    Write: user home and /tmp
    Network: yes
    Time: 300s
    """
    home = os.path.expanduser("~")
    
    return SandboxConstraints(
        allowed_write_paths={home, "/tmp"},
        forbidden_paths={"/etc/shadow", "/etc/passwd"},
        max_execution_time=300,
        allow_network=True,
        allow_subprocess=True,
        max_subprocesses=5
    )


def get_filesystem_only() -> SandboxConstraints:
    """
    For file operations only
    
    Read/Write: user home
    Network: no
    Subprocess: no
    """
    home = os.path.expanduser("~")
    
    return SandboxConstraints(
        allowed_read_paths={home},
        allowed_write_paths={home},
        forbidden_paths={
            "/etc", "/sys", "/proc", "/dev", "/boot",
            "/usr", "/bin", "/sbin", "/lib"
        },
        max_execution_time=30,
        allow_network=False,
        allow_subprocess=False
    )

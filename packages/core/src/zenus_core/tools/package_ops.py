"""
Package Operations

Manage system packages across different package managers.
Supports apt, dnf, pacman, and snap.
"""

import subprocess
import os
from typing import List, Optional
from zenus_core.tools.base import Tool


class PackageOps(Tool):
    """
    System package management
    
    Capabilities:
    - Install/remove packages
    - Update system packages
    - Search for packages
    - List installed packages
    - Clean package cache
    """
    
    def __init__(self):
        self.package_manager = self._detect_package_manager()
    
    def _detect_package_manager(self) -> str:
        """Detect which package manager is available"""
        managers = {
            "apt": "/usr/bin/apt",
            "apt-get": "/usr/bin/apt-get",
            "dnf": "/usr/bin/dnf",
            "yum": "/usr/bin/yum",
            "pacman": "/usr/bin/pacman",
            "zypper": "/usr/bin/zypper"
        }
        
        for name, path in managers.items():
            if os.path.exists(path):
                return name
        
        return "unknown"
    
    def _run_command(self, cmd: List[str], sudo: bool = False) -> str:
        """Run package manager command"""
        if sudo and os.geteuid() != 0:
            cmd = ["sudo"] + cmd
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 min timeout
            )
            
            if result.returncode != 0:
                return f"Error: {result.stderr}"
            
            return result.stdout
        
        except subprocess.TimeoutExpired:
            return "Error: Command timed out"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def install(self, package: str, confirm: bool = False) -> str:
        """
        Install package
        
        Args:
            package: Package name to install
            confirm: Auto-confirm installation
        
        Returns:
            Installation result
        """
        if self.package_manager == "apt":
            cmd = ["apt", "install", package]
            if confirm:
                cmd.append("-y")
        
        elif self.package_manager == "dnf":
            cmd = ["dnf", "install", package]
            if confirm:
                cmd.append("-y")
        
        elif self.package_manager == "pacman":
            cmd = ["pacman", "-S", package]
            if confirm:
                cmd.append("--noconfirm")
        
        else:
            return f"Package manager '{self.package_manager}' not supported"
        
        return self._run_command(cmd, sudo=True)
    
    def remove(self, package: str, confirm: bool = False) -> str:
        """
        Remove package
        
        Args:
            package: Package name to remove
            confirm: Auto-confirm removal
        
        Returns:
            Removal result
        """
        if self.package_manager == "apt":
            cmd = ["apt", "remove", package]
            if confirm:
                cmd.append("-y")
        
        elif self.package_manager == "dnf":
            cmd = ["dnf", "remove", package]
            if confirm:
                cmd.append("-y")
        
        elif self.package_manager == "pacman":
            cmd = ["pacman", "-R", package]
            if confirm:
                cmd.append("--noconfirm")
        
        else:
            return f"Package manager '{self.package_manager}' not supported"
        
        return self._run_command(cmd, sudo=True)
    
    def update(self, upgrade: bool = False) -> str:
        """
        Update package lists or upgrade packages
        
        Args:
            upgrade: Also upgrade installed packages
        
        Returns:
            Update result
        """
        if self.package_manager == "apt":
            cmd = ["apt", "update"]
            if upgrade:
                result = self._run_command(cmd, sudo=True)
                cmd = ["apt", "upgrade", "-y"]
                result += "\n" + self._run_command(cmd, sudo=True)
                return result
        
        elif self.package_manager == "dnf":
            cmd = ["dnf", "check-update"] if not upgrade else ["dnf", "upgrade", "-y"]
        
        elif self.package_manager == "pacman":
            cmd = ["pacman", "-Sy"] if not upgrade else ["pacman", "-Syu", "--noconfirm"]
        
        else:
            return f"Package manager '{self.package_manager}' not supported"
        
        return self._run_command(cmd, sudo=True)
    
    def search(self, query: str) -> str:
        """
        Search for packages
        
        Args:
            query: Search query
        
        Returns:
            Search results
        """
        if self.package_manager == "apt":
            cmd = ["apt", "search", query]
        
        elif self.package_manager == "dnf":
            cmd = ["dnf", "search", query]
        
        elif self.package_manager == "pacman":
            cmd = ["pacman", "-Ss", query]
        
        else:
            return f"Package manager '{self.package_manager}' not supported"
        
        return self._run_command(cmd, sudo=False)
    
    def list_installed(self, pattern: Optional[str] = None) -> str:
        """
        List installed packages
        
        Args:
            pattern: Filter pattern (optional)
        
        Returns:
            List of installed packages
        """
        if self.package_manager == "apt":
            cmd = ["apt", "list", "--installed"]
        
        elif self.package_manager == "dnf":
            cmd = ["dnf", "list", "installed"]
        
        elif self.package_manager == "pacman":
            cmd = ["pacman", "-Q"]
        
        else:
            return f"Package manager '{self.package_manager}' not supported"
        
        result = self._run_command(cmd, sudo=False)
        
        if pattern:
            lines = result.split("\n")
            filtered = [line for line in lines if pattern.lower() in line.lower()]
            return "\n".join(filtered)
        
        return result
    
    def clean(self) -> str:
        """
        Clean package cache
        
        Returns:
            Clean result
        """
        if self.package_manager == "apt":
            cmd = ["apt", "clean"]
        
        elif self.package_manager == "dnf":
            cmd = ["dnf", "clean", "all"]
        
        elif self.package_manager == "pacman":
            cmd = ["pacman", "-Sc", "--noconfirm"]
        
        else:
            return f"Package manager '{self.package_manager}' not supported"
        
        return self._run_command(cmd, sudo=True)
    
    def info(self, package: str) -> str:
        """
        Show package information
        
        Args:
            package: Package name
        
        Returns:
            Package information
        """
        if self.package_manager == "apt":
            cmd = ["apt", "show", package]
        
        elif self.package_manager == "dnf":
            cmd = ["dnf", "info", package]
        
        elif self.package_manager == "pacman":
            cmd = ["pacman", "-Si", package]
        
        else:
            return f"Package manager '{self.package_manager}' not supported"
        
        return self._run_command(cmd, sudo=False)

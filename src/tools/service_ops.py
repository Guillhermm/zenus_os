"""
Service Operations

Manage system services using systemctl.
"""

import subprocess
from typing import Optional
from tools.base import Tool


class ServiceOps(Tool):
    """
    System service management via systemctl
    
    Capabilities:
    - Start/stop/restart services
    - Enable/disable services at boot
    - Check service status
    - View service logs
    """
    
    def _run_systemctl(self, args: list, sudo: bool = False) -> str:
        """Run systemctl command"""
        cmd = ["systemctl"] + args
        
        if sudo:
            cmd = ["sudo"] + cmd
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return result.stdout + result.stderr
        
        except Exception as e:
            return f"Error: {str(e)}"
    
    def start(self, service: str) -> str:
        """Start a service"""
        return self._run_systemctl(["start", service], sudo=True)
    
    def stop(self, service: str) -> str:
        """Stop a service"""
        return self._run_systemctl(["stop", service], sudo=True)
    
    def restart(self, service: str) -> str:
        """Restart a service"""
        return self._run_systemctl(["restart", service], sudo=True)
    
    def status(self, service: str) -> str:
        """Check service status"""
        return self._run_systemctl(["status", service], sudo=False)
    
    def enable(self, service: str) -> str:
        """Enable service at boot"""
        return self._run_systemctl(["enable", service], sudo=True)
    
    def disable(self, service: str) -> str:
        """Disable service at boot"""
        return self._run_systemctl(["disable", service], sudo=True)
    
    def list_services(self, state: Optional[str] = None) -> str:
        """
        List services
        
        Args:
            state: Filter by state (active, inactive, failed)
        """
        args = ["list-units", "--type=service"]
        
        if state:
            args.append(f"--state={state}")
        
        return self._run_systemctl(args, sudo=False)
    
    def logs(self, service: str, lines: int = 50) -> str:
        """
        View service logs
        
        Args:
            service: Service name
            lines: Number of lines to show
        """
        try:
            result = subprocess.run(
                ["journalctl", "-u", service, "-n", str(lines), "--no-pager"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.stdout
        except Exception as e:
            return f"Error: {str(e)}"

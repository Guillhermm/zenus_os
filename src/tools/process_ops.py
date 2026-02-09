"""
Process Operations Tool

Provides process management capabilities.
"""

import os
import signal
import psutil
from tools.base import Tool


class ProcessOps(Tool):
    """Process management operations"""
    
    name = "ProcessOps"
    
    def find_by_name(self, name: str):
        """Find processes by name"""
        matches = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if name.lower() in proc.info['name'].lower():
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    matches.append(
                        f"PID {proc.info['pid']}: {proc.info['name']} ({cmdline[:50]})"
                    )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        if not matches:
            return f"No processes found matching '{name}'"
        
        return "\n".join(matches)
    
    def info(self, pid: int):
        """Get detailed information about a process"""
        try:
            proc = psutil.Process(pid)
            with proc.oneshot():
                info_lines = [
                    f"PID: {proc.pid}",
                    f"Name: {proc.name()}",
                    f"Status: {proc.status()}",
                    f"CPU: {proc.cpu_percent()}%",
                    f"Memory: {proc.memory_percent():.1f}%",
                    f"Command: {' '.join(proc.cmdline())}"
                ]
            return "\n".join(info_lines)
        except psutil.NoSuchProcess:
            return f"Process {pid} not found"
        except psutil.AccessDenied:
            return f"Access denied to process {pid}"
    
    def kill(self, pid: int, force: bool = False):
        """Kill a process (HIGH RISK - requires confirmation)"""
        try:
            proc = psutil.Process(pid)
            name = proc.name()
            
            if force:
                proc.kill()  # SIGKILL
                return f"Force killed process {pid} ({name})"
            else:
                proc.terminate()  # SIGTERM
                return f"Terminated process {pid} ({name})"
        except psutil.NoSuchProcess:
            return f"Process {pid} not found"
        except psutil.AccessDenied:
            return f"Access denied to kill process {pid}"

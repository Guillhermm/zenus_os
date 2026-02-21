"""
System Operations Tool

Provides system information and monitoring capabilities.
"""

import os
import shutil
import psutil
from tools.base import Tool


class SystemOps(Tool):
    """System information and monitoring operations"""
    
    name = "SystemOps"
    
    def disk_usage(self, path: str = "/"):
        """Get disk usage for a path"""
        path = os.path.expanduser(path)
        usage = shutil.disk_usage(path)
        total_gb = usage.total / (1024 ** 3)
        used_gb = usage.used / (1024 ** 3)
        free_gb = usage.free / (1024 ** 3)
        percent = (usage.used / usage.total) * 100
        
        return (
            f"Disk {path}: "
            f"{used_gb:.1f}GB used / {total_gb:.1f}GB total "
            f"({percent:.1f}% used, {free_gb:.1f}GB free)"
        )
    
    def memory_info(self):
        """Get system memory information"""
        mem = psutil.virtual_memory()
        total_gb = mem.total / (1024 ** 3)
        used_gb = mem.used / (1024 ** 3)
        available_gb = mem.available / (1024 ** 3)
        percent = mem.percent
        
        return (
            f"Memory: "
            f"{used_gb:.1f}GB used / {total_gb:.1f}GB total "
            f"({percent:.1f}% used, {available_gb:.1f}GB available)"
        )
    
    def cpu_info(self):
        """Get CPU usage information"""
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        return f"CPU: {cpu_percent}% used ({cpu_count} cores)"
    
    def list_processes(self, limit: int = 10):
        """List top processes by memory usage"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Sort by memory usage
        processes.sort(key=lambda p: p['memory_percent'], reverse=True)
        
        result_lines = []
        for proc in processes[:limit]:
            result_lines.append(
                f"PID {proc['pid']}: {proc['name']} "
                f"({proc['memory_percent']:.1f}% mem)"
            )
        
        return "\n".join(result_lines)
    
    def uptime(self):
        """Get system uptime"""
        boot_time = psutil.boot_time()
        uptime_seconds = psutil.time.time() - boot_time
        
        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        
        return f"System uptime: {days}d {hours}h {minutes}m"

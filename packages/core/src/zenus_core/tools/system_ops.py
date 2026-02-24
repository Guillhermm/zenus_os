"""
System Operations Tool

Provides system information and monitoring capabilities.
"""

import os
import shutil
import psutil
from zenus_core.tools.base import Tool


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
    
    def find_large_files(self, path: str = "~", min_size_mb: int = 100, limit: int = 20):
        """
        Find large files in a directory tree
        
        Args:
            path: Starting path (default: home directory)
            min_size_mb: Minimum file size in MB
            limit: Maximum number of results
        
        Returns:
            List of large files with sizes
        """
        import os
        from pathlib import Path
        
        path = os.path.expanduser(path)
        min_size_bytes = min_size_mb * 1024 * 1024
        
        large_files = []
        
        try:
            for root, dirs, files in os.walk(path):
                # Skip hidden directories and common system directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', '.git']]
                
                for file in files:
                    try:
                        filepath = os.path.join(root, file)
                        size = os.path.getsize(filepath)
                        
                        if size >= min_size_bytes:
                            size_mb = size / (1024 * 1024)
                            large_files.append((filepath, size_mb))
                    except (OSError, PermissionError):
                        continue
                
                # Stop if we have enough results
                if len(large_files) >= limit * 2:  # Collect more than needed for sorting
                    break
            
            # Sort by size (largest first) and take top N
            large_files.sort(key=lambda x: x[1], reverse=True)
            large_files = large_files[:limit]
            
            if not large_files:
                return f"No files larger than {min_size_mb}MB found in {path}"
            
            result_lines = [f"Found {len(large_files)} large files:"]
            for filepath, size_mb in large_files:
                result_lines.append(f"  {size_mb:.1f}MB: {filepath}")
            
            return "\n".join(result_lines)
        
        except Exception as e:
            return f"Error scanning for large files: {str(e)}"
    
    def check_resource_usage(self):
        """
        Get comprehensive system resource status
        
        Returns:
            Combined CPU, memory, and disk usage
        """
        lines = []
        
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        lines.append(f"CPU: {cpu_percent}% used ({cpu_count} cores)")
        
        # Memory
        mem = psutil.virtual_memory()
        mem_total_gb = mem.total / (1024 ** 3)
        mem_used_gb = mem.used / (1024 ** 3)
        mem_available_gb = mem.available / (1024 ** 3)
        lines.append(f"Memory: {mem_used_gb:.1f}GB / {mem_total_gb:.1f}GB ({mem.percent:.1f}% used, {mem_available_gb:.1f}GB free)")
        
        # Disk (root)
        disk = shutil.disk_usage("/")
        disk_total_gb = disk.total / (1024 ** 3)
        disk_used_gb = disk.used / (1024 ** 3)
        disk_free_gb = disk.free / (1024 ** 3)
        disk_percent = (disk.used / disk.total) * 100
        lines.append(f"Disk: {disk_used_gb:.1f}GB / {disk_total_gb:.1f}GB ({disk_percent:.1f}% used, {disk_free_gb:.1f}GB free)")
        
        # Warnings
        warnings = []
        if mem.percent > 80:
            warnings.append("⚠️  Memory usage is high (>80%)")
        if disk_percent > 85:
            warnings.append("⚠️  Disk usage is high (>85%)")
        if cpu_percent > 90:
            warnings.append("⚠️  CPU usage is very high (>90%)")
        
        if warnings:
            lines.append("")
            lines.extend(warnings)
        
        return "\n".join(lines)

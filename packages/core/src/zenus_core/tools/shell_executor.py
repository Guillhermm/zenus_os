"""
Shell Command Executor with Real-Time Streaming

Provides robust shell command execution with:
- Real-time output streaming
- No fixed timeouts
- Better error handling
- Output capture for observations
"""

import subprocess
import sys
from typing import Optional, Tuple
from rich.console import Console

console = Console()


class StreamingExecutor:
    """Execute shell commands with real-time output streaming"""
    
    def __init__(self, timeout: Optional[int] = None):
        """
        Initialize executor
        
        Args:
            timeout: Optional timeout in seconds (None = no timeout)
        """
        self.timeout = timeout
    
    def execute(
        self,
        cmd: list[str],
        sudo: bool = False,
        stream_output: bool = True,
        capture: bool = True
    ) -> Tuple[int, str, str]:
        """
        Execute command with optional streaming
        
        Args:
            cmd: Command as list of strings
            sudo: Prepend sudo if needed
            stream_output: Print output in real-time
            capture: Capture output for return value
        
        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        if sudo:
            import os
            if os.geteuid() != 0:
                cmd = ["sudo"] + cmd
        
        try:
            if stream_output:
                return self._execute_streaming(cmd, capture)
            else:
                return self._execute_quiet(cmd)
        
        except subprocess.TimeoutExpired:
            return (1, "", "Error: Command timed out")
        except Exception as e:
            return (1, "", f"Error: {str(e)}")
    
    def _execute_streaming(
        self,
        cmd: list[str],
        capture: bool
    ) -> Tuple[int, str, str]:
        """Execute with real-time output streaming"""
        stdout_lines = []
        stderr_lines = []
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1  # Line buffered
        )
        
        # Stream stdout in real-time
        try:
            for line in iter(process.stdout.readline, ''):
                if not line:
                    break
                
                # Print to console
                console.print(f"  [dim]{line.rstrip()}[/dim]")
                
                # Capture if needed
                if capture:
                    stdout_lines.append(line)
            
            # Wait for completion
            process.wait(timeout=self.timeout)
            
            # Get any remaining stderr
            stderr = process.stderr.read()
            if stderr:
                console.print(f"  [yellow]{stderr.rstrip()}[/yellow]")
                stderr_lines.append(stderr)
        
        finally:
            process.stdout.close()
            process.stderr.close()
        
        stdout = ''.join(stdout_lines)
        stderr = ''.join(stderr_lines)
        
        return (process.returncode, stdout, stderr)
    
    def _execute_quiet(
        self,
        cmd: list[str]
    ) -> Tuple[int, str, str]:
        """Execute without streaming (quiet mode)"""
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=self.timeout
        )
        
        return (result.returncode, result.stdout, result.stderr)


def execute_shell_command(
    cmd: list[str],
    sudo: bool = False,
    stream: bool = True,
    timeout: Optional[int] = None
) -> str:
    """
    High-level wrapper for shell command execution
    
    Args:
        cmd: Command as list of strings
        sudo: Run with sudo
        stream: Stream output in real-time
        timeout: Optional timeout (None = no timeout)
    
    Returns:
        Combined stdout/stderr as string
        
    Raises:
        RuntimeError: If command fails
    """
    executor = StreamingExecutor(timeout=timeout)
    returncode, stdout, stderr = executor.execute(cmd, sudo=sudo, stream_output=stream)
    
    # Format output for observations
    output_parts = []
    
    if stdout.strip():
        output_parts.append(stdout.strip())
    
    if stderr.strip():
        output_parts.append(f"[stderr] {stderr.strip()}")
    
    combined_output = "\n".join(output_parts) if output_parts else "(no output)"
    
    if returncode != 0:
        raise RuntimeError(f"Command failed (exit {returncode}): {combined_output}")
    
    return combined_output

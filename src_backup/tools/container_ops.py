"""
Container Operations

Manage Docker containers and images.
Falls back to Podman if Docker not available.
"""

import subprocess
import os
from typing import Optional, List
from tools.base import Tool


class ContainerOps(Tool):
    """
    Container management (Docker/Podman)
    
    Capabilities:
    - Run containers
    - List/stop/remove containers
    - Build/pull/push images
    - Manage volumes and networks
    """
    
    def __init__(self):
        self.runtime = self._detect_runtime()
    
    def _detect_runtime(self) -> str:
        """Detect container runtime (docker or podman)"""
        for runtime in ["docker", "podman"]:
            try:
                subprocess.run(
                    [runtime, "--version"],
                    capture_output=True,
                    timeout=2
                )
                return runtime
            except:
                continue
        return "none"
    
    def _run(self, args: List[str]) -> str:
        """Run container command"""
        if self.runtime == "none":
            return "Error: No container runtime found (install docker or podman)"
        
        cmd = [self.runtime] + args
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                return f"Error: {result.stderr}"
            
            return result.stdout
        except Exception as e:
            return f"Error: {str(e)}"
    
    def run(
        self,
        image: str,
        name: Optional[str] = None,
        ports: Optional[str] = None,
        volumes: Optional[str] = None,
        detach: bool = False,
        command: Optional[str] = None
    ) -> str:
        """
        Run a container
        
        Args:
            image: Image name
            name: Container name
            ports: Port mapping (e.g., "8080:80")
            volumes: Volume mapping (e.g., "/host:/container")
            detach: Run in background
            command: Command to run in container
        """
        args = ["run"]
        
        if detach:
            args.append("-d")
        
        if name:
            args.extend(["--name", name])
        
        if ports:
            args.extend(["-p", ports])
        
        if volumes:
            args.extend(["-v", volumes])
        
        args.append(image)
        
        if command:
            args.extend(command.split())
        
        return self._run(args)
    
    def ps(self, all: bool = False) -> str:
        """List containers"""
        args = ["ps"]
        if all:
            args.append("-a")
        return self._run(args)
    
    def stop(self, container: str) -> str:
        """Stop a container"""
        return self._run(["stop", container])
    
    def remove(self, container: str, force: bool = False) -> str:
        """Remove a container"""
        args = ["rm"]
        if force:
            args.append("-f")
        args.append(container)
        return self._run(args)
    
    def logs(self, container: str, lines: int = 50) -> str:
        """View container logs"""
        return self._run(["logs", "--tail", str(lines), container])
    
    def exec(self, container: str, command: str) -> str:
        """Execute command in running container"""
        return self._run(["exec", container] + command.split())
    
    def images(self) -> str:
        """List images"""
        return self._run(["images"])
    
    def pull(self, image: str) -> str:
        """Pull an image"""
        return self._run(["pull", image])
    
    def build(self, path: str, tag: str) -> str:
        """Build image from Dockerfile"""
        return self._run(["build", "-t", tag, path])
    
    def rmi(self, image: str, force: bool = False) -> str:
        """Remove an image"""
        args = ["rmi"]
        if force:
            args.append("-f")
        args.append(image)
        return self._run(args)

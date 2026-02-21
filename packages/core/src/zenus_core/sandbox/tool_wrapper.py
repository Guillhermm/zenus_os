"""
Tool Wrapper

Wraps tool execution with sandbox enforcement.
"""

from typing import Any, Dict
from zenus_core.sandbox.executor import SandboxedExecutor, SandboxViolation, SandboxConfig
from zenus_core.tools.base import Tool
from zenus_core.brain.llm.schemas import Step


class SandboxedTool:
    """
    Wrapper that adds sandbox enforcement to tool execution
    
    Usage:
        wrapped_tool = SandboxedTool(file_ops, sandbox_config)
        result = wrapped_tool.execute(step)
    """
    
    def __init__(self, tool: Tool, sandbox: SandboxedExecutor):
        self.tool = tool
        self.sandbox = sandbox
    
    def execute(self, step: Step) -> Any:
        """
        Execute tool action with sandbox enforcement
        
        Args:
            step: The step to execute
        
        Returns:
            Tool execution result
        
        Raises:
            SandboxViolation if sandbox boundary violated
        """
        
        # Validate path arguments before execution
        self._validate_step_paths(step)
        
        # Get the action method
        action = getattr(self.tool, step.action)
        
        # Execute with sandbox context
        try:
            result = action(**step.args)
            return result
        except Exception as e:
            # Wrap permission errors as sandbox violations
            if "Permission denied" in str(e):
                raise SandboxViolation(f"Permission denied: {e}")
            raise
    
    def _validate_step_paths(self, step: Step):
        """Validate all path arguments in step"""
        
        # Check common path argument names
        path_args = ["path", "source", "destination", "src", "dst", "file_path"]
        
        for arg_name in path_args:
            if arg_name in step.args:
                path_value = step.args[arg_name]
                
                # Determine if write access needed based on action
                write_actions = ["mkdir", "move", "write_file", "touch", "delete"]
                write_needed = step.action in write_actions
                
                # Validate access
                self.sandbox.validate_path_access(path_value, write=write_needed)


class SandboxedToolRegistry:
    """
    Registry that wraps all tools with sandbox enforcement
    
    Usage:
        registry = SandboxedToolRegistry(TOOLS, sandbox_config)
        wrapped_tool = registry.get("FileOps")
    """
    
    def __init__(self, tools: Dict[str, Tool], sandbox_config: SandboxConfig):
        self.sandbox = SandboxedExecutor(sandbox_config)
        self.wrapped_tools = {
            name: SandboxedTool(tool, self.sandbox)
            for name, tool in tools.items()
        }
    
    def get(self, tool_name: str) -> SandboxedTool:
        """Get wrapped tool by name"""
        return self.wrapped_tools.get(tool_name)
    
    def keys(self):
        """Get all tool names"""
        return self.wrapped_tools.keys()

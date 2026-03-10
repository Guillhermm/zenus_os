"""
Tool Wrapper

Wraps tool execution with sandbox enforcement (composition pattern).
For the inheritance pattern see sandbox.executor.SandboxedToolBase.
"""

from typing import Any, Dict
from zenus_core.sandbox.constraints import SandboxConstraints, get_safe_defaults
from zenus_core.sandbox.executor import SandboxExecutor, SandboxViolation
from zenus_core.tools.base import Tool
from zenus_core.brain.llm.schemas import Step


class ToolSandboxWrapper:
    """
    Wraps an existing Tool instance with sandbox enforcement (composition pattern).

    Usage:
        wrapped_tool = ToolSandboxWrapper(file_ops, sandbox)
        result = wrapped_tool.execute(step)
    """

    def __init__(self, tool: Tool, sandbox: SandboxExecutor):
        self.tool = tool
        self.sandbox = sandbox

    def execute(self, step: Step) -> Any:
        """
        Execute tool action with sandbox enforcement.

        Raises:
            SandboxViolation if sandbox boundary violated
        """
        self._validate_step_paths(step)
        action = getattr(self.tool, step.action)
        try:
            result = action(**step.args)
            return result
        except Exception as e:
            if "Permission denied" in str(e):
                raise SandboxViolation(f"Permission denied: {e}")
            raise

    def _validate_step_paths(self, step: Step):
        """Validate all path arguments in step"""
        path_args = ["path", "source", "destination", "src", "dst", "file_path"]
        write_actions = ["mkdir", "move", "write_file", "touch", "delete"]

        for arg_name in path_args:
            if arg_name in step.args:
                path_value = step.args[arg_name]
                write_needed = step.action in write_actions
                self.sandbox.validate_path_access(path_value, is_write=write_needed)


class ToolSandboxRegistry:
    """
    Registry that wraps all tools with sandbox enforcement.

    Usage:
        registry = ToolSandboxRegistry(TOOLS, constraints)
        wrapped_tool = registry.get("FileOps")
    """

    def __init__(self, tools: Dict[str, Tool], constraints: SandboxConstraints = None):
        self.sandbox = SandboxExecutor(constraints or get_safe_defaults())
        self.wrapped_tools = {
            name: ToolSandboxWrapper(tool, self.sandbox)
            for name, tool in tools.items()
        }

    def get(self, tool_name: str) -> ToolSandboxWrapper:
        """Get wrapped tool by name"""
        return self.wrapped_tools.get(tool_name)

    def keys(self):
        """Get all tool names"""
        return self.wrapped_tools.keys()

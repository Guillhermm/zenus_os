"""
Tests for plan execution
"""

import pytest
from unittest.mock import Mock
from zenus_core.brain.llm.schemas import IntentIR, Step
from zenus_core.brain.planner import execute_plan
from safety.policy import SafetyError
from zenus_core.tools.file_ops import FileOps


class TestPlanner:
    """Test plan execution logic"""
    
    def setup_method(self):
        """Reset tool registry before each test"""
        from tools import registry
        # Store original and reset
        self.original_tools = registry.TOOLS.copy()
        registry.TOOLS.clear()
        registry.TOOLS["FileOps"] = FileOps()
    
    def teardown_method(self):
        """Restore tool registry after each test"""
        from tools import registry
        registry.TOOLS.clear()
        registry.TOOLS.update(self.original_tools)
    
    def test_executes_simple_plan(self, capsys):
        """Should execute a simple single-step plan"""
        # Create mock tool
        mock_tool = Mock()
        mock_tool.scan = Mock(return_value=["file1.txt", "file2.txt"])
        
        # Replace in registry
        from tools import registry
        registry.TOOLS["FileOps"] = mock_tool
        
        step = Step(tool="FileOps", action="scan", args={"path": "/tmp"}, risk=0)
        intent = IntentIR(
            goal="List files in tmp",
            requires_confirmation=False,
            steps=[step]
        )
        
        execute_plan(intent)
        
        # Verify tool was called
        mock_tool.scan.assert_called_once_with(path="/tmp")
        
        # Verify output
        captured = capsys.readouterr()
        assert "Done:" in captured.out
    
    def test_executes_multi_step_plan(self):
        """Should execute multiple steps in sequence"""
        # Track calls
        calls = []
        
        class MockTool:
            def mkdir(self, **kwargs):
                calls.append(("mkdir", kwargs))
                return "Created"
            
            def touch(self, **kwargs):
                calls.append(("touch", kwargs))
                return "Touched"
        
        from tools import registry
        registry.TOOLS["FileOps"] = MockTool()
        
        steps = [
            Step(tool="FileOps", action="mkdir", args={"path": "/tmp/test"}, risk=1),
            Step(tool="FileOps", action="touch", args={"path": "/tmp/test/file"}, risk=1)
        ]
        intent = IntentIR(
            goal="Create directory and file",
            requires_confirmation=False,
            steps=steps
        )
        
        execute_plan(intent)
        
        # Verify both steps executed in order
        assert len(calls) == 2
        assert calls[0] == ("mkdir", {"path": "/tmp/test"})
        assert calls[1] == ("touch", {"path": "/tmp/test/file"})
    
    def test_stops_on_safety_error(self):
        """Should stop execution if safety check fails"""
        step = Step(tool="FileOps", action="delete", args={}, risk=3)
        intent = IntentIR(goal="Delete", requires_confirmation=False, steps=[step])
        
        with pytest.raises(SafetyError):
            execute_plan(intent)
    
    def test_raises_on_missing_tool(self):
        """Should raise ValueError if tool not found"""
        from tools import registry
        # Remove FileOps
        del registry.TOOLS["FileOps"]
        
        step = Step(tool="NonExistent", action="test", args={}, risk=0)
        intent = IntentIR(goal="Test", requires_confirmation=False, steps=[step])
        
        with pytest.raises(ValueError, match="Tool not found"):
            execute_plan(intent)
    
    def test_raises_on_missing_action(self):
        """Should raise ValueError if action not found"""
        class MockTool:
            def scan(self):
                return "result"
        
        from tools import registry
        registry.TOOLS["FileOps"] = MockTool()
        
        step = Step(tool="FileOps", action="nonexistent", args={}, risk=0)
        intent = IntentIR(goal="Test", requires_confirmation=False, steps=[step])
        
        with pytest.raises(ValueError, match="Action not found"):
            execute_plan(intent)
    
    def test_logs_steps_when_logger_provided(self):
        """Should log step results when logger is provided"""
        mock_tool = Mock()
        mock_tool.scan = Mock(return_value="result")
        mock_logger = Mock()
        
        from tools import registry
        registry.TOOLS["FileOps"] = mock_tool
        
        step = Step(tool="FileOps", action="scan", args={}, risk=0)
        intent = IntentIR(goal="Test", requires_confirmation=False, steps=[step])
        
        execute_plan(intent, logger=mock_logger)
        
        # Verify logger was called
        mock_logger.log_step_result.assert_called_once()
        args = mock_logger.log_step_result.call_args[0]
        assert args[0] == "FileOps"
        assert args[1] == "scan"
        assert args[3] is True  # success

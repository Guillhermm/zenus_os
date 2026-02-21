"""
Tests for safety policy enforcement
"""

import pytest
from zenus_core.brain.llm.schemas import Step
from zenus_core.safety.policy import check_step, SafetyError


class TestSafetyPolicy:
    """Test safety policy checks"""
    
    def test_allows_read_operations(self):
        """Risk 0 (read) operations should be allowed"""
        step = Step(tool="FileOps", action="scan", args={}, risk=0)
        assert check_step(step) is True
    
    def test_allows_create_operations(self):
        """Risk 1 (create) operations should be allowed"""
        step = Step(tool="FileOps", action="mkdir", args={}, risk=1)
        assert check_step(step) is True
    
    def test_allows_modify_operations(self):
        """Risk 2 (modify) operations should be allowed"""
        step = Step(tool="FileOps", action="move", args={}, risk=2)
        assert check_step(step) is True
    
    def test_blocks_delete_operations(self):
        """Risk 3 (delete) operations should be blocked"""
        step = Step(tool="FileOps", action="delete", args={}, risk=3)
        
        with pytest.raises(SafetyError) as exc_info:
            check_step(step)
        
        assert "High risk operation blocked" in str(exc_info.value)
        assert "risk=3" in str(exc_info.value)
    
    def test_blocks_unknown_high_risk(self):
        """Any risk >= 3 should be blocked"""
        # Test with risk=3 (max allowed by schema, should still be blocked)
        step = Step(tool="FileOps", action="nuke", args={}, risk=3)
        
        with pytest.raises(SafetyError):
            check_step(step)

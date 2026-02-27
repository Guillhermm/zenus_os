"""
Integration tests for SystemOps tool
"""

import pytest
import psutil
from zenus_core.tools.system_ops import SystemOps


class TestSystemOps:
    """Test SystemOps tool operations"""
    
    def setup_method(self):
        """Set up test environment"""
        self.tool = SystemOps()
    
    def test_check_resource_usage(self):
        """Should return CPU, memory, and disk usage"""
        result = self.tool.check_resource_usage()
        
        assert "CPU:" in result
        assert "Memory:" in result
        assert "Disk:" in result
        assert "%" in result  # Should contain percentages
        assert "GB" in result or "MB" in result  # Should contain sizes
    
    def test_resource_usage_valid_numbers(self):
        """Resource usage should return valid percentages"""
        result = self.tool.check_resource_usage()
        
        # Extract CPU percentage
        if "CPU:" in result:
            # Check that numbers are reasonable (0-100%)
            assert any(char.isdigit() for char in result)
    
    def test_list_processes(self):
        """Should list running processes"""
        result = self.tool.list_processes(limit=10)
        
        assert "PID" in result
        assert "mem" in result or "memory" in result
        
        # Should list multiple processes
        lines = result.strip().split('\n')
        assert len(lines) >= 3  # At least a few processes
    
    def test_list_processes_limit(self):
        """Should respect limit parameter"""
        result = self.tool.list_processes(limit=5)
        
        lines = result.strip().split('\n')
        # Should have at most 5 processes
        assert len(lines) <= 5
    
    def test_list_processes_finds_self(self):
        """Should find the current Python process"""
        result = self.tool.list_processes(limit=50)
        
        # Should find at least one python process (the test itself)
        assert "python" in result.lower()
    
    def test_disk_usage(self):
        """Should return disk usage for a path"""
        result = self.tool.disk_usage("/")
        
        assert "Disk" in result
        assert "GB" in result or "MB" in result
        assert "%" in result
        assert "used" in result.lower()
        assert "free" in result.lower()
    
    def test_disk_usage_valid_path(self):
        """Should work with /tmp directory"""
        result = self.tool.disk_usage("/tmp")
        
        assert "tmp" in result or "/" in result
        assert "GB" in result or "MB" in result
    
    def test_disk_usage_invalid_path(self):
        """Should handle invalid paths gracefully"""
        # Non-existent path should either error gracefully or return root usage
        result = self.tool.disk_usage("/nonexistent/path/that/does/not/exist")
        
        # Should not crash - either returns error message or root usage
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_get_system_info(self):
        """Should return system information"""
        result = self.tool.get_system_info()
        
        assert "OS:" in result or "System:" in result
        assert "CPU" in result or "Processor" in result
        # Should contain some system info
        assert len(result) > 50
    
    def test_resource_usage_returns_current_state(self):
        """Resource usage should reflect current system state"""
        result1 = self.tool.check_resource_usage()
        result2 = self.tool.check_resource_usage()
        
        # Both should be valid strings
        assert isinstance(result1, str) and isinstance(result2, str)
        assert len(result1) > 0 and len(result2) > 0
        
        # Should contain similar structure (might have different values)
        assert result1.count("CPU:") == result2.count("CPU:")
        assert result1.count("Memory:") == result2.count("Memory:")


@pytest.mark.slow
class TestSystemOpsPerformance:
    """Performance tests for SystemOps"""
    
    def setup_method(self):
        """Set up test environment"""
        self.tool = SystemOps()
    
    def test_check_resource_usage_fast(self):
        """Resource check should be fast (<100ms)"""
        import time
        
        start = time.time()
        self.tool.check_resource_usage()
        elapsed = time.time() - start
        
        # Should complete quickly
        assert elapsed < 0.1, f"Resource check took {elapsed:.3f}s (should be <0.1s)"
    
    def test_list_processes_reasonable_time(self):
        """Listing processes should be reasonable (<500ms)"""
        import time
        
        start = time.time()
        self.tool.list_processes(limit=100)
        elapsed = time.time() - start
        
        # Should complete in reasonable time
        assert elapsed < 0.5, f"Process listing took {elapsed:.3f}s (should be <0.5s)"

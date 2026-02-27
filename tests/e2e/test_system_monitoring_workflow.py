"""
E2E tests for system monitoring workflows
"""

import pytest
import time
from zenus_core.tools.system_ops import SystemOps


@pytest.mark.e2e
class TestSystemMonitoringWorkflows:
    """End-to-end tests for system monitoring workflows"""
    
    def setup_method(self):
        """Set up test environment"""
        self.system_ops = SystemOps()
    
    def test_complete_system_health_check(self):
        """E2E: Complete system health check workflow"""
        # Step 1: Check resource usage
        resources = self.system_ops.check_resource_usage()
        assert "CPU" in resources
        assert "Memory" in resources
        assert "Disk" in resources
        
        # Step 2: List top processes
        processes = self.system_ops.list_processes(limit=10)
        assert "PID" in processes
        assert len(processes.strip().split('\n')) <= 10
        
        # Step 3: Check disk usage for key paths
        disk_root = self.system_ops.disk_usage("/")
        assert "GB" in disk_root or "MB" in disk_root
        
        disk_tmp = self.system_ops.disk_usage("/tmp")
        assert "GB" in disk_tmp or "MB" in disk_tmp
        
        # Step 4: Get system info
        sys_info = self.system_ops.get_system_info()
        assert len(sys_info) > 0
        
        # All checks passed - system health check complete!
        assert True
    
    def test_resource_monitoring_over_time(self):
        """E2E: Monitor resources over short period"""
        samples = []
        
        # Take 3 samples with small delays
        for i in range(3):
            result = self.system_ops.check_resource_usage()
            samples.append(result)
            
            if i < 2:  # Don't sleep after last sample
                time.sleep(0.5)
        
        # All samples should be valid
        assert len(samples) == 3
        for sample in samples:
            assert "CPU" in sample
            assert "Memory" in sample
            assert "Disk" in sample
    
    def test_identify_high_memory_processes(self):
        """E2E: Identify processes using high memory"""
        # Get top 20 processes
        processes = self.system_ops.list_processes(limit=20)
        
        assert "PID" in processes
        assert "mem" in processes.lower() or "memory" in processes.lower()
        
        # Parse process list (basic parsing)
        lines = processes.strip().split('\n')
        
        # Should have found processes
        assert len(lines) >= 1
        
        # Each line should contain PID and percentage
        for line in lines:
            if "PID" in line:
                assert "%" in line
    
    def test_disk_space_analysis(self):
        """E2E: Analyze disk space usage across filesystems"""
        # Check multiple common paths
        paths = ["/", "/tmp", "/home"]
        results = {}
        
        for path in paths:
            try:
                result = self.system_ops.disk_usage(path)
                results[path] = result
            except Exception:
                # Path might not exist, skip
                continue
        
        # Should have checked at least one path
        assert len(results) >= 1
        
        # Each result should contain disk info
        for path, result in results.items():
            assert "GB" in result or "MB" in result
            assert "%" in result


@pytest.mark.e2e
@pytest.mark.slow
class TestSystemMonitoringPerformance:
    """Performance tests for system monitoring workflows"""
    
    def setup_method(self):
        """Set up test environment"""
        self.system_ops = SystemOps()
    
    def test_rapid_health_checks(self):
        """Should handle rapid successive health checks"""
        start = time.time()
        
        # Perform 10 rapid health checks
        for i in range(10):
            self.system_ops.check_resource_usage()
        
        elapsed = time.time() - start
        
        # Should complete in reasonable time (<2s)
        assert elapsed < 2.0, f"10 health checks took {elapsed:.2f}s (should be <2s)"
    
    def test_complete_monitoring_workflow_fast(self):
        """Complete monitoring workflow should be fast"""
        start = time.time()
        
        # Full workflow
        self.system_ops.check_resource_usage()
        self.system_ops.list_processes(limit=10)
        self.system_ops.disk_usage("/")
        self.system_ops.get_system_info()
        
        elapsed = time.time() - start
        
        # Should complete quickly (<1s)
        assert elapsed < 1.0, f"Complete monitoring took {elapsed:.2f}s (should be <1s)"

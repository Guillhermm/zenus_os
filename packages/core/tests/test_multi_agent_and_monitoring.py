"""
Tests for Multi-Agent Collaboration and Proactive Monitoring
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from zenus_core.brain.multi_agent import (
    MultiAgentSystem, AgentRole, Agent, ResearcherAgent,
    PlannerAgent, ExecutorAgent, ValidatorAgent
)
from zenus_core.monitoring.proactive_monitor import (
    ProactiveMonitor, HealthCheck, HealthChecker, Remediator,
    AlertLevel, HealthStatus
)


class TestMultiAgentSystem:
    """Test Multi-Agent Collaboration"""
    
    @pytest.fixture
    def mock_llm(self):
        llm = Mock()
        llm.generate = Mock(return_value='{"analysis": "Test", "approaches": [], "recommended_tools": [], "challenges": [], "best_practices": [], "confidence": 0.8, "reasoning": "Test"}')
        return llm
    
    @pytest.fixture
    def mock_logger(self):
        logger = Mock()
        logger.log_info = Mock()
        logger.log_error = Mock()
        return logger
    
    @pytest.fixture
    def mock_orchestrator(self):
        orch = Mock()
        orch.execute_command = Mock(return_value="Success")
        return orch
    
    @pytest.fixture
    def multi_agent(self, mock_llm, mock_logger, mock_orchestrator):
        return MultiAgentSystem(mock_llm, mock_logger, mock_orchestrator)
    
    def test_system_initialization(self, multi_agent):
        """Test that multi-agent system initializes correctly"""
        assert multi_agent.researcher is not None
        assert multi_agent.planner is not None
        assert multi_agent.executor is not None
        assert multi_agent.validator is not None
        
        assert multi_agent.researcher.role == AgentRole.RESEARCHER
        assert multi_agent.planner.role == AgentRole.PLANNER
        assert multi_agent.executor.role == AgentRole.EXECUTOR
        assert multi_agent.validator.role == AgentRole.VALIDATOR
    
    def test_researcher_agent(self, mock_llm, mock_logger):
        """Test researcher agent execution"""
        agent = ResearcherAgent(mock_llm, mock_logger)
        result = agent.execute("test task", {})
        
        assert result.agent == AgentRole.RESEARCHER
        assert result.success is True
        assert result.confidence > 0
    
    def test_planner_agent(self, mock_llm, mock_logger):
        """Test planner agent execution"""
        mock_llm.generate = Mock(return_value='{"prerequisites": [], "steps": [], "timeline": "1h", "risks": [], "confidence": 0.85, "reasoning": "Test"}')
        
        agent = PlannerAgent(mock_llm, mock_logger)
        result = agent.execute("test task", {"research": {}})
        
        assert result.agent == AgentRole.PLANNER
        assert result.success is True
    
    def test_executor_agent(self, mock_llm, mock_logger, mock_orchestrator):
        """Test executor agent execution"""
        agent = ExecutorAgent(mock_llm, mock_logger, mock_orchestrator)
        
        plan = {
            "steps": [
                {"step_num": 1, "action": "test action", "command": "echo test", "risk": "low"}
            ]
        }
        
        result = agent.execute("test task", {"plan": plan})
        
        assert result.agent == AgentRole.EXECUTOR
        assert mock_orchestrator.execute_command.called
    
    def test_validator_agent(self, mock_llm, mock_logger):
        """Test validator agent execution"""
        mock_llm.generate = Mock(return_value='{"overall_success": true, "checks": [], "issues": [], "recommendations": [], "confidence": 0.9, "reasoning": "Test"}')
        
        agent = ValidatorAgent(mock_llm, mock_logger)
        result = agent.execute("test task", {"plan": {}, "execution": {}})
        
        assert result.agent == AgentRole.VALIDATOR
        assert result.success is True
    
    def test_collaboration_workflow(self, multi_agent):
        """Test full collaboration workflow"""
        session = multi_agent.collaborate("build a REST API", {})
        
        assert session is not None
        assert len(session.agents_involved) > 0
        assert len(session.results) > 0
        assert session.total_duration > 0
        
        # Should involve at least researcher and planner
        assert AgentRole.RESEARCHER in session.agents_involved
        assert AgentRole.PLANNER in session.agents_involved
    
    def test_agent_communication(self, multi_agent):
        """Test inter-agent message passing"""
        from zenus_core.brain.multi_agent import CollaborationSession
        import uuid
        
        session = CollaborationSession(
            session_id=str(uuid.uuid4())[:8],
            task="test",
            agents_involved=[],
            messages=[],
            results=[],
            final_result=None,
            success=False,
            total_duration=0.0
        )
        
        msg = multi_agent.researcher.send_message(
            AgentRole.PLANNER,
            "request",
            {"data": "test"},
            session
        )
        
        assert msg.from_agent == AgentRole.RESEARCHER
        assert msg.to_agent == AgentRole.PLANNER
        assert len(session.messages) == 1


class TestProactiveMonitoring:
    """Test Proactive Monitoring System"""
    
    @pytest.fixture
    def mock_logger(self):
        logger = Mock()
        logger.log_info = Mock()
        logger.log_error = Mock()
        return logger
    
    @pytest.fixture
    def temp_storage(self, tmp_path):
        return tmp_path / "monitoring"
    
    @pytest.fixture
    def monitor(self, mock_logger, temp_storage):
        return ProactiveMonitor(mock_logger, storage_dir=temp_storage)
    
    def test_monitor_initialization(self, monitor):
        """Test monitor initializes with default checks"""
        assert monitor is not None
        assert len(monitor.health_checks) > 0
        
        # Should have disk, memory, and log checks by default
        check_types = [c.check_type for c in monitor.health_checks]
        assert "disk" in check_types
        assert "memory" in check_types
        assert "log" in check_types
    
    def test_health_checker_disk(self, mock_logger):
        """Test disk space checking"""
        checker = HealthChecker(mock_logger)
        
        # This will actually check real disk
        success, details = checker.check_disk_space({"warning": 80, "critical": 90})
        
        assert "usage" in details
        assert isinstance(details["usage"], int)
    
    def test_health_checker_memory(self, mock_logger):
        """Test memory usage checking"""
        checker = HealthChecker(mock_logger)
        
        success, details = checker.check_memory_usage({"warning": 80, "critical": 90})
        
        assert "usage" in details
        assert "used_mb" in details
        assert "total_mb" in details
    
    @patch('subprocess.run')
    def test_health_checker_service(self, mock_run, mock_logger):
        """Test service status checking"""
        checker = HealthChecker(mock_logger)
        
        # Mock successful service check
        mock_run.return_value = Mock(returncode=0, stdout="active\n")
        
        success, details = checker.check_service_status("nginx")
        
        assert success is True
        assert details["service"] == "nginx"
        assert details["status"] == "active"
    
    def test_add_health_check(self, monitor):
        """Test adding custom health check"""
        initial_count = len(monitor.health_checks)
        
        new_check = HealthCheck(
            name="custom_check",
            check_type="disk",
            threshold={"warning": 70, "critical": 85},
            check_interval=600,
            auto_remediate=False,
            remediation_action=None
        )
        
        monitor.add_health_check(new_check)
        
        assert len(monitor.health_checks) == initial_count + 1
        assert any(c.name == "custom_check" for c in monitor.health_checks)
    
    def test_remove_health_check(self, monitor):
        """Test removing health check"""
        # Add a check first
        check = HealthCheck(
            name="temp_check",
            check_type="disk",
            threshold={},
            check_interval=300,
            auto_remediate=False,
            remediation_action=None
        )
        monitor.add_health_check(check)
        
        # Remove it
        monitor.remove_health_check("temp_check")
        
        assert not any(c.name == "temp_check" for c in monitor.health_checks)
    
    def test_start_monitoring_session(self, monitor):
        """Test starting monitoring session"""
        session = monitor.start_monitoring(interval=300)
        
        assert session is not None
        assert session.checks_run == 0
        assert session.alerts_generated == 0
        assert session.status == HealthStatus.HEALTHY
    
    def test_run_checks(self, monitor):
        """Test running health checks"""
        monitor.start_monitoring()
        
        # This will actually run checks
        alerts = monitor.run_checks()
        
        assert isinstance(alerts, list)
        assert monitor.current_session.checks_run > 0
    
    def test_alert_generation(self, monitor):
        """Test alert creation"""
        check = HealthCheck(
            name="test_check",
            check_type="disk",
            threshold={"warning": 1, "critical": 2},  # Super low threshold to trigger alert
            check_interval=1,
            auto_remediate=False,
            remediation_action=None
        )
        
        monitor.add_health_check(check)
        monitor.start_monitoring()
        
        # Run checks - should generate alert due to low threshold
        alerts = monitor.run_checks()
        
        # May or may not generate alert depending on actual disk usage
        # But it should at least complete without error
        assert isinstance(alerts, list)
    
    def test_get_status(self, monitor):
        """Test getting monitor status"""
        monitor.start_monitoring()
        status = monitor.get_status()
        
        assert "session" in status
        assert "health_checks" in status
        assert "checks" in status
        assert isinstance(status["checks"], list)
    
    @patch('subprocess.run')
    def test_remediator(self, mock_run, mock_logger):
        """Test automatic remediation"""
        mock_run.return_value = Mock(returncode=0, stdout="Success")
        
        remediator = Remediator(mock_logger)
        success, message = remediator.remediate(
            "test_check",
            {"issue": "test"},
            "echo 'remediation'"
        )
        
        # Should have attempted remediation
        assert mock_run.called


class TestIntegration:
    """Integration tests for both features"""
    
    def test_both_features_coexist(self, tmp_path):
        """Test that multi-agent and monitoring can coexist"""
        mock_llm = Mock()
        mock_llm.generate = Mock(return_value='{"test": "data", "confidence": 0.8, "reasoning": "test"}')
        
        mock_logger = Mock()
        mock_logger.log_info = Mock()
        mock_logger.log_error = Mock()
        
        mock_orch = Mock()
        mock_orch.execute_command = Mock(return_value="Success")
        
        # Create both systems
        multi_agent = MultiAgentSystem(mock_llm, mock_logger, mock_orch)
        monitor = ProactiveMonitor(mock_logger, mock_orch, storage_dir=tmp_path / "monitoring")
        
        # Both should initialize without conflicts
        assert multi_agent is not None
        assert monitor is not None
        
        # Both should be functional
        monitor.start_monitoring()
        status = monitor.get_status()
        assert status is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

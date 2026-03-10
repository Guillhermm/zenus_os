"""
Tests for Failure Analyzer
"""

import pytest
import tempfile
import os
from zenus_core.brain.failure_analyzer import FailureAnalyzer
from zenus_core.memory.failure_logger import FailureLogger, Failure
from zenus_core.brain.llm.schemas import IntentIR, Step


@pytest.fixture
def temp_db():
    """Create temporary database for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_failures.db")
        yield db_path


@pytest.fixture
def logger(temp_db):
    """Create logger with temp database"""
    return FailureLogger(db_path=temp_db)


@pytest.fixture
def analyzer(logger):
    """Create analyzer with test logger"""
    analyzer = FailureAnalyzer()
    analyzer.logger = logger
    return analyzer


def test_categorize_permission_error(analyzer):
    """Test error categorization for permission errors"""
    error_type = analyzer._categorize_error("Permission denied: /root/file.txt")
    assert error_type == "permission_denied"
    
    error_type = analyzer._categorize_error("Access denied to resource")
    assert error_type == "permission_denied"


def test_categorize_file_not_found(analyzer):
    """Test error categorization for file not found"""
    error_type = analyzer._categorize_error("No such file or directory")
    assert error_type == "file_not_found"
    
    error_type = analyzer._categorize_error("File does not exist")
    assert error_type == "file_not_found"


def test_categorize_network_error(analyzer):
    """Test error categorization for network errors"""
    error_type = analyzer._categorize_error("Connection refused")
    assert error_type == "network_error"
    
    error_type = analyzer._categorize_error("Network unreachable")
    assert error_type == "network_error"


def test_categorize_unknown_error(analyzer):
    """Test unknown error categorization"""
    error_type = analyzer._categorize_error("Some weird error message")
    assert error_type == "unknown"


def test_generate_suggestions_permission(analyzer):
    """Test suggestion generation for permission errors"""
    suggestions = analyzer._generate_suggestions(
        error_type="permission_denied",
        error_message="Permission denied",
        tool="FileOps"
    )
    
    assert len(suggestions) > 0
    assert any("sudo" in s.lower() for s in suggestions)


def test_generate_suggestions_file_not_found(analyzer):
    """Test suggestion generation for file not found"""
    suggestions = analyzer._generate_suggestions(
        error_type="file_not_found",
        error_message="No such file",
        tool="FileOps"
    )
    
    assert len(suggestions) > 0
    assert any("path" in s.lower() for s in suggestions)


def test_analyze_failure_logs_to_database(analyzer):
    """Test that analyze_failure logs to database"""
    analysis = analyzer.analyze_failure(
        user_input="read /root/secret.txt",
        intent_goal="Read secret file",
        tool="FileOps",
        error_message="Permission denied: /root/secret.txt",
        context={"cwd": "/home/user"}
    )
    
    assert analysis["failure_id"] > 0
    assert analysis["error_type"] == "permission_denied"
    assert len(analysis["suggestions"]) > 0


def test_analyze_before_execution_no_history(analyzer):
    """Test pre-execution analysis with no failure history"""
    intent = IntentIR(
        goal="Read file",
        requires_confirmation=False,
        steps=[Step(tool="FileOps", action="read_file", args={"path": "test.txt"}, risk=0)]
    )
    
    analysis = analyzer.analyze_before_execution("read test.txt", intent)
    
    assert not analysis["has_warnings"]
    assert analysis["success_probability"] >= 0.9


def test_analyze_before_execution_with_history(analyzer):
    """Test pre-execution analysis with failure history"""
    # Log some past failures
    for i in range(3):
        analyzer.logger.log_failure(
            user_input="npm install",
            intent_goal="Install packages",
            tool="PackageOps",
            error_type="network_error",
            error_message="ECONNREFUSED",
            context={}
        )
    
    # Analyze new similar command
    intent = IntentIR(
        goal="Install packages",
        requires_confirmation=False,
        steps=[Step(tool="PackageOps", action="install", args={"package": "react"}, risk=1)]
    )
    
    analysis = analyzer.analyze_before_execution("npm install react", intent)
    
    assert analysis["has_warnings"]
    assert analysis["success_probability"] < 0.9
    assert len(analysis["warnings"]) > 0


def test_get_success_probability_no_failures(analyzer):
    """Test success probability with no failures"""
    prob, confidence = analyzer.get_success_probability("git push", "GitOps")
    
    assert prob >= 0.9
    assert confidence == "high"


def test_get_success_probability_some_failures(analyzer):
    """Test success probability with some failures"""
    # Log failures
    for i in range(2):
        analyzer.logger.log_failure(
            user_input="git push",
            intent_goal="Push changes",
            tool="GitOps",
            error_type="network_error",
            error_message="Connection failed",
            context={}
        )
    
    prob, confidence = analyzer.get_success_probability("git push origin main", "GitOps")
    
    assert prob < 0.9
    assert confidence in ["medium", "low"]


def test_get_success_probability_many_failures(analyzer):
    """Test success probability with many failures"""
    # Log many failures
    for i in range(6):
        analyzer.logger.log_failure(
            user_input="docker run",
            intent_goal="Run container",
            tool="ContainerOps",
            error_type="permission_denied",
            error_message="Permission denied",
            context={}
        )
    
    prob, confidence = analyzer.get_success_probability("docker run nginx", "ContainerOps")
    
    assert prob <= 0.5
    assert confidence == "low"


def test_should_retry_permission_error(analyzer):
    """Test retry decision for permission errors"""
    failure = Failure(
        timestamp="2024-01-01T10:00:00",
        user_input="read /root/file.txt",
        intent_goal="Read file",
        tool="FileOps",
        error_type="permission_denied",
        error_message="Permission denied",
        context={}
    )
    
    should_retry, reason = analyzer.should_retry(failure, attempt_count=1)
    
    assert not should_retry
    assert "manual intervention" in reason.lower()


def test_should_retry_network_error(analyzer):
    """Test retry decision for network errors"""
    failure = Failure(
        timestamp="2024-01-01T10:00:00",
        user_input="curl https://api.example.com",
        intent_goal="Fetch data",
        tool="NetworkOps",
        error_type="network_error",
        error_message="Connection refused",
        context={}
    )
    
    # First attempt should retry
    should_retry, reason = analyzer.should_retry(failure, attempt_count=1)
    assert should_retry
    assert "transient" in reason.lower()
    
    # Too many attempts should not retry
    should_retry, reason = analyzer.should_retry(failure, attempt_count=4)
    assert not should_retry


def test_should_retry_unknown_error_once(analyzer):
    """Test retry decision for unknown errors"""
    failure = Failure(
        timestamp="2024-01-01T10:00:00",
        user_input="some command",
        intent_goal="Do something",
        tool="FileOps",
        error_type="unknown",
        error_message="Weird error",
        context={}
    )
    
    # First attempt should retry
    should_retry, reason = analyzer.should_retry(failure, attempt_count=1)
    assert should_retry
    
    # Second attempt should not retry
    should_retry, reason = analyzer.should_retry(failure, attempt_count=2)
    assert not should_retry


def test_generate_recovery_plan_permission(analyzer):
    """Test recovery plan generation for permission errors"""
    failure = Failure(
        timestamp="2024-01-01T10:00:00",
        user_input="read /root/file.txt",
        intent_goal="Read file",
        tool="FileOps",
        error_type="permission_denied",
        error_message="Permission denied",
        context={}
    )
    
    plan = analyzer.generate_recovery_plan(failure)
    
    assert plan is not None
    assert "permission" in plan.lower()
    assert any(word in plan.lower() for word in ["chmod", "chown", "sudo"])


def test_generate_recovery_plan_file_not_found(analyzer):
    """Test recovery plan generation for file not found"""
    failure = Failure(
        timestamp="2024-01-01T10:00:00",
        user_input="read missing.txt",
        intent_goal="Read file",
        tool="FileOps",
        error_type="file_not_found",
        error_message="No such file",
        context={}
    )
    
    plan = analyzer.generate_recovery_plan(failure)
    
    assert plan is not None
    assert any(word in plan.lower() for word in ["path", "find", "verify"])


def test_tool_specific_suggestions_browser(analyzer):
    """Test tool-specific suggestions for BrowserOps"""
    suggestions = analyzer._get_tool_specific_suggestions(
        tool="BrowserOps",
        error_message="Element not found timeout"
    )
    
    assert len(suggestions) > 0
    assert any("timeout" in s.lower() or "webpage" in s.lower() for s in suggestions)


def test_tool_specific_suggestions_package(analyzer):
    """Test tool-specific suggestions for PackageOps"""
    suggestions = analyzer._get_tool_specific_suggestions(
        tool="PackageOps",
        error_message="Package not found"
    )
    
    assert len(suggestions) > 0
    assert any("update" in s.lower() or "apt" in s.lower() for s in suggestions)


def test_recurring_failure_detection(analyzer):
    """Test detection of recurring failures"""
    # Log the same failure twice
    for i in range(2):
        analyzer.logger.log_failure(
            user_input="docker run image",
            intent_goal="Run container",
            tool="ContainerOps",
            error_type="permission_denied",
            error_message="Permission denied",
            context={}
        )
    
    # Analyze new occurrence
    analysis = analyzer.analyze_failure(
        user_input="docker run image",
        intent_goal="Run container",
        tool="ContainerOps",
        error_message="Permission denied",
        context={}
    )
    
    assert analysis["is_recurring"]
    assert len(analysis["similar_failures"]) >= 2

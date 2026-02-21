"""
Tests for error recovery system
"""

import pytest
from zenus_core.execution.error_recovery import (
    ErrorRecovery,
    RecoveryStrategy,
    RecoveryResult
)


def test_error_recovery_initialization():
    """Test error recovery initialization"""
    recovery = ErrorRecovery(max_retries=3)
    assert recovery.max_retries == 3
    assert recovery.backoff_base == 2.0
    assert recovery.recovery_stats["retries"] == 0


def test_recovery_stats():
    """Test recovery statistics tracking"""
    recovery = ErrorRecovery()
    stats = recovery.get_stats()
    
    assert "retries" in stats
    assert "skips" in stats
    assert "aborts" in stats
    assert all(v == 0 for v in stats.values())


def test_handle_missing_dependency():
    """Test handling missing Python module"""
    recovery = ErrorRecovery()
    
    error = ImportError("No module named 'nonexistent_module'")
    context = {"tool": "TestTool", "action": "test"}
    
    result = recovery._handle_missing_dependency(error, context)
    
    assert result.success is True
    assert result.strategy == RecoveryStrategy.SKIP
    assert "nonexistent_module" in result.message or "unknown" in result.message


def test_handle_missing_key():
    """Test handling missing dictionary key"""
    recovery = ErrorRecovery()
    
    error = KeyError("missing_key")
    context = {}
    
    result = recovery._handle_missing_key(error, context)
    
    assert result.success is True
    assert result.strategy == RecoveryStrategy.SKIP

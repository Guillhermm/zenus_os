"""
Tests for Rollback Engine
"""

import pytest
import tempfile
import os
from pathlib import Path
from zenus_core.memory.action_tracker import ActionTracker
from zenus_core.cli.rollback import RollbackEngine, RollbackError


@pytest.fixture
def temp_db():
    """Create temporary database for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_actions.db")
        yield db_path


@pytest.fixture
def tracker(temp_db):
    """Create tracker with temp database"""
    return ActionTracker(db_path=temp_db)


@pytest.fixture
def rollback_engine(tracker):
    """Create rollback engine with test tracker"""
    engine = RollbackEngine()
    engine.tracker = tracker
    return engine


def test_analyze_feasibility_all_rollbackable(tracker, rollback_engine):
    """Test feasibility analysis with all rollbackable actions"""
    tx_id = tracker.start_transaction("test", "test goal")
    
    tracker.track_action("FileOps", "create_file", {"path": "/tmp/a.txt"}, {}, tx_id)
    tracker.track_action("FileOps", "create_file", {"path": "/tmp/b.txt"}, {}, tx_id)
    
    actions = tracker.get_transaction_actions(tx_id)
    feasibility = rollback_engine.analyze_feasibility(actions)
    
    assert feasibility["possible"] is True
    assert feasibility["rollbackable_count"] == 2
    assert feasibility["non_rollbackable_count"] == 0


def test_analyze_feasibility_with_non_rollbackable(tracker, rollback_engine):
    """Test feasibility analysis with non-rollbackable actions"""
    tx_id = tracker.start_transaction("test", "test goal")
    
    tracker.track_action("FileOps", "create_file", {"path": "/tmp/a.txt"}, {}, tx_id)
    tracker.track_action("GitOps", "push", {"remote": "origin"}, {}, tx_id)
    
    actions = tracker.get_transaction_actions(tx_id)
    feasibility = rollback_engine.analyze_feasibility(actions)
    
    assert feasibility["possible"] is False
    assert feasibility["non_rollbackable_count"] == 1
    assert "GitOps.push" in feasibility["non_rollbackable"]


def test_describe_rollback_delete(rollback_engine, tracker):
    """Test rollback description for delete strategy"""
    from memory.action_tracker import Action
    
    action = Action(
        id=1,
        transaction_id="test",
        timestamp="2024-01-01T00:00:00",
        tool="FileOps",
        operation="create_file",
        params={},
        result={},
        rollback_possible=True,
        rollback_strategy="delete",
        rollback_data={"path": "/tmp/test.txt"}
    )
    
    description = rollback_engine._describe_rollback(action)
    assert "Delete" in description
    assert "/tmp/test.txt" in description


def test_describe_rollback_move_back(rollback_engine, tracker):
    """Test rollback description for move_back strategy"""
    from memory.action_tracker import Action
    
    action = Action(
        id=1,
        transaction_id="test",
        timestamp="2024-01-01T00:00:00",
        tool="FileOps",
        operation="move_file",
        params={},
        result={},
        rollback_possible=True,
        rollback_strategy="move_back",
        rollback_data={"from": "/tmp/new.txt", "to": "/tmp/old.txt"}
    )
    
    description = rollback_engine._describe_rollback(action)
    assert "Move" in description
    assert "/tmp/new.txt" in description
    assert "/tmp/old.txt" in description


def test_rollback_file_creation(tracker, rollback_engine):
    """Test rolling back file creation"""
    # Create a temporary file
    test_file = Path(tempfile.gettempdir()) / "rollback_test.txt"
    test_file.write_text("test content")
    
    try:
        # Track the creation
        tx_id = tracker.start_transaction("create file", "Create test file")
        tracker.track_action(
            "FileOps",
            "create_file",
            {"path": str(test_file)},
            {"success": True},
            tx_id
        )
        tracker.end_transaction(tx_id, "completed")
        
        # File should exist
        assert test_file.exists()
        
        # Rollback
        result = rollback_engine.rollback_transaction(tx_id, dry_run=False)
        
        assert result["success"] is True
        assert result["actions_rolled_back"] == 1
        assert not test_file.exists()  # File should be deleted
    
    finally:
        test_file.unlink(missing_ok=True)


def test_rollback_dry_run(tracker, rollback_engine):
    """Test rollback dry run mode"""
    test_file = Path(tempfile.gettempdir()) / "dry_run_test.txt"
    test_file.write_text("test")
    
    try:
        tx_id = tracker.start_transaction("test", "test goal")
        tracker.track_action(
            "FileOps",
            "create_file",
            {"path": str(test_file)},
            {},
            tx_id
        )
        
        result = rollback_engine.rollback_transaction(tx_id, dry_run=True)
        
        assert result["dry_run"] is True
        assert test_file.exists()  # File should still exist
    
    finally:
        test_file.unlink(missing_ok=True)


def test_rollback_with_non_rollbackable_action(tracker, rollback_engine):
    """Test rollback fails with non-rollbackable actions"""
    tx_id = tracker.start_transaction("test", "test goal")
    
    tracker.track_action("GitOps", "push", {"remote": "origin"}, {}, tx_id)
    tracker.end_transaction(tx_id, "completed")
    
    with pytest.raises(RollbackError) as exc_info:
        rollback_engine.rollback_transaction(tx_id, dry_run=False)
    
    assert "Cannot rollback" in str(exc_info.value)


def test_rollback_last_n_actions(tracker, rollback_engine):
    """Test rolling back last N actions"""
    # Create test files
    test_files = [Path(tempfile.gettempdir()) / f"test_{i}.txt" for i in range(3)]
    for f in test_files:
        f.write_text("test")
    
    try:
        # Track actions
        tx_id = tracker.start_transaction("create files", "Create multiple files")
        for f in test_files:
            tracker.track_action(
                "FileOps",
                "create_file",
                {"path": str(f)},
                {},
                tx_id
            )
        tracker.end_transaction(tx_id, "completed")
        
        # All files should exist
        assert all(f.exists() for f in test_files)
        
        # Rollback last 2 actions
        result = rollback_engine.rollback_last_n_actions(2, dry_run=False)
        
        assert result["success"] is True
        assert result["actions_rolled_back"] == 2
        
        # Last 2 files should be deleted
        assert test_files[0].exists()  # First file still exists
        assert not test_files[1].exists()  # Rolled back
        assert not test_files[2].exists()  # Rolled back
    
    finally:
        for f in test_files:
            f.unlink(missing_ok=True)


def test_rollback_empty_transaction(tracker, rollback_engine):
    """Test rollback fails on empty transaction"""
    tx_id = tracker.start_transaction("empty", "Empty transaction")
    tracker.end_transaction(tx_id, "completed")
    
    with pytest.raises(RollbackError) as exc_info:
        rollback_engine.rollback_transaction(tx_id)
    
    assert "No actions found" in str(exc_info.value)


def test_rollback_updates_transaction_status(tracker, rollback_engine):
    """Test that rollback updates transaction rollback status"""
    test_file = Path(tempfile.gettempdir()) / "status_test.txt"
    test_file.write_text("test")
    
    try:
        tx_id = tracker.start_transaction("test", "test goal")
        tracker.track_action(
            "FileOps",
            "create_file",
            {"path": str(test_file)},
            {},
            tx_id
        )
        tracker.end_transaction(tx_id, "completed")
        
        # Rollback
        rollback_engine.rollback_transaction(tx_id, dry_run=False)
        
        # Check transaction status
        transactions = tracker.get_recent_transactions(limit=1)
        assert transactions[0]["rollback_status"] == "completed"
    
    finally:
        test_file.unlink(missing_ok=True)


def test_rollback_marks_actions_as_rolled_back(tracker, rollback_engine):
    """Test that rolled back actions are marked"""
    test_file = Path(tempfile.gettempdir()) / "mark_test.txt"
    test_file.write_text("test")
    
    try:
        tx_id = tracker.start_transaction("test", "test goal")
        action_id = tracker.track_action(
            "FileOps",
            "create_file",
            {"path": str(test_file)},
            {},
            tx_id
        )
        tracker.end_transaction(tx_id, "completed")
        
        # Rollback
        rollback_engine.rollback_transaction(tx_id, dry_run=False)
        
        # Check action is marked as rolled back
        import sqlite3
        conn = sqlite3.connect(tracker.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT rolled_back FROM actions WHERE id = ?", (action_id,))
        result = cursor.fetchone()
        conn.close()
        
        assert result[0] == 1
    
    finally:
        test_file.unlink(missing_ok=True)


def test_rollback_file_move(tracker, rollback_engine):
    """Test rolling back file move operation"""
    # Create source file
    src_file = Path(tempfile.gettempdir()) / "move_src.txt"
    dest_file = Path(tempfile.gettempdir()) / "move_dest.txt"
    
    src_file.write_text("test content")
    
    try:
        # Track move operation
        tx_id = tracker.start_transaction("move file", "Move test file")
        tracker.track_action(
            "FileOps",
            "move_file",
            {"source": str(src_file), "dest": str(dest_file)},
            {"success": True},
            tx_id
        )
        
        # Simulate the move
        src_file.rename(dest_file)
        
        tracker.end_transaction(tx_id, "completed")
        
        # Dest should exist, src should not
        assert dest_file.exists()
        assert not src_file.exists()
        
        # Rollback
        result = rollback_engine.rollback_transaction(tx_id, dry_run=False)
        
        assert result["success"] is True
        assert src_file.exists()  # Moved back
        assert not dest_file.exists()
    
    finally:
        src_file.unlink(missing_ok=True)
        dest_file.unlink(missing_ok=True)


def test_rollback_partial_failure(tracker, rollback_engine):
    """Test rollback with some actions failing"""
    # Create one real file and one fake action
    test_file = Path(tempfile.gettempdir()) / "partial_test.txt"
    test_file.write_text("test")
    
    try:
        tx_id = tracker.start_transaction("test", "test goal")
        
        # Real action
        tracker.track_action(
            "FileOps",
            "create_file",
            {"path": str(test_file)},
            {},
            tx_id
        )
        
        # Action with non-existent file (will fail to rollback)
        tracker.track_action(
            "FileOps",
            "create_file",
            {"path": "/nonexistent/path/file.txt"},
            {},
            tx_id
        )
        
        tracker.end_transaction(tx_id, "completed")
        
        # Rollback - should partially succeed
        result = rollback_engine.rollback_transaction(tx_id, dry_run=False)
        
        # Should have some failures
        assert result["actions_failed"] > 0
        assert len(result["errors"]) > 0
    
    finally:
        test_file.unlink(missing_ok=True)

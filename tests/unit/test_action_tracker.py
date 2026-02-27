"""
Tests for Action Tracker
"""

import pytest
import tempfile
import os
from pathlib import Path
from memory.action_tracker import ActionTracker, Action


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


def test_tracker_initialization(tracker, temp_db):
    """Test tracker creates database and tables"""
    assert os.path.exists(temp_db)
    
    # Verify tables exist
    import sqlite3
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name IN ('actions', 'transactions', 'checkpoints')
    """)
    tables = {row[0] for row in cursor.fetchall()}
    conn.close()
    
    assert 'actions' in tables
    assert 'transactions' in tables
    assert 'checkpoints' in tables


def test_start_transaction(tracker):
    """Test starting a transaction"""
    tx_id = tracker.start_transaction("test command", "test goal")
    
    assert tx_id is not None
    assert len(tx_id) == 12  # MD5 hash truncated to 12 chars
    assert tracker.current_transaction == tx_id


def test_end_transaction(tracker):
    """Test ending a transaction"""
    tx_id = tracker.start_transaction("test", "test goal")
    tracker.end_transaction(tx_id, "completed")
    
    assert tracker.current_transaction is None


def test_track_file_create_action(tracker):
    """Test tracking file creation action"""
    tx_id = tracker.start_transaction("create file", "Create a file")
    
    action_id = tracker.track_action(
        tool="FileOps",
        operation="create_file",
        params={"path": "/tmp/test.txt", "content": "hello"},
        result={"success": True},
        transaction_id=tx_id
    )
    
    assert action_id > 0


def test_file_create_rollback_strategy(tracker):
    """Test rollback strategy for file creation"""
    tx_id = tracker.start_transaction("create file", "Create a file")
    
    tracker.track_action(
        tool="FileOps",
        operation="create_file",
        params={"path": "/tmp/test.txt"},
        result={"success": True},
        transaction_id=tx_id
    )
    
    actions = tracker.get_transaction_actions(tx_id)
    assert len(actions) == 1
    assert actions[0].rollback_possible is True
    assert actions[0].rollback_strategy == "delete"


def test_file_move_rollback_strategy(tracker):
    """Test rollback strategy for file move"""
    tx_id = tracker.start_transaction("move file", "Move a file")
    
    tracker.track_action(
        tool="FileOps",
        operation="move_file",
        params={"source": "/tmp/old.txt", "dest": "/tmp/new.txt"},
        result={"success": True},
        transaction_id=tx_id
    )
    
    actions = tracker.get_transaction_actions(tx_id)
    assert actions[0].rollback_possible is True
    assert actions[0].rollback_strategy == "move_back"
    assert actions[0].rollback_data["from"] == "/tmp/new.txt"
    assert actions[0].rollback_data["to"] == "/tmp/old.txt"


def test_package_install_rollback_strategy(tracker):
    """Test rollback strategy for package installation"""
    tx_id = tracker.start_transaction("install package", "Install package")
    
    tracker.track_action(
        tool="PackageOps",
        operation="install",
        params={"package": "curl"},
        result={"success": True},
        transaction_id=tx_id
    )
    
    actions = tracker.get_transaction_actions(tx_id)
    assert actions[0].rollback_possible is True
    assert actions[0].rollback_strategy == "uninstall"


def test_git_commit_rollback_strategy(tracker):
    """Test rollback strategy for git commit"""
    tx_id = tracker.start_transaction("git commit", "Commit changes")
    
    tracker.track_action(
        tool="GitOps",
        operation="commit",
        params={"message": "test commit"},
        result={"commit_hash": "abc123"},
        transaction_id=tx_id
    )
    
    actions = tracker.get_transaction_actions(tx_id)
    assert actions[0].rollback_possible is True
    assert actions[0].rollback_strategy == "git_reset"


def test_git_push_not_rollbackable(tracker):
    """Test that git push is not rollbackable"""
    tx_id = tracker.start_transaction("git push", "Push changes")
    
    tracker.track_action(
        tool="GitOps",
        operation="push",
        params={"remote": "origin", "branch": "main"},
        result={"success": True},
        transaction_id=tx_id
    )
    
    actions = tracker.get_transaction_actions(tx_id)
    assert actions[0].rollback_possible is False


def test_service_start_rollback_strategy(tracker):
    """Test rollback strategy for service start"""
    tx_id = tracker.start_transaction("start service", "Start nginx")
    
    tracker.track_action(
        tool="ServiceOps",
        operation="start",
        params={"service": "nginx"},
        result={"success": True},
        transaction_id=tx_id
    )
    
    actions = tracker.get_transaction_actions(tx_id)
    assert actions[0].rollback_possible is True
    assert actions[0].rollback_strategy == "stop"


def test_multiple_actions_in_transaction(tracker):
    """Test tracking multiple actions in one transaction"""
    tx_id = tracker.start_transaction("multi-step", "Multiple operations")
    
    tracker.track_action("FileOps", "create_file", {"path": "/tmp/a.txt"}, {"success": True}, tx_id)
    tracker.track_action("FileOps", "create_file", {"path": "/tmp/b.txt"}, {"success": True}, tx_id)
    tracker.track_action("PackageOps", "install", {"package": "curl"}, {"success": True}, tx_id)
    
    actions = tracker.get_transaction_actions(tx_id)
    assert len(actions) == 3
    assert all(a.transaction_id == tx_id for a in actions)


def test_get_recent_transactions(tracker):
    """Test retrieving recent transactions"""
    # Create multiple transactions
    for i in range(3):
        tx_id = tracker.start_transaction(f"test {i}", f"test goal {i}")
        tracker.track_action("FileOps", "create_file", {"path": f"/tmp/test{i}.txt"}, {"success": True}, tx_id)
        tracker.end_transaction(tx_id, "completed")
    
    transactions = tracker.get_recent_transactions(limit=2)
    assert len(transactions) == 2
    assert all(tx["status"] == "completed" for tx in transactions)


def test_create_checkpoint(tracker):
    """Test creating a checkpoint"""
    tx_id = tracker.start_transaction("test", "test goal")
    
    # Create a temporary file to backup
    test_file = Path(tempfile.gettempdir()) / "checkpoint_test.txt"
    test_file.write_text("test content")
    
    try:
        success = tracker.create_checkpoint(
            checkpoint_name="test_checkpoint",
            description="Test checkpoint",
            file_paths=[str(test_file)]
        )
        
        assert success is True
        
        # Verify backup was created
        backup_dir = Path.home() / ".zenus" / "backups" / "test_checkpoint"
        assert backup_dir.exists()
        backup_file = backup_dir / test_file.name
        assert backup_file.exists()
        assert backup_file.read_text() == "test content"
    
    finally:
        test_file.unlink(missing_ok=True)


def test_checkpoint_duplicate_name(tracker):
    """Test that duplicate checkpoint names fail"""
    tx_id = tracker.start_transaction("test", "test goal")
    
    success1 = tracker.create_checkpoint("dup_checkpoint", "First")
    success2 = tracker.create_checkpoint("dup_checkpoint", "Second")
    
    assert success1 is True
    assert success2 is False


def test_mark_rolled_back(tracker):
    """Test marking an action as rolled back"""
    tx_id = tracker.start_transaction("test", "test goal")
    action_id = tracker.track_action(
        "FileOps", "create_file", {"path": "/tmp/test.txt"}, {"success": True}, tx_id
    )
    
    tracker.mark_rolled_back(action_id)
    
    # Verify it's marked
    import sqlite3
    conn = sqlite3.connect(tracker.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT rolled_back FROM actions WHERE id = ?", (action_id,))
    result = cursor.fetchone()
    conn.close()
    
    assert result[0] == 1


def test_container_run_rollback_strategy(tracker):
    """Test rollback strategy for container run"""
    tx_id = tracker.start_transaction("run container", "Run nginx container")
    
    tracker.track_action(
        tool="ContainerOps",
        operation="run",
        params={"image": "nginx"},
        result={"container_id": "abc123"},
        transaction_id=tx_id
    )
    
    actions = tracker.get_transaction_actions(tx_id)
    assert actions[0].rollback_possible is True
    assert actions[0].rollback_strategy == "stop_and_remove"
    assert actions[0].rollback_data["container_id"] == "abc123"

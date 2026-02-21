"""
Action Tracker

Tracks all executed operations for rollback capability.

Responsibilities:
- Log all operations with metadata
- Generate inverse operations
- Support transaction-like operation groups
- Enable safe rollback
"""

import sqlite3
import json
import hashlib
from datetime import datetime
from typing import Optional, Dict, List, Any
from pathlib import Path
from dataclasses import dataclass, asdict
import shutil
import os


@dataclass
class Action:
    """Represents a single tracked action"""
    id: Optional[int]
    transaction_id: str
    timestamp: str
    tool: str
    operation: str
    params: Dict
    result: Any
    rollback_possible: bool
    rollback_strategy: Optional[str]
    rollback_data: Optional[Dict]


class ActionTracker:
    """
    Tracks actions for rollback capability
    
    Features:
    - Transaction grouping
    - Automatic inverse operation generation
    - Checkpoint management
    - Rollback feasibility analysis
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize action tracker
        
        Args:
            db_path: Path to SQLite database (default: ~/.zenus/actions.db)
        """
        if db_path is None:
            db_path = str(Path.home() / ".zenus" / "actions.db")
        
        self.db_path = db_path
        self.current_transaction = None
        self._ensure_db()
        self._ensure_backup_dir()
    
    def _ensure_db(self):
        """Create database and tables if they don't exist"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Actions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                tool TEXT NOT NULL,
                operation TEXT NOT NULL,
                params_json TEXT NOT NULL,
                result_json TEXT,
                rollback_possible BOOLEAN NOT NULL,
                rollback_strategy TEXT,
                rollback_data_json TEXT,
                rolled_back BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Transactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id TEXT PRIMARY KEY,
                start_time TEXT NOT NULL,
                end_time TEXT,
                user_input TEXT NOT NULL,
                intent_goal TEXT NOT NULL,
                status TEXT NOT NULL,
                rollback_status TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Checkpoints table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS checkpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                checkpoint_name TEXT UNIQUE NOT NULL,
                transaction_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                description TEXT,
                backup_paths_json TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Indices
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_actions_transaction 
            ON actions(transaction_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_actions_timestamp 
            ON actions(timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_transactions_status 
            ON transactions(status)
        """)
        
        conn.commit()
        conn.close()
    
    def _ensure_backup_dir(self):
        """Ensure backup directory exists"""
        backup_dir = Path.home() / ".zenus" / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
    
    def start_transaction(self, user_input: str, intent_goal: str) -> str:
        """
        Start a new transaction
        
        Args:
            user_input: Original user command
            intent_goal: Intent goal
        
        Returns:
            Transaction ID
        """
        # Generate transaction ID
        timestamp = datetime.now().isoformat()
        transaction_id = hashlib.md5(f"{timestamp}{user_input}".encode()).hexdigest()[:12]
        
        self.current_transaction = transaction_id
        
        # Record transaction
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO transactions
            (id, start_time, user_input, intent_goal, status)
            VALUES (?, ?, ?, ?, ?)
        """, (transaction_id, timestamp, user_input, intent_goal, "in_progress"))
        
        conn.commit()
        conn.close()
        
        return transaction_id
    
    def end_transaction(self, transaction_id: str, status: str = "completed"):
        """
        End a transaction
        
        Args:
            transaction_id: Transaction ID
            status: Final status (completed, failed, cancelled)
        """
        timestamp = datetime.now().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE transactions
            SET end_time = ?, status = ?
            WHERE id = ?
        """, (timestamp, status, transaction_id))
        
        conn.commit()
        conn.close()
        
        if transaction_id == self.current_transaction:
            self.current_transaction = None
    
    def track_action(
        self,
        tool: str,
        operation: str,
        params: Dict,
        result: Any,
        transaction_id: Optional[str] = None
    ) -> int:
        """
        Track an executed action
        
        Args:
            tool: Tool used
            operation: Operation performed
            params: Operation parameters
            result: Operation result
            transaction_id: Transaction ID (uses current if None)
        
        Returns:
            Action ID
        """
        if transaction_id is None:
            transaction_id = self.current_transaction or "standalone"
        
        timestamp = datetime.now().isoformat()
        
        # Determine rollback strategy
        rollback_info = self._determine_rollback_strategy(tool, operation, params, result)
        
        # Store action
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO actions
            (transaction_id, timestamp, tool, operation, params_json,
             result_json, rollback_possible, rollback_strategy, rollback_data_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            transaction_id,
            timestamp,
            tool,
            operation,
            json.dumps(params),
            json.dumps(result),
            rollback_info["possible"],
            rollback_info["strategy"],
            json.dumps(rollback_info["data"]) if rollback_info["data"] else None
        ))
        
        action_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return action_id
    
    def _determine_rollback_strategy(
        self,
        tool: str,
        operation: str,
        params: Dict,
        result: Any
    ) -> Dict:
        """
        Determine if and how an action can be rolled back
        
        Returns:
            Dictionary with rollback information
        """
        rollback_info = {
            "possible": False,
            "strategy": None,
            "data": None
        }
        
        # FileOps rollback strategies
        if tool == "FileOps":
            if operation == "create_file":
                rollback_info = {
                    "possible": True,
                    "strategy": "delete",
                    "data": {"path": params.get("path")}
                }
            
            elif operation == "delete_file":
                # Can restore from backup if we made one
                rollback_info = {
                    "possible": False,  # Would need pre-deletion backup
                    "strategy": "restore",
                    "data": None
                }
            
            elif operation == "write_file":
                # Could restore previous content if we backed it up
                rollback_info = {
                    "possible": False,  # Would need pre-write backup
                    "strategy": "restore_content",
                    "data": None
                }
            
            elif operation == "move_file":
                rollback_info = {
                    "possible": True,
                    "strategy": "move_back",
                    "data": {
                        "from": params.get("dest"),
                        "to": params.get("source")
                    }
                }
            
            elif operation == "copy_file":
                rollback_info = {
                    "possible": True,
                    "strategy": "delete_copy",
                    "data": {"path": params.get("dest")}
                }
        
        # PackageOps rollback strategies
        elif tool == "PackageOps":
            if operation == "install":
                rollback_info = {
                    "possible": True,
                    "strategy": "uninstall",
                    "data": {"package": params.get("package")}
                }
            
            elif operation == "uninstall":
                rollback_info = {
                    "possible": True,
                    "strategy": "reinstall",
                    "data": {"package": params.get("package")}
                }
        
        # GitOps rollback strategies
        elif tool == "GitOps":
            if operation == "commit":
                rollback_info = {
                    "possible": True,
                    "strategy": "git_reset",
                    "data": {"commit": result.get("commit_hash") if isinstance(result, dict) else None}
                }
            
            elif operation == "push":
                rollback_info = {
                    "possible": False,  # Dangerous to revert pushed commits
                    "strategy": "requires_manual",
                    "data": None
                }
        
        # ServiceOps rollback strategies
        elif tool == "ServiceOps":
            if operation == "start":
                rollback_info = {
                    "possible": True,
                    "strategy": "stop",
                    "data": {"service": params.get("service")}
                }
            
            elif operation == "stop":
                rollback_info = {
                    "possible": True,
                    "strategy": "start",
                    "data": {"service": params.get("service")}
                }
        
        # ContainerOps rollback strategies
        elif tool == "ContainerOps":
            if operation == "run":
                rollback_info = {
                    "possible": True,
                    "strategy": "stop_and_remove",
                    "data": {"container_id": result.get("container_id") if isinstance(result, dict) else None}
                }
        
        return rollback_info
    
    def create_checkpoint(
        self,
        checkpoint_name: str,
        description: str,
        file_paths: Optional[List[str]] = None
    ) -> bool:
        """
        Create a checkpoint (backup critical files)
        
        Args:
            checkpoint_name: Unique checkpoint name
            description: Checkpoint description
            file_paths: Files to backup
        
        Returns:
            Success status
        """
        if not self.current_transaction:
            return False
        
        timestamp = datetime.now().isoformat()
        backup_paths = {}
        
        # Backup specified files
        if file_paths:
            backup_dir = Path.home() / ".zenus" / "backups" / checkpoint_name
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            for file_path in file_paths:
                if os.path.exists(file_path):
                    try:
                        backup_path = backup_dir / Path(file_path).name
                        shutil.copy2(file_path, backup_path)
                        backup_paths[file_path] = str(backup_path)
                    except Exception as e:
                        print(f"Warning: Failed to backup {file_path}: {e}")
        
        # Store checkpoint
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO checkpoints
                (checkpoint_name, transaction_id, timestamp, description, backup_paths_json)
                VALUES (?, ?, ?, ?, ?)
            """, (
                checkpoint_name,
                self.current_transaction,
                timestamp,
                description,
                json.dumps(backup_paths)
            ))
            
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Checkpoint already exists
            return False
        finally:
            conn.close()
    
    def get_transaction_actions(self, transaction_id: str) -> List[Action]:
        """
        Get all actions in a transaction
        
        Args:
            transaction_id: Transaction ID
        
        Returns:
            List of actions
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, transaction_id, timestamp, tool, operation,
                   params_json, result_json, rollback_possible,
                   rollback_strategy, rollback_data_json
            FROM actions
            WHERE transaction_id = ?
            ORDER BY id
        """, (transaction_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        actions = []
        for row in results:
            actions.append(Action(
                id=row[0],
                transaction_id=row[1],
                timestamp=row[2],
                tool=row[3],
                operation=row[4],
                params=json.loads(row[5]),
                result=json.loads(row[6]) if row[6] else None,
                rollback_possible=bool(row[7]),
                rollback_strategy=row[8],
                rollback_data=json.loads(row[9]) if row[9] else None
            ))
        
        return actions
    
    def get_recent_transactions(self, limit: int = 10) -> List[Dict]:
        """
        Get recent transactions
        
        Args:
            limit: Maximum number to return
        
        Returns:
            List of transaction dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, start_time, end_time, user_input, intent_goal, status, rollback_status
            FROM transactions
            ORDER BY start_time DESC
            LIMIT ?
        """, (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        transactions = []
        for row in results:
            transactions.append({
                "id": row[0],
                "start_time": row[1],
                "end_time": row[2],
                "user_input": row[3],
                "intent_goal": row[4],
                "status": row[5],
                "rollback_status": row[6]
            })
        
        return transactions
    
    def mark_rolled_back(self, action_id: int):
        """Mark an action as rolled back"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE actions
            SET rolled_back = 1
            WHERE id = ?
        """, (action_id,))
        
        conn.commit()
        conn.close()


# Global instance
_action_tracker = None


def get_action_tracker() -> ActionTracker:
    """Get global action tracker instance"""
    global _action_tracker
    if _action_tracker is None:
        _action_tracker = ActionTracker()
    return _action_tracker

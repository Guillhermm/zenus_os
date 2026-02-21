"""
Rollback Engine

Executes inverse operations to undo actions.

Capabilities:
- Full transaction rollback
- Partial rollback (last N steps)
- Checkpoint restoration
- Safety validation
"""

from typing import List, Optional, Dict, Tuple
from memory.action_tracker import get_action_tracker, Action
from zenus_core.cli.formatter import console, print_error, print_success
import os
import shutil
import subprocess
import json
from pathlib import Path


class RollbackError(Exception):
    """Raised when rollback fails"""
    pass


class RollbackEngine:
    """
    Executes rollback operations
    
    Features:
    - Transaction rollback
    - Step-by-step rollback
    - Checkpoint restoration
    - Dry-run mode
    - Safety checks
    """
    
    def __init__(self):
        self.tracker = get_action_tracker()
    
    def rollback_transaction(
        self,
        transaction_id: str,
        dry_run: bool = False
    ) -> Dict:
        """
        Rollback an entire transaction
        
        Args:
            transaction_id: Transaction ID to rollback
            dry_run: If True, show what would be done without doing it
        
        Returns:
            Result dictionary with success/failure details
        """
        # Get all actions in transaction
        actions = self.tracker.get_transaction_actions(transaction_id)
        
        if not actions:
            raise RollbackError(f"No actions found for transaction {transaction_id}")
        
        # Analyze rollback feasibility
        feasibility = self.analyze_feasibility(actions)
        
        if not feasibility["possible"]:
            raise RollbackError(
                f"Cannot rollback transaction: {feasibility['reason']}\n"
                f"Non-rollbackable actions: {feasibility['non_rollbackable']}"
            )
        
        # Show what will be rolled back
        console.print(f"\n[yellow]Rolling back transaction: {transaction_id}[/yellow]")
        console.print(f"  Total actions: {len(actions)}")
        console.print(f"  Rollbackable: {feasibility['rollbackable_count']}")
        
        if dry_run:
            console.print("\n[cyan]Dry run - showing rollback plan:[/cyan]")
            for action in reversed(actions):
                if action.rollback_possible:
                    console.print(f"  • {self._describe_rollback(action)}")
            return {"success": True, "dry_run": True, "actions_count": len(actions)}
        
        # Execute rollback (reverse order)
        results = {
            "success": True,
            "actions_rolled_back": 0,
            "actions_failed": 0,
            "errors": []
        }
        
        for action in reversed(actions):
            if not action.rollback_possible:
                continue
            
            try:
                console.print(f"  Rolling back: {action.tool}.{action.operation}")
                self._execute_rollback(action)
                self.tracker.mark_rolled_back(action.id)
                results["actions_rolled_back"] += 1
            except Exception as e:
                error_msg = f"Failed to rollback action {action.id}: {str(e)}"
                console.print(f"  [red]✗ {error_msg}[/red]")
                results["errors"].append(error_msg)
                results["actions_failed"] += 1
                results["success"] = False
        
        # Update transaction rollback status
        if results["success"]:
            self._update_transaction_rollback_status(transaction_id, "completed")
        else:
            self._update_transaction_rollback_status(transaction_id, "partial")
        
        return results
    
    def rollback_last_n_actions(
        self,
        n: int = 1,
        dry_run: bool = False
    ) -> Dict:
        """
        Rollback the last N actions
        
        Args:
            n: Number of actions to rollback
            dry_run: If True, show plan without executing
        
        Returns:
            Result dictionary
        """
        # Get recent transactions
        recent_transactions = self.tracker.get_recent_transactions(limit=1)
        
        if not recent_transactions:
            raise RollbackError("No recent transactions found")
        
        last_transaction = recent_transactions[0]
        actions = self.tracker.get_transaction_actions(last_transaction["id"])
        
        if len(actions) < n:
            console.print(f"[yellow]Warning: Only {len(actions)} actions available, rolling back all[/yellow]")
            n = len(actions)
        
        # Take last N actions
        actions_to_rollback = actions[-n:]
        
        console.print(f"\n[yellow]Rolling back last {n} action(s)[/yellow]")
        
        if dry_run:
            console.print("\n[cyan]Dry run - showing rollback plan:[/cyan]")
            for action in reversed(actions_to_rollback):
                if action.rollback_possible:
                    console.print(f"  • {self._describe_rollback(action)}")
                else:
                    console.print(f"  • [red]Cannot rollback: {action.tool}.{action.operation}[/red]")
            return {"success": True, "dry_run": True, "actions_count": len(actions_to_rollback)}
        
        # Execute rollback
        results = {
            "success": True,
            "actions_rolled_back": 0,
            "actions_failed": 0,
            "errors": []
        }
        
        for action in reversed(actions_to_rollback):
            if not action.rollback_possible:
                console.print(f"  [yellow]Skipping non-rollbackable: {action.tool}.{action.operation}[/yellow]")
                continue
            
            try:
                console.print(f"  Rolling back: {action.tool}.{action.operation}")
                self._execute_rollback(action)
                self.tracker.mark_rolled_back(action.id)
                results["actions_rolled_back"] += 1
            except Exception as e:
                error_msg = f"Failed to rollback action {action.id}: {str(e)}"
                console.print(f"  [red]✗ {error_msg}[/red]")
                results["errors"].append(error_msg)
                results["actions_failed"] += 1
                results["success"] = False
        
        return results
    
    def analyze_feasibility(self, actions: List[Action]) -> Dict:
        """
        Analyze if actions can be rolled back
        
        Args:
            actions: List of actions
        
        Returns:
            Feasibility analysis
        """
        rollbackable = []
        non_rollbackable = []
        
        for action in actions:
            if action.rollback_possible and not self._is_action_rolled_back(action):
                rollbackable.append(action)
            else:
                non_rollbackable.append(action)
        
        # Can rollback if all actions are rollbackable or already rolled back
        can_rollback = len(non_rollbackable) == 0 or all(
            self._is_action_rolled_back(a) for a in non_rollbackable
        )
        
        reason = None
        if not can_rollback:
            reasons = []
            for action in non_rollbackable:
                if not self._is_action_rolled_back(action):
                    reasons.append(f"{action.tool}.{action.operation}")
            reason = "The following actions cannot be rolled back: " + ", ".join(reasons)
        
        return {
            "possible": can_rollback,
            "rollbackable_count": len(rollbackable),
            "non_rollbackable_count": len([a for a in non_rollbackable if not self._is_action_rolled_back(a)]),
            "non_rollbackable": [f"{a.tool}.{a.operation}" for a in non_rollbackable if not self._is_action_rolled_back(a)],
            "reason": reason
        }
    
    def _execute_rollback(self, action: Action):
        """
        Execute rollback for a single action
        
        Args:
            action: Action to rollback
        
        Raises:
            RollbackError: If rollback fails
        """
        if not action.rollback_strategy:
            raise RollbackError(f"No rollback strategy for {action.tool}.{action.operation}")
        
        strategy = action.rollback_strategy
        data = action.rollback_data or {}
        
        try:
            if strategy == "delete":
                # Delete a created file
                path = data.get("path")
                if path and os.path.exists(path):
                    if os.path.isfile(path):
                        os.remove(path)
                    elif os.path.isdir(path):
                        shutil.rmtree(path)
            
            elif strategy == "delete_copy":
                # Delete a copied file
                path = data.get("path")
                if path and os.path.exists(path):
                    os.remove(path)
            
            elif strategy == "move_back":
                # Move file back to original location
                from_path = data.get("from")
                to_path = data.get("to")
                if from_path and to_path and os.path.exists(from_path):
                    shutil.move(from_path, to_path)
            
            elif strategy == "restore":
                # Restore from backup
                # Would need checkpoint data
                raise RollbackError("Restore requires checkpoint - not available")
            
            elif strategy == "restore_content":
                # Restore file content from backup
                raise RollbackError("Content restore requires checkpoint - not available")
            
            elif strategy == "uninstall":
                # Uninstall a package
                package = data.get("package")
                if package:
                    self._execute_package_op("uninstall", package)
            
            elif strategy == "reinstall":
                # Reinstall a package
                package = data.get("package")
                if package:
                    self._execute_package_op("install", package)
            
            elif strategy == "git_reset":
                # Reset to previous commit
                commit = data.get("commit")
                if commit:
                    subprocess.run(["git", "reset", "--hard", f"{commit}^"], check=True)
            
            elif strategy == "stop":
                # Stop a service
                service = data.get("service")
                if service:
                    subprocess.run(["systemctl", "stop", service], check=True)
            
            elif strategy == "start":
                # Start a service
                service = data.get("service")
                if service:
                    subprocess.run(["systemctl", "start", service], check=True)
            
            elif strategy == "stop_and_remove":
                # Stop and remove container
                container_id = data.get("container_id")
                if container_id:
                    subprocess.run(["docker", "stop", container_id], check=True)
                    subprocess.run(["docker", "rm", container_id], check=True)
            
            elif strategy == "requires_manual":
                raise RollbackError("This action requires manual rollback")
            
            else:
                raise RollbackError(f"Unknown rollback strategy: {strategy}")
        
        except subprocess.CalledProcessError as e:
            raise RollbackError(f"Command failed: {e}")
        except Exception as e:
            raise RollbackError(str(e))
    
    def _execute_package_op(self, operation: str, package: str):
        """Execute package operation (install/uninstall)"""
        # Detect package manager
        if shutil.which("apt"):
            if operation == "install":
                subprocess.run(["sudo", "apt", "install", "-y", package], check=True)
            else:
                subprocess.run(["sudo", "apt", "remove", "-y", package], check=True)
        elif shutil.which("dnf"):
            if operation == "install":
                subprocess.run(["sudo", "dnf", "install", "-y", package], check=True)
            else:
                subprocess.run(["sudo", "dnf", "remove", "-y", package], check=True)
        elif shutil.which("pacman"):
            if operation == "install":
                subprocess.run(["sudo", "pacman", "-S", "--noconfirm", package], check=True)
            else:
                subprocess.run(["sudo", "pacman", "-R", "--noconfirm", package], check=True)
        else:
            raise RollbackError("No supported package manager found")
    
    def _describe_rollback(self, action: Action) -> str:
        """Generate human-readable rollback description"""
        strategy = action.rollback_strategy
        data = action.rollback_data or {}
        
        descriptions = {
            "delete": f"Delete {data.get('path')}",
            "delete_copy": f"Delete copied file {data.get('path')}",
            "move_back": f"Move {data.get('from')} back to {data.get('to')}",
            "uninstall": f"Uninstall package {data.get('package')}",
            "reinstall": f"Reinstall package {data.get('package')}",
            "git_reset": f"Reset git commit {data.get('commit')}",
            "stop": f"Stop service {data.get('service')}",
            "start": f"Start service {data.get('service')}",
            "stop_and_remove": f"Stop and remove container {data.get('container_id')}"
        }
        
        return descriptions.get(strategy, f"Rollback {action.tool}.{action.operation}")
    
    def _is_action_rolled_back(self, action: Action) -> bool:
        """Check if action has already been rolled back"""
        import sqlite3
        
        conn = sqlite3.connect(self.tracker.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT rolled_back FROM actions WHERE id = ?", (action.id,))
        result = cursor.fetchone()
        conn.close()
        
        return bool(result[0]) if result else False
    
    def _update_transaction_rollback_status(self, transaction_id: str, status: str):
        """Update transaction rollback status"""
        import sqlite3
        
        conn = sqlite3.connect(self.tracker.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE transactions
            SET rollback_status = ?
            WHERE id = ?
        """, (status, transaction_id))
        
        conn.commit()
        conn.close()
    
    def restore_checkpoint(
        self,
        checkpoint_name: str,
        dry_run: bool = False
    ) -> Dict:
        """
        Restore from a checkpoint
        
        Args:
            checkpoint_name: Checkpoint to restore
            dry_run: If True, show plan without executing
        
        Returns:
            Result dictionary
        """
        import sqlite3
        
        # Get checkpoint
        conn = sqlite3.connect(self.tracker.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT transaction_id, backup_paths_json, description
            FROM checkpoints
            WHERE checkpoint_name = ?
        """, (checkpoint_name,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            raise RollbackError(f"Checkpoint '{checkpoint_name}' not found")
        
        transaction_id, backup_paths_json, description = result
        backup_paths = json.loads(backup_paths_json) if backup_paths_json else {}
        
        console.print(f"\n[yellow]Restoring checkpoint: {checkpoint_name}[/yellow]")
        console.print(f"  Description: {description}")
        console.print(f"  Files to restore: {len(backup_paths)}")
        
        if dry_run:
            console.print("\n[cyan]Dry run - files that would be restored:[/cyan]")
            for original_path, backup_path in backup_paths.items():
                console.print(f"  • {original_path}")
            return {"success": True, "dry_run": True, "files_count": len(backup_paths)}
        
        # Restore files
        results = {
            "success": True,
            "files_restored": 0,
            "files_failed": 0,
            "errors": []
        }
        
        for original_path, backup_path in backup_paths.items():
            try:
                if os.path.exists(backup_path):
                    console.print(f"  Restoring: {original_path}")
                    shutil.copy2(backup_path, original_path)
                    results["files_restored"] += 1
                else:
                    error_msg = f"Backup file not found: {backup_path}"
                    console.print(f"  [yellow]Warning: {error_msg}[/yellow]")
                    results["errors"].append(error_msg)
            except Exception as e:
                error_msg = f"Failed to restore {original_path}: {str(e)}"
                console.print(f"  [red]✗ {error_msg}[/red]")
                results["errors"].append(error_msg)
                results["files_failed"] += 1
                results["success"] = False
        
        return results


# Global instance
_rollback_engine = None


def get_rollback_engine() -> RollbackEngine:
    """Get global rollback engine instance"""
    global _rollback_engine
    if _rollback_engine is None:
        _rollback_engine = RollbackEngine()
    return _rollback_engine

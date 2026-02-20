"""
Failure Logger

Records execution failures for learning and pattern analysis.

Database Schema:
- failures: id, timestamp, user_input, intent_goal, tool, error_type, error_message, context_json, resolution
- failure_patterns: pattern_hash, count, last_seen, suggested_fix
"""

import sqlite3
import json
import hashlib
from datetime import datetime
from typing import Optional, Dict, List
from pathlib import Path
from dataclasses import dataclass, asdict


@dataclass
class Failure:
    """Represents a single execution failure"""
    timestamp: str
    user_input: str
    intent_goal: str
    tool: str
    error_type: str
    error_message: str
    context: Dict
    resolution: Optional[str] = None
    id: Optional[int] = None


class FailureLogger:
    """
    Persistent failure logging and retrieval
    
    Stores failures in SQLite for:
    - Pattern analysis
    - Learning from mistakes
    - Suggesting fixes
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize failure logger
        
        Args:
            db_path: Path to SQLite database (default: ~/.zenus/failures.db)
        """
        if db_path is None:
            db_path = str(Path.home() / ".zenus" / "failures.db")
        
        self.db_path = db_path
        self._ensure_db()
    
    def _ensure_db(self):
        """Create database and tables if they don't exist"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Failures table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS failures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_input TEXT NOT NULL,
                intent_goal TEXT NOT NULL,
                tool TEXT NOT NULL,
                error_type TEXT NOT NULL,
                error_message TEXT NOT NULL,
                context_json TEXT,
                resolution TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Failure patterns table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS failure_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_hash TEXT UNIQUE NOT NULL,
                pattern_description TEXT,
                count INTEGER DEFAULT 1,
                last_seen TEXT NOT NULL,
                suggested_fix TEXT,
                success_after_fix INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Indices for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_failures_timestamp 
            ON failures(timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_failures_tool 
            ON failures(tool)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_failures_error_type 
            ON failures(error_type)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_patterns_hash 
            ON failure_patterns(pattern_hash)
        """)
        
        conn.commit()
        conn.close()
    
    def log_failure(
        self,
        user_input: str,
        intent_goal: str,
        tool: str,
        error_type: str,
        error_message: str,
        context: Optional[Dict] = None,
        resolution: Optional[str] = None
    ) -> int:
        """
        Log a failure
        
        Args:
            user_input: Original user command
            intent_goal: Translated intent goal
            tool: Tool that failed
            error_type: Category of error (syntax, permission, network, etc.)
            error_message: Actual error message
            context: Additional context (directory, git status, etc.)
            resolution: How the failure was resolved (if known)
        
        Returns:
            Failure ID
        """
        timestamp = datetime.now().isoformat()
        context_json = json.dumps(context or {})
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO failures 
            (timestamp, user_input, intent_goal, tool, error_type, 
             error_message, context_json, resolution)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp, user_input, intent_goal, tool, error_type,
            error_message, context_json, resolution
        ))
        
        failure_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Update pattern tracking
        self._update_pattern(user_input, tool, error_type, error_message)
        
        return failure_id
    
    def _update_pattern(
        self,
        user_input: str,
        tool: str,
        error_type: str,
        error_message: str
    ):
        """Update failure pattern tracking"""
        
        # Generate pattern hash (normalize for pattern matching)
        pattern_str = f"{tool}:{error_type}:{self._normalize_error(error_message)}"
        pattern_hash = hashlib.md5(pattern_str.encode()).hexdigest()
        
        timestamp = datetime.now().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if pattern exists
        cursor.execute(
            "SELECT id, count FROM failure_patterns WHERE pattern_hash = ?",
            (pattern_hash,)
        )
        result = cursor.fetchone()
        
        if result:
            # Update existing pattern
            cursor.execute("""
                UPDATE failure_patterns 
                SET count = count + 1, last_seen = ?
                WHERE pattern_hash = ?
            """, (timestamp, pattern_hash))
        else:
            # Create new pattern
            pattern_description = f"{tool} {error_type}: {error_message[:100]}"
            cursor.execute("""
                INSERT INTO failure_patterns 
                (pattern_hash, pattern_description, last_seen)
                VALUES (?, ?, ?)
            """, (pattern_hash, pattern_description, timestamp))
        
        conn.commit()
        conn.close()
    
    def get_similar_failures(
        self,
        user_input: str,
        tool: Optional[str] = None,
        limit: int = 5
    ) -> List[Failure]:
        """
        Get similar past failures
        
        Args:
            user_input: Current user command
            tool: Filter by tool (optional)
            limit: Maximum results
        
        Returns:
            List of similar failures
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Simple similarity: exact tool match or keyword overlap
        query = """
            SELECT id, timestamp, user_input, intent_goal, tool,
                   error_type, error_message, context_json, resolution
            FROM failures
            WHERE 1=1
        """
        params = []
        
        if tool:
            query += " AND tool = ?"
            params.append(tool)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        
        failures = []
        for row in results:
            context = json.loads(row[7]) if row[7] else {}
            failures.append(Failure(
                id=row[0],
                timestamp=row[1],
                user_input=row[2],
                intent_goal=row[3],
                tool=row[4],
                error_type=row[5],
                error_message=row[6],
                context=context,
                resolution=row[8]
            ))
        
        return failures
    
    def get_pattern_suggestions(self, tool: str, error_message: str) -> Optional[str]:
        """
        Get suggested fix for a pattern
        
        Args:
            tool: Tool that failed
            error_message: Error message
        
        Returns:
            Suggested fix if available
        """
        # Normalize error for pattern matching
        normalized_error = self._normalize_error(error_message)
        pattern_str = f"{tool}:*:{normalized_error}"
        pattern_hash = hashlib.md5(pattern_str.encode()).hexdigest()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT suggested_fix, count, success_after_fix
            FROM failure_patterns
            WHERE pattern_hash = ?
        """, (pattern_hash,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            # Return suggestion if it has been successful
            if result[2] > result[1] * 0.5:  # 50%+ success rate
                return result[0]
        
        return None
    
    def add_pattern_suggestion(
        self,
        pattern_hash: str,
        suggested_fix: str
    ):
        """
        Add a suggested fix for a pattern
        
        Args:
            pattern_hash: Pattern hash
            suggested_fix: Suggested fix description
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE failure_patterns
            SET suggested_fix = ?
            WHERE pattern_hash = ?
        """, (suggested_fix, pattern_hash))
        
        conn.commit()
        conn.close()
    
    def mark_pattern_success(self, pattern_hash: str):
        """
        Mark that a suggested fix worked
        
        Args:
            pattern_hash: Pattern hash
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE failure_patterns
            SET success_after_fix = success_after_fix + 1
            WHERE pattern_hash = ?
        """, (pattern_hash,))
        
        conn.commit()
        conn.close()
    
    def get_failure_stats(self) -> Dict:
        """
        Get overall failure statistics
        
        Returns:
            Dictionary with stats
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total failures
        cursor.execute("SELECT COUNT(*) FROM failures")
        total = cursor.fetchone()[0]
        
        # Failures by tool
        cursor.execute("""
            SELECT tool, COUNT(*) as count
            FROM failures
            GROUP BY tool
            ORDER BY count DESC
            LIMIT 10
        """)
        by_tool = dict(cursor.fetchall())
        
        # Failures by error type
        cursor.execute("""
            SELECT error_type, COUNT(*) as count
            FROM failures
            GROUP BY error_type
            ORDER BY count DESC
        """)
        by_type = dict(cursor.fetchall())
        
        # Recent failures (last 7 days)
        cursor.execute("""
            SELECT COUNT(*)
            FROM failures
            WHERE timestamp >= datetime('now', '-7 days')
        """)
        recent = cursor.fetchone()[0]
        
        # Patterns with suggestions
        cursor.execute("""
            SELECT COUNT(*)
            FROM failure_patterns
            WHERE suggested_fix IS NOT NULL
        """)
        with_suggestions = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_failures": total,
            "by_tool": by_tool,
            "by_error_type": by_type,
            "recent_7_days": recent,
            "patterns_with_suggestions": with_suggestions
        }
    
    @staticmethod
    def _normalize_error(error_message: str) -> str:
        """
        Normalize error message for pattern matching
        
        Removes specific details like file paths, line numbers, etc.
        """
        import re
        
        # Remove file paths
        normalized = re.sub(r'/[\w/.-]+', '/<path>', error_message)
        
        # Remove line numbers
        normalized = re.sub(r'line \d+', 'line <N>', normalized)
        
        # Remove specific numbers
        normalized = re.sub(r'\d+', '<NUM>', normalized)
        
        # Convert to lowercase
        normalized = normalized.lower()
        
        return normalized[:200]  # Limit length


# Global instance
_failure_logger = None


def get_failure_logger() -> FailureLogger:
    """Get global failure logger instance"""
    global _failure_logger
    if _failure_logger is None:
        _failure_logger = FailureLogger()
    return _failure_logger

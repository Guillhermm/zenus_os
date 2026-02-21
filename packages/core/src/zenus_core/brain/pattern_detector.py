"""
Pattern Detector

Learns user patterns from execution history:
- Recurring commands (daily/weekly/monthly)
- Common workflows (sequences of actions)
- Preferred tools for specific tasks
- Time-based patterns
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import Counter, defaultdict


@dataclass
class DetectedPattern:
    """A detected usage pattern"""
    pattern_type: str  # 'recurring', 'workflow', 'preference', 'time-based'
    description: str
    confidence: float  # 0.0 to 1.0
    occurrences: int
    first_seen: str
    last_seen: str
    frequency: Optional[str] = None  # 'daily', 'weekly', 'monthly'
    suggested_cron: Optional[str] = None
    commands: List[str] = field(default_factory=list)


class PatternDetector:
    """
    Detects patterns in user behavior
    
    Features:
    - Recurring command detection
    - Workflow pattern recognition
    - Time-based pattern analysis
    - Automation suggestions
    """
    
    def __init__(self):
        self.min_occurrences = 3  # Minimum occurrences to detect pattern
        self.min_confidence = 0.7  # Minimum confidence to suggest
    
    def detect_patterns(
        self,
        history: List[Dict],
        lookback_days: int = 30
    ) -> List[DetectedPattern]:
        """
        Detect patterns from execution history
        
        Args:
            history: List of execution records
            lookback_days: How many days to analyze
        
        Returns:
            List of detected patterns
        """
        patterns = []
        
        # Filter to lookback period
        cutoff_date = datetime.now() - timedelta(days=lookback_days)
        recent_history = []
        for h in history:
            ts = self._parse_timestamp(h.get('timestamp', ''))
            if ts and ts > cutoff_date:
                recent_history.append(h)
        
        if len(recent_history) < self.min_occurrences:
            return patterns
        
        # Detect different pattern types
        patterns.extend(self._detect_recurring_commands(recent_history))
        patterns.extend(self._detect_workflows(recent_history))
        patterns.extend(self._detect_time_patterns(recent_history))
        patterns.extend(self._detect_preferences(recent_history))
        
        # Sort by confidence
        patterns.sort(key=lambda p: p.confidence, reverse=True)
        
        return patterns
    
    def _detect_recurring_commands(self, history: List[Dict]) -> List[DetectedPattern]:
        """Detect commands that repeat regularly"""
        patterns = []
        
        # Group by normalized command
        command_groups = defaultdict(list)
        for record in history:
            cmd = record.get('user_input', '')
            normalized = self._normalize_command(cmd)
            command_groups[normalized].append(record)
        
        # Analyze each command group
        for normalized_cmd, records in command_groups.items():
            if len(records) < self.min_occurrences:
                continue
            
            # Get timestamps
            timestamps = [
                self._parse_timestamp(r.get('timestamp', ''))
                for r in records
            ]
            timestamps = [t for t in timestamps if t]
            
            if not timestamps:
                continue
            
            # Detect frequency
            frequency, cron_expr = self._detect_frequency(timestamps)
            
            if frequency:
                confidence = min(len(records) / 10.0, 1.0)  # More occurrences = higher confidence
                
                pattern = DetectedPattern(
                    pattern_type='recurring',
                    description=f"You {normalized_cmd} {frequency}",
                    confidence=confidence,
                    occurrences=len(records),
                    first_seen=records[0].get('timestamp', ''),
                    last_seen=records[-1].get('timestamp', ''),
                    frequency=frequency,
                    suggested_cron=cron_expr,
                    commands=[r.get('user_input', '') for r in records]
                )
                patterns.append(pattern)
        
        return patterns
    
    def _detect_workflows(self, history: List[Dict]) -> List[DetectedPattern]:
        """Detect command sequences (workflows)"""
        patterns = []
        
        # Look for sequences of commands within short time windows
        window_minutes = 30
        sequences = []
        current_sequence = []
        last_timestamp = None
        
        for record in history:
            timestamp = self._parse_timestamp(record.get('timestamp', ''))
            if not timestamp:
                continue
            
            if last_timestamp is None or (timestamp - last_timestamp).total_seconds() / 60 <= window_minutes:
                current_sequence.append(record)
            else:
                if len(current_sequence) >= 2:
                    sequences.append(current_sequence)
                current_sequence = [record]
            
            last_timestamp = timestamp
        
        # Add final sequence
        if len(current_sequence) >= 2:
            sequences.append(current_sequence)
        
        # Find common sequences
        sequence_patterns = Counter()
        for seq in sequences:
            normalized = tuple(self._normalize_command(r.get('user_input', '')) for r in seq)
            sequence_patterns[normalized] += 1
        
        # Create patterns for common sequences
        for seq, count in sequence_patterns.items():
            if count >= self.min_occurrences:
                confidence = min(count / 5.0, 1.0)
                
                pattern = DetectedPattern(
                    pattern_type='workflow',
                    description=f"Common workflow: {' → '.join(seq)}",
                    confidence=confidence,
                    occurrences=count,
                    first_seen='',  # Would need to track
                    last_seen='',
                    commands=list(seq)
                )
                patterns.append(pattern)
        
        return patterns
    
    def _detect_time_patterns(self, history: List[Dict]) -> List[DetectedPattern]:
        """Detect time-based patterns (e.g., always runs at 9 AM)"""
        patterns = []
        
        # Group by hour of day
        hour_commands = defaultdict(list)
        for record in history:
            timestamp = self._parse_timestamp(record.get('timestamp', ''))
            if timestamp:
                hour = timestamp.hour
                cmd = self._normalize_command(record.get('user_input', ''))
                hour_commands[hour].append(cmd)
        
        # Find commands that cluster at specific times
        for hour, commands in hour_commands.items():
            command_counts = Counter(commands)
            
            for cmd, count in command_counts.items():
                if count >= self.min_occurrences:
                    confidence = min(count / 10.0, 1.0)
                    
                    pattern = DetectedPattern(
                        pattern_type='time-based',
                        description=f"You typically {cmd} around {hour:02d}:00",
                        confidence=confidence,
                        occurrences=count,
                        first_seen='',
                        last_seen='',
                        commands=[cmd]
                    )
                    patterns.append(pattern)
        
        return patterns
    
    def _detect_preferences(self, history: List[Dict]) -> List[DetectedPattern]:
        """Detect tool/action preferences"""
        patterns = []
        
        # Track tool usage
        tool_counts = Counter()
        for record in history:
            intent = record.get('intent', {})
            for step in intent.get('steps', []):
                tool = step.get('tool', '')
                if tool:
                    tool_counts[tool] += 1
        
        # Find dominant tools
        total_tool_uses = sum(tool_counts.values())
        if total_tool_uses > 0:
            for tool, count in tool_counts.most_common(3):
                percentage = count / total_tool_uses
                if percentage > 0.3:  # Tool used in >30% of operations
                    pattern = DetectedPattern(
                        pattern_type='preference',
                        description=f"You frequently use {tool} ({percentage:.0%} of operations)",
                        confidence=percentage,
                        occurrences=count,
                        first_seen='',
                        last_seen='',
                        commands=[]
                    )
                    patterns.append(pattern)
        
        return patterns
    
    def _normalize_command(self, command: str) -> str:
        """Normalize command for pattern matching"""
        # Remove specific paths and numbers
        normalized = re.sub(r'/[^\s]+', '<path>', command)
        normalized = re.sub(r'\d+', '<number>', normalized)
        normalized = normalized.lower().strip()
        return normalized
    
    def _detect_frequency(self, timestamps: List[datetime]) -> Tuple[Optional[str], Optional[str]]:
        """
        Detect frequency pattern from timestamps
        
        Returns:
            (frequency_description, cron_expression) or (None, None)
        """
        if len(timestamps) < 2:
            return None, None
        
        # Calculate intervals
        intervals = []
        for i in range(1, len(timestamps)):
            delta = timestamps[i] - timestamps[i-1]
            intervals.append(delta.total_seconds() / 3600)  # Hours
        
        avg_interval = sum(intervals) / len(intervals)
        
        # Classify frequency
        if 20 <= avg_interval <= 28:  # ~24 hours
            # Daily pattern
            avg_hour = sum(t.hour for t in timestamps) / len(timestamps)
            cron = f"0 {int(avg_hour)} * * *"
            return "daily", cron
        
        elif 160 <= avg_interval <= 200:  # ~7 days
            # Weekly pattern
            avg_weekday = sum(t.weekday() for t in timestamps) / len(timestamps)
            avg_hour = sum(t.hour for t in timestamps) / len(timestamps)
            cron = f"0 {int(avg_hour)} * * {int(avg_weekday)}"
            return "weekly", cron
        
        elif 600 <= avg_interval <= 800:  # ~30 days
            # Monthly pattern
            avg_day = sum(t.day for t in timestamps) / len(timestamps)
            avg_hour = sum(t.hour for t in timestamps) / len(timestamps)
            cron = f"0 {int(avg_hour)} {int(avg_day)} * *"
            return "monthly", cron
        
        return None, None
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse timestamp string to datetime"""
        if not timestamp_str:
            return None
        
        try:
            # Handle ISO format
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except:
            return None


# Global instance
_pattern_detector: Optional[PatternDetector] = None


def get_pattern_detector() -> PatternDetector:
    """Get singleton pattern detector"""
    global _pattern_detector
    if _pattern_detector is None:
        _pattern_detector = PatternDetector()
    return _pattern_detector

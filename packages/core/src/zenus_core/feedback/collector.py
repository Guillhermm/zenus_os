"""
Feedback Collection System

Collects user feedback on command executions:
- Thumbs up/down after each command
- Success metric tracking
- Training data export for fine-tuning
"""

import json
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, asdict

from zenus_core.brain.llm.schemas import IntentIR


@dataclass
class FeedbackEntry:
    """Single feedback entry"""
    timestamp: str
    user_input: str
    intent_goal: str
    tool_used: str
    feedback: str  # 'positive', 'negative', 'skip'
    execution_time_ms: float
    success: bool
    comment: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dict"""
        return asdict(self)


class FeedbackCollector:
    """
    Collects and stores user feedback
    
    Features:
    - Quick thumbs up/down prompts
    - Success rate tracking per tool/intent
    - Export training data
    - Privacy-aware (filters sensitive data)
    """
    
    def __init__(
        self,
        feedback_path: Optional[str] = None,
        prompt_frequency: float = 0.1,  # 10% of commands (less annoying)
        enable_prompts: bool = True
    ):
        if feedback_path is None:
            feedback_path = Path.home() / ".zenus" / "feedback.jsonl"
        
        self.feedback_path = Path(feedback_path)
        self.feedback_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.prompt_frequency = prompt_frequency
        
        # Check environment variable for override
        import os
        env_enable = os.environ.get('ZENUS_FEEDBACK_PROMPTS', '').lower()
        if env_enable in ('false', '0', 'no', 'off'):
            self.enable_prompts = False
        else:
            self.enable_prompts = enable_prompts
        
        # Track what we've already asked about (session-level, normalized)
        self._asked_this_session: set = set()
        
        # Stats cache
        self._stats_cache: Optional[Dict] = None
        self._stats_cache_time: float = 0
        self._stats_cache_ttl: int = 300  # 5 minutes
    
    def collect(
        self,
        user_input: str,
        intent: IntentIR,
        execution_time_ms: float,
        success: bool
    ) -> Optional[str]:
        """
        Collect feedback from user
        
        Args:
            user_input: User's command
            intent: Executed IntentIR
            execution_time_ms: Time taken
            success: Whether execution succeeded
        
        Returns:
            Feedback ('positive', 'negative', 'skip') or None
        """
        if not self.enable_prompts:
            return None
        
        # Normalize command for deduplication
        normalized = user_input.lower().strip()
        
        # Don't ask if we already asked this session
        if normalized in self._asked_this_session:
            return None
        
        # Don't ask if we already have feedback for this command (from any session)
        if self._already_has_feedback(normalized):
            return None
        
        # Random sampling based on frequency (less annoying)
        import random
        if random.random() > self.prompt_frequency:
            return None
        
        # Mark as asked this session
        self._asked_this_session.add(normalized)
        
        # Prompt user
        from rich.console import Console
        console = Console()
        
        try:
            response = console.input("\n[bold cyan]Was this helpful?[/bold cyan] (y/n/skip): ").strip().lower()
            
            if response in ['y', 'yes']:
                feedback = 'positive'
            elif response in ['n', 'no']:
                feedback = 'negative'
                
                # Ask for optional comment
                comment = console.input("[dim]What went wrong? (optional):[/dim] ").strip()
                if comment:
                    self._record_feedback(
                        user_input, intent, execution_time_ms, success, feedback, comment
                    )
                    return feedback
            else:
                feedback = 'skip'
            
            # Record feedback
            self._record_feedback(
                user_input, intent, execution_time_ms, success, feedback
            )
            
            return feedback
        
        except (KeyboardInterrupt, EOFError):
            return None
    
    def _record_feedback(
        self,
        user_input: str,
        intent: IntentIR,
        execution_time_ms: float,
        success: bool,
        feedback: str,
        comment: Optional[str] = None
    ):
        """Record feedback to disk"""
        # Determine primary tool
        tool_used = intent.steps[0].tool if intent.steps else "unknown"
        
        entry = FeedbackEntry(
            timestamp=datetime.now().isoformat(),
            user_input=user_input[:200],  # Truncate for privacy
            intent_goal=intent.goal[:200],
            tool_used=tool_used,
            feedback=feedback,
            execution_time_ms=execution_time_ms,
            success=success,
            comment=comment,
        )
        
        # Append to JSONL file
        try:
            with open(self.feedback_path, 'a') as f:
                f.write(json.dumps(entry.to_dict()) + '\n')
            
            # Invalidate stats cache
            self._stats_cache = None
        
        except Exception as e:
            # Non-critical, just skip
            pass
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get feedback statistics
        
        Returns stats by:
        - Overall success rate
        - Per tool
        - Per intent type
        - Positive/negative ratio
        """
        # Check cache
        if (self._stats_cache is not None and 
            time.time() - self._stats_cache_time < self._stats_cache_ttl):
            return self._stats_cache
        
        # Compute fresh stats
        stats = {
            'total_feedback': 0,
            'positive': 0,
            'negative': 0,
            'skip': 0,
            'by_tool': {},
            'by_success': {'successful': 0, 'failed': 0},
        }
        
        if not self.feedback_path.exists():
            return stats
        
        try:
            with open(self.feedback_path, 'r') as f:
                for line in f:
                    entry = json.loads(line)
                    
                    stats['total_feedback'] += 1
                    
                    feedback = entry.get('feedback', 'skip')
                    stats[feedback] = stats.get(feedback, 0) + 1
                    
                    # By tool
                    tool = entry.get('tool_used', 'unknown')
                    if tool not in stats['by_tool']:
                        stats['by_tool'][tool] = {
                            'total': 0, 'positive': 0, 'negative': 0
                        }
                    
                    stats['by_tool'][tool]['total'] += 1
                    if feedback == 'positive':
                        stats['by_tool'][tool]['positive'] += 1
                    elif feedback == 'negative':
                        stats['by_tool'][tool]['negative'] += 1
                    
                    # By success
                    if entry.get('success'):
                        stats['by_success']['successful'] += 1
                    else:
                        stats['by_success']['failed'] += 1
            
            # Calculate rates
            if stats['total_feedback'] > 0:
                stats['positive_rate'] = stats['positive'] / stats['total_feedback']
                stats['negative_rate'] = stats['negative'] / stats['total_feedback']
            
            # Cache it
            self._stats_cache = stats
            self._stats_cache_time = time.time()
            
            return stats
        
        except Exception as e:
            return stats
    
    def export_training_data(
        self,
        output_path: Optional[str] = None,
        min_rating: str = 'positive',
        include_negative: bool = False
    ) -> str:
        """
        Export training data for fine-tuning
        
        Args:
            output_path: Where to save (default: ~/.zenus/training_data.jsonl)
            min_rating: Minimum feedback rating to include
            include_negative: Include negative examples
        
        Returns:
            Path to exported file
        """
        if output_path is None:
            output_path = Path.home() / ".zenus" / "training_data.jsonl"
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not self.feedback_path.exists():
            return str(output_path)
        
        exported = 0
        
        try:
            with open(self.feedback_path, 'r') as fin:
                with open(output_path, 'w') as fout:
                    for line in fin:
                        entry = json.loads(line)
                        
                        feedback = entry.get('feedback', 'skip')
                        
                        # Filter by rating
                        if feedback == 'skip':
                            continue
                        
                        if feedback == 'negative' and not include_negative:
                            continue
                        
                        if min_rating == 'positive' and feedback != 'positive':
                            continue
                        
                        # Privacy filter (remove sensitive patterns)
                        user_input = self._sanitize_text(entry.get('user_input', ''))
                        intent_goal = self._sanitize_text(entry.get('intent_goal', ''))
                        
                        # Format for training
                        training_example = {
                            'prompt': user_input,
                            'completion': intent_goal,
                            'feedback': feedback,
                            'success': entry.get('success', False),
                        }
                        
                        fout.write(json.dumps(training_example) + '\n')
                        exported += 1
            
            return f"Exported {exported} examples to {output_path}"
        
        except Exception as e:
            return f"Export failed: {str(e)}"
    
    def _already_has_feedback(self, normalized_input: str) -> bool:
        """Check if we already have feedback for this command"""
        if not self.feedback_path.exists():
            return False
        
        try:
            with open(self.feedback_path, 'r') as f:
                for line in f:
                    entry = json.loads(line)
                    stored_input = entry.get('user_input', '').lower().strip()
                    
                    # Check if it's the same command (or very similar)
                    if stored_input == normalized_input:
                        # We have feedback for this already
                        return True
                    
                    # Also check if it's a substring match (very similar)
                    if len(normalized_input) > 20:  # Only for longer commands
                        if normalized_input in stored_input or stored_input in normalized_input:
                            return True
            
            return False
        
        except:
            return False
    
    def _sanitize_text(self, text: str) -> str:
        """Remove sensitive information from text"""
        import re
        
        # Remove potential passwords, tokens, API keys
        text = re.sub(r'(password|token|key|secret)[\s:=]+\S+', '[REDACTED]', text, flags=re.IGNORECASE)
        
        # Remove email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
        
        # Remove URLs with potential tokens
        text = re.sub(r'https?://[^\s]+[?&](token|key|auth)=[^\s&]+', '[URL]', text)
        
        return text


# Global collector
_feedback_collector: Optional[FeedbackCollector] = None


def get_feedback_collector() -> FeedbackCollector:
    """Get singleton feedback collector"""
    global _feedback_collector
    if _feedback_collector is None:
        _feedback_collector = FeedbackCollector()
    return _feedback_collector

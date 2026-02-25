"""
Metrics Collection System

Tracks performance metrics for monitoring and optimization:
- Token usage per command
- Latency distribution
- Success/failure rates
- Cache hit rates
- Cost tracking
"""

import time
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import defaultdict


@dataclass
class MetricPoint:
    """Single metric data point"""
    timestamp: float
    metric_name: str
    value: float
    tags: Dict[str, str]
    
    def to_dict(self) -> Dict:
        return asdict(self)


class MetricsCollector:
    """
    Collects and stores performance metrics
    
    Metrics tracked:
    - command_latency_ms: Time to execute
    - tokens_used: LLM tokens consumed
    - cache_hit: Cache hit (1) or miss (0)
    - success: Command succeeded (1) or failed (0)
    - cost_estimate: Estimated cost in dollars
    """
    
    def __init__(
        self,
        metrics_path: Optional[str] = None,
        flush_interval: int = 10,  # Flush every N metrics
    ):
        if metrics_path is None:
            metrics_path = Path.home() / ".zenus" / "metrics.jsonl"
        
        self.metrics_path = Path(metrics_path)
        self.metrics_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.flush_interval = flush_interval
        
        # In-memory buffer
        self.buffer: List[MetricPoint] = []
        
        # Aggregates for quick stats
        self.aggregates = {
            'total_commands': 0,
            'total_tokens': 0,
            'total_cost': 0.0,
            'cache_hits': 0,
            'cache_misses': 0,
            'successes': 0,
            'failures': 0,
            'latency_sum': 0.0,
            'by_model': defaultdict(lambda: {
                'count': 0, 'tokens': 0, 'cost': 0.0, 'latency_sum': 0.0
            }),
        }
    
    def record(
        self,
        metric_name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None
    ):
        """
        Record a metric
        
        Args:
            metric_name: Name of metric (e.g., 'command_latency_ms')
            value: Metric value
            tags: Optional tags (e.g., {'model': 'deepseek', 'tool': 'FileOps'})
        """
        point = MetricPoint(
            timestamp=time.time(),
            metric_name=metric_name,
            value=value,
            tags=tags or {}
        )
        
        self.buffer.append(point)
        
        # Update aggregates
        self._update_aggregates(point)
        
        # Flush if buffer full
        if len(self.buffer) >= self.flush_interval:
            self.flush()
    
    def record_command(
        self,
        latency_ms: float,
        model: str,
        tool: str,
        tokens: int = 0,
        cost: float = 0.0,
        cache_hit: bool = False,
        success: bool = True
    ):
        """
        Convenience method to record command execution
        
        Args:
            latency_ms: Execution time in milliseconds
            model: LLM model used
            tool: Tool used
            tokens: Tokens consumed
            cost: Estimated cost
            cache_hit: Whether cache was hit
            success: Whether command succeeded
        """
        tags = {
            'model': model,
            'tool': tool,
        }
        
        self.record('command_latency_ms', latency_ms, tags)
        
        if tokens > 0:
            self.record('tokens_used', tokens, tags)
        
        if cost > 0:
            self.record('cost_estimate', cost, tags)
        
        self.record('cache_hit', 1.0 if cache_hit else 0.0, tags)
        self.record('success', 1.0 if success else 0.0, tags)
    
    def _update_aggregates(self, point: MetricPoint):
        """Update in-memory aggregates"""
        tags = point.tags
        model = tags.get('model', 'unknown')
        
        if point.metric_name == 'command_latency_ms':
            self.aggregates['total_commands'] += 1
            self.aggregates['latency_sum'] += point.value
            self.aggregates['by_model'][model]['count'] += 1
            self.aggregates['by_model'][model]['latency_sum'] += point.value
        
        elif point.metric_name == 'tokens_used':
            self.aggregates['total_tokens'] += point.value
            self.aggregates['by_model'][model]['tokens'] += point.value
        
        elif point.metric_name == 'cost_estimate':
            self.aggregates['total_cost'] += point.value
            self.aggregates['by_model'][model]['cost'] += point.value
        
        elif point.metric_name == 'cache_hit':
            if point.value > 0:
                self.aggregates['cache_hits'] += 1
            else:
                self.aggregates['cache_misses'] += 1
        
        elif point.metric_name == 'success':
            if point.value > 0:
                self.aggregates['successes'] += 1
            else:
                self.aggregates['failures'] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get current statistics
        
        Returns:
            Dictionary with current metrics
        """
        total_commands = self.aggregates['total_commands']
        
        stats = {
            'total_commands': total_commands,
            'total_tokens': int(self.aggregates['total_tokens']),
            'total_cost': round(self.aggregates['total_cost'], 4),
            'cache_hits': self.aggregates['cache_hits'],
            'cache_misses': self.aggregates['cache_misses'],
            'successes': self.aggregates['successes'],
            'failures': self.aggregates['failures'],
        }
        
        # Calculated stats
        if total_commands > 0:
            stats['avg_latency_ms'] = round(
                self.aggregates['latency_sum'] / total_commands, 2
            )
            stats['success_rate'] = round(
                self.aggregates['successes'] / total_commands, 3
            )
        
        total_cache_requests = stats['cache_hits'] + stats['cache_misses']
        if total_cache_requests > 0:
            stats['cache_hit_rate'] = round(
                stats['cache_hits'] / total_cache_requests, 3
            )
        
        # Per-model stats
        stats['by_model'] = {}
        for model, data in self.aggregates['by_model'].items():
            count = data['count']
            if count > 0:
                stats['by_model'][model] = {
                    'commands': count,
                    'tokens': int(data['tokens']),
                    'cost': round(data['cost'], 4),
                    'avg_latency_ms': round(data['latency_sum'] / count, 2),
                }
        
        return stats
    
    def flush(self):
        """Flush buffer to disk"""
        if not self.buffer:
            return
        
        try:
            with open(self.metrics_path, 'a') as f:
                for point in self.buffer:
                    f.write(json.dumps(point.to_dict()) + '\n')
            
            self.buffer.clear()
        
        except Exception as e:
            # Non-critical, just skip
            pass
    
    def query(
        self,
        metric_name: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        tags: Optional[Dict[str, str]] = None,
        limit: int = 1000
    ) -> List[MetricPoint]:
        """
        Query metrics from disk
        
        Args:
            metric_name: Filter by metric name
            start_time: Start timestamp
            end_time: End timestamp
            tags: Filter by tags
            limit: Maximum results
        
        Returns:
            List of matching metric points
        """
        if not self.metrics_path.exists():
            return []
        
        results = []
        
        try:
            with open(self.metrics_path, 'r') as f:
                for line in f:
                    data = json.loads(line)
                    point = MetricPoint(**data)
                    
                    # Apply filters
                    if metric_name and point.metric_name != metric_name:
                        continue
                    
                    if start_time and point.timestamp < start_time:
                        continue
                    
                    if end_time and point.timestamp > end_time:
                        continue
                    
                    if tags:
                        if not all(point.tags.get(k) == v for k, v in tags.items()):
                            continue
                    
                    results.append(point)
                    
                    if len(results) >= limit:
                        break
        
        except Exception as e:
            pass
        
        return results


# Global collector
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get singleton metrics collector"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector

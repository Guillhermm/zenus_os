"""Rich output formatting"""

from zenus_core.output.formatter import OutputFormatter, get_formatter, format_output

__all__ = ['OutputFormatter', 'get_formatter', 'format_output']

from zenus_core.output.console import (  # noqa: F401
    console, print_success, print_error, print_warning, print_info,
    print_step, print_goal, print_plan_summary, print_similar_commands,
    print_explanation, print_code_block, print_json, print_divider,
    print_header, print_status_table
)
from zenus_core.output.streaming import StreamHandler, get_stream_handler
from zenus_core.output.progress import ProgressTracker, StreamingDisplay, get_progress_tracker, get_streaming_display, ProgressIndicator

__all__ += [
    'console', 'print_success', 'print_error', 'print_warning', 'print_info',
    'StreamHandler', 'get_stream_handler',
    'ProgressTracker', 'StreamingDisplay', 'get_progress_tracker', 'get_streaming_display', 'ProgressIndicator'
]

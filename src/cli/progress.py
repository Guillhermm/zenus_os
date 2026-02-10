"""
Progress Indicators

Show thinking and execution progress to user.
"""

import sys
import time
import threading
from contextlib import contextmanager


class ProgressIndicator:
    """Shows progress for long-running operations"""
    
    def __init__(self):
        self.active = False
        self.thread = None
        self.start_time = None
    
    @contextmanager
    def thinking(self, message: str = "Thinking"):
        """Show thinking indicator"""
        self.start(message)
        try:
            yield
        finally:
            self.stop()
    
    @contextmanager
    def executing(self, message: str = "Executing"):
        """Show execution indicator"""
        self.start(message)
        try:
            yield
        finally:
            self.stop()
    
    def start(self, message: str):
        """Start progress indicator"""
        self.active = True
        self.start_time = time.time()
        self.thread = threading.Thread(target=self._animate, args=(message,))
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        """Stop progress indicator"""
        self.active = False
        if self.thread:
            self.thread.join(timeout=0.5)
        
        # Clear the line
        sys.stdout.write('\r' + ' ' * 80 + '\r')
        sys.stdout.flush()
        
        # Show elapsed time
        if self.start_time:
            elapsed = time.time() - self.start_time
            if elapsed > 1.0:
                print(f"  (completed in {elapsed:.1f}s)")
    
    def _animate(self, message: str):
        """Animation loop"""
        frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        idx = 0
        
        while self.active:
            elapsed = time.time() - self.start_time if self.start_time else 0
            frame = frames[idx % len(frames)]
            sys.stdout.write(f'\r  {frame} {message}... ({elapsed:.1f}s)')
            sys.stdout.flush()
            idx += 1
            time.sleep(0.1)

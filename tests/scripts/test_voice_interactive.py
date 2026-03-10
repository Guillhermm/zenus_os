#!/usr/bin/env python3
"""
Interactive voice test - listens for ONE voice command
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "packages/core/src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "packages/voice/src"))

from zenus_core.cli.orchestrator import Orchestrator
from zenus_voice import create_voice_interface, WhisperModel

print("🎤 Zenus Voice - Interactive Test")
print("=" * 40)

# Create orchestrator
print("Initializing Zenus...")
orch = Orchestrator()

# Create voice interface
print("Loading voice interface (Whisper model will download on first run)...")
voice = create_voice_interface(
    orch,
    stt_model=WhisperModel.TINY,  # Fastest for testing
    device="cpu"
)

print("\n✓ Ready!")
print("=" * 40)
print("\nSpeak your command when you see '🎤 Listening...'")
print("Example commands:")
print("  - 'List files in current directory'")
print("  - 'Show system information'")
print("  - 'What's the current time'")
print("\nPress Ctrl+C to exit\n")

try:
    # Listen and execute one command
    result = voice.listen_and_execute()
    
    print("\n" + "=" * 40)
    print("✓ Command executed!")
    print("=" * 40)
    
except KeyboardInterrupt:
    print("\n\nExiting...")
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

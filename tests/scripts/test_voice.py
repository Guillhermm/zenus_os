#!/usr/bin/env python3
"""
Quick test script for Zenus Voice Interface

Tests voice interface functionality step-by-step
"""

import sys
import os

# Add packages to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "packages/core/src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "packages/voice/src"))

print("=" * 60)
print("🎤 ZENUS VOICE INTERFACE TEST")
print("=" * 60)

# Test 1: Import packages
print("\n📦 Test 1: Checking imports...")
try:
    from zenus_core.cli.orchestrator import Orchestrator
    print("✓ zenus_core imported")
except Exception as e:
    print(f"✗ Failed to import zenus_core: {e}")
    sys.exit(1)

try:
    import zenus_voice
    print("✓ zenus_voice imported")
except Exception as e:
    print(f"✗ Failed to import zenus_voice: {e}")
    print("\n💡 Install voice package:")
    print("   cd packages/voice")
    print("   poetry install")
    sys.exit(1)

# Test 2: Check dependencies
print("\n📦 Test 2: Checking dependencies...")

try:
    import whisper
    print("✓ whisper available")
except ImportError:
    print("✗ whisper not installed")
    print("   pip install openai-whisper")

try:
    import pyaudio
    print("✓ pyaudio available")
except ImportError:
    print("✗ pyaudio not installed")
    print("   Linux: sudo apt-get install portaudio19-dev && pip install pyaudio")
    print("   macOS: brew install portaudio && pip install pyaudio")
    print("   Windows: Download wheel from https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio")

try:
    import pyttsx3
    print("✓ pyttsx3 available")
except ImportError:
    print("✗ pyttsx3 not installed")
    print("   pip install pyttsx3")

try:
    import webrtcvad
    print("✓ webrtcvad available")
except ImportError:
    print("⚠ webrtcvad not installed (optional)")
    print("   pip install webrtcvad")

# Test 3: Create orchestrator
print("\n🧠 Test 3: Creating Zenus orchestrator...")
try:
    orch = Orchestrator()
    print("✓ Orchestrator created")
except Exception as e:
    print(f"✗ Failed to create orchestrator: {e}")
    sys.exit(1)

# Test 4: Check microphone
print("\n🎤 Test 4: Checking microphone...")
try:
    import pyaudio
    audio = pyaudio.PyAudio()
    
    devices = []
    for i in range(audio.get_device_count()):
        info = audio.get_device_info_by_index(i)
        if info['maxInputChannels'] > 0:
            devices.append((i, info['name']))
    
    if devices:
        print(f"✓ Found {len(devices)} input device(s):")
        for idx, name in devices:
            print(f"  [{idx}] {name}")
    else:
        print("✗ No microphone detected!")
        print("   Connect a microphone and try again")
    
    audio.terminate()
except Exception as e:
    print(f"⚠ Could not check microphone: {e}")

# Test 5: Test TTS (without voice, just check it initializes)
print("\n🔊 Test 5: Testing TTS initialization...")
try:
    from zenus_voice import get_tts, TTSEngine
    
    print("  Testing system TTS...")
    tts = get_tts(TTSEngine.PYTTSX3)
    print("✓ System TTS initialized")
    
    # Test listing voices
    from zenus_voice.tts import SystemTTS
    system_tts = SystemTTS()
    voices = system_tts.list_voices()
    print(f"  Available system voices: {len(voices)}")
    for voice in voices[:3]:
        print(f"    - {voice}")
    if len(voices) > 3:
        print(f"    ... and {len(voices) - 3} more")
    
except Exception as e:
    print(f"✗ TTS initialization failed: {e}")

# Test 6: Create voice interface (without actually using microphone)
print("\n🎤 Test 6: Creating voice interface...")
try:
    from zenus_voice import create_voice_interface, WhisperModel, TTSEngine, Voice
    
    print("  Creating voice interface (this may take a moment)...")
    print("  Whisper will download model on first run (~74MB for base model)...")
    
    voice = create_voice_interface(
        orch,
        stt_model=WhisperModel.TINY,  # Fastest model for testing
        tts_engine=TTSEngine.PYTTSX3,  # System TTS (no download needed)
        device="cpu"
    )
    
    print("✓ Voice interface created successfully!")
    
    # Test speaking (if TTS works)
    try:
        print("\n  Testing TTS (you should hear this)...")
        voice.set_voice_responses(True)
        voice._respond("Voice interface test successful!")
        print("✓ TTS working")
    except Exception as e:
        print(f"⚠ TTS test failed (non-critical): {e}")
    
except Exception as e:
    print(f"✗ Voice interface creation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Summary
print("\n" + "=" * 60)
print("🎉 VOICE INTERFACE READY!")
print("=" * 60)
print("\nTo use voice control:")
print("  1. Basic mode (one command):")
print("     python3 test_voice_interactive.py")
print()
print("  2. Test with a file:")
print("     python3 test_voice_file.py <audio_file.wav>")
print()
print("  3. Full voice interface:")
print("     cd packages/voice")
print("     poetry run zenus-voice")
print()
print("=" * 60)

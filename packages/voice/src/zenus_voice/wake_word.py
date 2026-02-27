"""
Wake Word Detection

Detect "Hey Zenus" or custom wake words to activate voice control.
Uses Porcupine for accurate, efficient wake word detection.
"""

import pyaudio
import struct
from typing import Optional, Callable
from enum import Enum


class WakeWord(Enum):
    """Supported wake words"""
    HEY_ZENUS = "hey_zenus"
    COMPUTER = "computer"
    JARVIS = "jarvis"
    ALEXA = "alexa"  # Just for demo, not affiliated with Amazon


class WakeWordDetector:
    """
    Wake word detection using Porcupine
    
    Listens in background for wake word, then triggers callback.
    Highly efficient - uses minimal CPU/battery.
    """
    
    def __init__(
        self,
        wake_word: WakeWord = WakeWord.HEY_ZENUS,
        access_key: Optional[str] = None,
        on_wake: Optional[Callable] = None
    ):
        """
        Args:
            wake_word: Which wake word to listen for
            access_key: Picovoice access key (get free key from picovoice.ai)
            on_wake: Callback function when wake word detected
        """
        self.wake_word = wake_word
        self.on_wake = on_wake
        self.is_listening = False
        
        # Initialize Porcupine
        try:
            import pvporcupine
            
            # Use provided access key or look for env variable
            if not access_key:
                import os
                access_key = os.getenv("PICOVOICE_ACCESS_KEY")
            
            if not access_key:
                raise ValueError(
                    "Picovoice access key required. "
                    "Get free key at https://picovoice.ai and set PICOVOICE_ACCESS_KEY env variable"
                )
            
            # Create Porcupine instance with built-in wake word
            keyword_paths = self._get_keyword_path(wake_word)
            
            self.porcupine = pvporcupine.create(
                access_key=access_key,
                keywords=[wake_word.value] if not keyword_paths else None,
                keyword_paths=keyword_paths
            )
            
            self.sample_rate = self.porcupine.sample_rate
            self.frame_length = self.porcupine.frame_length
            
            print(f"✓ Wake word detector initialized ({wake_word.value})")
            
        except ImportError:
            raise ImportError(
                "Porcupine not installed. Install with: "
                "pip install pvporcupine"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize wake word detector: {e}")
    
    def _get_keyword_path(self, wake_word: WakeWord) -> Optional[list]:
        """Get path to custom keyword file (if any)"""
        # For built-in keywords, return None to use Porcupine's defaults
        # For custom keywords, return path to .ppn file
        return None
    
    def start_listening(self):
        """Start listening for wake word in background"""
        if self.is_listening:
            return
        
        self.is_listening = True
        
        audio = pyaudio.PyAudio()
        
        try:
            stream = audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.frame_length
            )
            
            print(f"👂 Listening for '{self.wake_word.value}'...")
            
            while self.is_listening:
                pcm = stream.read(self.frame_length, exception_on_overflow=False)
                pcm = struct.unpack_from("h" * self.frame_length, pcm)
                
                keyword_index = self.porcupine.process(pcm)
                
                if keyword_index >= 0:
                    print(f"\n🔔 Wake word detected!")
                    
                    if self.on_wake:
                        self.on_wake()
            
            stream.stop_stream()
            stream.close()
            
        finally:
            audio.terminate()
    
    def stop_listening(self):
        """Stop listening for wake word"""
        self.is_listening = False
        print("👂 Wake word detection stopped")
    
    def __del__(self):
        """Cleanup"""
        if hasattr(self, 'porcupine'):
            self.porcupine.delete()


class SimpleWakeWordDetector:
    """
    Simple wake word detection without Porcupine (fallback)
    
    Uses basic audio analysis - less accurate but no dependencies.
    """
    
    def __init__(
        self,
        wake_phrase: str = "hey zenus",
        on_wake: Optional[Callable] = None
    ):
        """
        Args:
            wake_phrase: Phrase to listen for
            on_wake: Callback when phrase detected
        """
        self.wake_phrase = wake_phrase.lower()
        self.on_wake = on_wake
        self.is_listening = False
        
        # We'll use the STT engine for detection
        from zenus_voice.stt import SpeechToText, WhisperModel
        self.stt = SpeechToText(WhisperModel.TINY)  # Fastest model
        
        print(f"✓ Simple wake word detector initialized ('{wake_phrase}')")
    
    def start_listening(self):
        """Start listening for wake phrase"""
        if self.is_listening:
            return
        
        self.is_listening = True
        
        print(f"👂 Listening for '{self.wake_phrase}'...")
        
        while self.is_listening:
            try:
                # Listen for short audio snippet
                result = self.stt.listen_and_transcribe(
                    duration=3.0,  # 3 second snippets
                    silence_duration=0.8
                )
                
                # Check if wake phrase detected
                if result.text and self.wake_phrase in result.text.lower():
                    print(f"\n🔔 Wake phrase detected!")
                    
                    if self.on_wake:
                        self.on_wake()
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Wake word detection error: {e}")
    
    def stop_listening(self):
        """Stop listening"""
        self.is_listening = False
        print("👂 Wake word detection stopped")


def create_wake_detector(
    use_porcupine: bool = True,
    wake_word: WakeWord = WakeWord.HEY_ZENUS,
    access_key: Optional[str] = None,
    on_wake: Optional[Callable] = None
):
    """
    Create wake word detector
    
    Args:
        use_porcupine: Use Porcupine (True) or simple detector (False)
        wake_word: Which wake word to use
        access_key: Picovoice access key (required for Porcupine)
        on_wake: Callback when wake word detected
    
    Returns:
        WakeWordDetector or SimpleWakeWordDetector
    """
    if use_porcupine:
        try:
            return WakeWordDetector(wake_word, access_key, on_wake)
        except Exception as e:
            print(f"Porcupine not available ({e}), using simple detector")
            return SimpleWakeWordDetector(wake_word.value.replace("_", " "), on_wake)
    else:
        return SimpleWakeWordDetector(wake_word.value.replace("_", " "), on_wake)

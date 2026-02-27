"""
Speech-to-Text (STT) Module

Uses OpenAI Whisper for local, offline speech recognition.
No API keys needed - runs entirely on your machine!
"""

import whisper
import numpy as np
import soundfile as sf
import pyaudio
import wave
import tempfile
from pathlib import Path
from typing import Optional, Callable
from dataclasses import dataclass
from enum import Enum


class WhisperModel(Enum):
    """Available Whisper models (size vs accuracy trade-off)"""
    TINY = "tiny"        # ~39M params, fastest
    BASE = "base"        # ~74M params, good balance
    SMALL = "small"      # ~244M params, better accuracy
    MEDIUM = "medium"    # ~769M params, high accuracy
    LARGE = "large"      # ~1550M params, best accuracy


@dataclass
class TranscriptionResult:
    """Result from speech transcription"""
    text: str
    language: str
    confidence: float
    duration: float


class VoiceActivityDetector:
    """Detects when user is speaking vs silence"""
    
    def __init__(self, aggressiveness: int = 3):
        """
        Args:
            aggressiveness: 0-3, higher = more aggressive (less false positives)
        """
        import webrtcvad
        self.vad = webrtcvad.Vad(aggressiveness)
    
    def is_speech(self, audio_data: bytes, sample_rate: int) -> bool:
        """Check if audio frame contains speech"""
        try:
            return self.vad.is_speech(audio_data, sample_rate)
        except Exception:
            return False


class SpeechToText:
    """
    Local speech-to-text using Whisper
    
    Features:
    - Offline/local processing (no API calls)
    - Multi-language support
    - Voice activity detection
    - Configurable model size
    """
    
    def __init__(
        self,
        model: WhisperModel = WhisperModel.BASE,
        device: str = "cpu",  # or "cuda" for GPU
        language: Optional[str] = None  # None = auto-detect
    ):
        self.model_name = model.value
        self.device = device
        self.language = language
        
        # Load Whisper model (first time downloads, then cached)
        print(f"Loading Whisper {self.model_name} model...")
        self.model = whisper.load_model(self.model_name, device=device)
        print("✓ Whisper model loaded")
        
        # Voice activity detector
        self.vad = VoiceActivityDetector()
        
        # Audio settings
        self.sample_rate = 16000  # Whisper expects 16kHz
        self.chunk_duration = 0.03  # 30ms chunks
        self.chunk_size = int(self.sample_rate * self.chunk_duration)
    
    def transcribe_file(self, audio_path: str) -> TranscriptionResult:
        """
        Transcribe audio from file
        
        Args:
            audio_path: Path to audio file (wav, mp3, etc.)
        
        Returns:
            TranscriptionResult with text and metadata
        """
        import time
        start_time = time.time()
        
        # Transcribe with Whisper
        result = self.model.transcribe(
            audio_path,
            language=self.language,
            fp16=False  # Use FP32 for CPU
        )
        
        duration = time.time() - start_time
        
        return TranscriptionResult(
            text=result["text"].strip(),
            language=result["language"],
            confidence=self._estimate_confidence(result),
            duration=duration
        )
    
    def transcribe_audio_data(self, audio_data: np.ndarray) -> TranscriptionResult:
        """
        Transcribe raw audio data
        
        Args:
            audio_data: NumPy array of audio samples (float32, 16kHz)
        
        Returns:
            TranscriptionResult
        """
        # Save to temporary file (Whisper needs a file path)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            tmp_path = tmp_file.name
            sf.write(tmp_path, audio_data, self.sample_rate)
        
        try:
            result = self.transcribe_file(tmp_path)
            return result
        finally:
            # Clean up temp file
            Path(tmp_path).unlink(missing_ok=True)
    
    def listen_and_transcribe(
        self,
        duration: Optional[float] = None,
        silence_duration: float = 1.5,
        on_speech_start: Optional[Callable] = None,
        on_speech_end: Optional[Callable] = None
    ) -> TranscriptionResult:
        """
        Listen to microphone and transcribe speech
        
        Args:
            duration: Maximum recording duration (None = until silence)
            silence_duration: Seconds of silence to stop recording
            on_speech_start: Callback when speech detected
            on_speech_end: Callback when speech ends
        
        Returns:
            TranscriptionResult
        """
        import time
        
        # Initialize PyAudio
        audio = pyaudio.PyAudio()
        
        try:
            # Open microphone stream
            stream = audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            print("🎤 Listening... (speak now)")
            
            frames = []
            is_speaking = False
            silence_start = None
            recording_start = time.time()
            
            while True:
                # Read audio chunk
                data = stream.read(self.chunk_size, exception_on_overflow=False)
                
                # Check for speech
                has_speech = self.vad.is_speech(data, self.sample_rate)
                
                if has_speech:
                    if not is_speaking and on_speech_start:
                        on_speech_start()
                    is_speaking = True
                    silence_start = None
                    frames.append(data)
                elif is_speaking:
                    # Speech ended, track silence
                    if silence_start is None:
                        silence_start = time.time()
                    
                    frames.append(data)
                    
                    # Check if silence duration exceeded
                    if time.time() - silence_start > silence_duration:
                        if on_speech_end:
                            on_speech_end()
                        break
                
                # Check max duration
                if duration and (time.time() - recording_start) > duration:
                    break
            
            stream.stop_stream()
            stream.close()
            
            print("🎤 Recording complete")
            
            # Convert frames to numpy array
            audio_data = np.frombuffer(b''.join(frames), dtype=np.int16)
            audio_data = audio_data.astype(np.float32) / 32768.0  # Normalize to [-1, 1]
            
            # Transcribe
            return self.transcribe_audio_data(audio_data)
            
        finally:
            audio.terminate()
    
    def _estimate_confidence(self, whisper_result: dict) -> float:
        """Estimate transcription confidence from Whisper result"""
        # Whisper doesn't provide confidence directly
        # Use heuristics: language detection probability, no hallucination markers
        
        # Check if language was detected with high confidence
        language_prob = whisper_result.get("language_probability", 0.5)
        
        # Check for common hallucination patterns
        text = whisper_result["text"].lower()
        hallucination_markers = [
            "thank you for watching",
            "subscribe",
            "like and",
            "[music]",
            "[applause]"
        ]
        
        has_hallucination = any(marker in text for marker in hallucination_markers)
        
        if has_hallucination:
            return 0.3  # Low confidence
        
        return language_prob


class MicrophoneRecorder:
    """Helper for recording audio from microphone"""
    
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.chunk_size = 1024
    
    def record(self, duration: float, output_path: str):
        """
        Record audio for specified duration
        
        Args:
            duration: Recording duration in seconds
            output_path: Path to save WAV file
        """
        audio = pyaudio.PyAudio()
        
        try:
            stream = audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            print(f"🎤 Recording for {duration} seconds...")
            
            frames = []
            num_chunks = int(self.sample_rate / self.chunk_size * duration)
            
            for _ in range(num_chunks):
                data = stream.read(self.chunk_size)
                frames.append(data)
            
            stream.stop_stream()
            stream.close()
            
            # Save to file
            with wave.open(output_path, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
                wf.setframerate(self.sample_rate)
                wf.writeframes(b''.join(frames))
            
            print(f"✓ Saved to {output_path}")
            
        finally:
            audio.terminate()


# Singleton instance
_stt_instance: Optional[SpeechToText] = None


def get_stt(
    model: WhisperModel = WhisperModel.BASE,
    device: str = "cpu"
) -> SpeechToText:
    """Get or create STT instance"""
    global _stt_instance
    if _stt_instance is None:
        _stt_instance = SpeechToText(model, device)
    return _stt_instance

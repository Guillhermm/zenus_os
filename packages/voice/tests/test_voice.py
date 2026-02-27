"""
Basic tests for Zenus Voice package
"""

import pytest
from unittest.mock import Mock, MagicMock, patch


class TestVoiceOrchestrator:
    """Test VoiceOrchestrator"""
    
    def test_conversation_context(self):
        """Test conversation context management"""
        from zenus_voice.voice_orchestrator import ConversationContext, ConversationTurn
        
        context = ConversationContext(max_turns=3)
        
        # Add turns
        for i in range(5):
            turn = ConversationTurn(
                timestamp=f"2024-{i}",
                user_input=f"command {i}",
                assistant_response=f"response {i}",
                confidence=0.9,
                duration=1.0
            )
            context.add_turn(turn)
        
        # Should only keep last 3
        assert len(context.turns) == 3
        assert context.turns[0].user_input == "command 2"
        assert context.turns[-1].user_input == "command 4"
    
    def test_context_text_generation(self):
        """Test context text generation"""
        from zenus_voice.voice_orchestrator import ConversationContext, ConversationTurn
        
        context = ConversationContext()
        
        turn1 = ConversationTurn(
            timestamp="2024-1",
            user_input="list files",
            assistant_response="file1.txt file2.txt",
            confidence=0.9,
            duration=1.0
        )
        context.add_turn(turn1)
        
        context_text = context.get_context_text()
        assert "list files" in context_text
        assert "file1.txt" in context_text
    
    def test_context_clear(self):
        """Test clearing context"""
        from zenus_voice.voice_orchestrator import ConversationContext, ConversationTurn
        
        context = ConversationContext()
        context.add_turn(ConversationTurn(
            timestamp="2024-1",
            user_input="test",
            assistant_response="response",
            confidence=0.9,
            duration=1.0
        ))
        
        assert len(context.turns) == 1
        
        context.clear()
        assert len(context.turns) == 0


class TestTTSConfig:
    """Test TTS configuration"""
    
    def test_tts_config_creation(self):
        """Test creating TTS config"""
        from zenus_voice.tts import TTSConfig, Voice
        
        config = TTSConfig(
            voice=Voice.FEMALE_WARM,
            speed=1.2,
            volume=0.8
        )
        
        assert config.voice == Voice.FEMALE_WARM
        assert config.speed == 1.2
        assert config.volume == 0.8


class TestWhisperModel:
    """Test Whisper model enum"""
    
    def test_whisper_models(self):
        """Test Whisper model values"""
        from zenus_voice.stt import WhisperModel
        
        assert WhisperModel.TINY.value == "tiny"
        assert WhisperModel.BASE.value == "base"
        assert WhisperModel.SMALL.value == "small"
        assert WhisperModel.MEDIUM.value == "medium"
        assert WhisperModel.LARGE.value == "large"


class TestTranscriptionResult:
    """Test transcription result dataclass"""
    
    def test_transcription_result(self):
        """Test creating transcription result"""
        from zenus_voice.stt import TranscriptionResult
        
        result = TranscriptionResult(
            text="hello world",
            language="en",
            confidence=0.95,
            duration=1.5
        )
        
        assert result.text == "hello world"
        assert result.language == "en"
        assert result.confidence == 0.95
        assert result.duration == 1.5


class TestWakeWord:
    """Test wake word enum"""
    
    def test_wake_words(self):
        """Test wake word values"""
        from zenus_voice.wake_word import WakeWord
        
        assert WakeWord.HEY_ZENUS.value == "hey_zenus"
        assert WakeWord.COMPUTER.value == "computer"
        assert WakeWord.JARVIS.value == "jarvis"


class TestVoiceEnums:
    """Test voice-related enums"""
    
    def test_conversation_state(self):
        """Test conversation state enum"""
        from zenus_voice.voice_orchestrator import ConversationState
        
        assert ConversationState.IDLE.value == "idle"
        assert ConversationState.LISTENING.value == "listening"
        assert ConversationState.PROCESSING.value == "processing"
        assert ConversationState.SPEAKING.value == "speaking"
    
    def test_tts_engine(self):
        """Test TTS engine enum"""
        from zenus_voice.tts import TTSEngine
        
        assert TTSEngine.PIPER.value == "piper"
        assert TTSEngine.PYTTSX3.value == "pyttsx3"
    
    def test_voice_enum(self):
        """Test voice enum"""
        from zenus_voice.tts import Voice
        
        assert Voice.FEMALE_WARM.value == "en_US-lessac-medium"
        assert Voice.MALE_DEEP.value == "en_US-ryan-medium"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

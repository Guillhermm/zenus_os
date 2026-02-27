"""
Voice Orchestrator

Ties together STT, TTS, and Zenus orchestrator for voice control.
Handles conversational flow, interruptions, and context carryover.
"""

from typing import Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from zenus_voice.stt import SpeechToText, WhisperModel, TranscriptionResult
from zenus_voice.tts import TextToSpeech, TTSEngine, Voice, TTSConfig


class ConversationState(Enum):
    """Current state of voice conversation"""
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    INTERRUPTED = "interrupted"


@dataclass
class ConversationTurn:
    """A single turn in the conversation"""
    timestamp: str
    user_input: str
    assistant_response: str
    confidence: float
    duration: float


@dataclass
class ConversationContext:
    """Maintains conversation context for carryover"""
    turns: List[ConversationTurn] = field(default_factory=list)
    max_turns: int = 5  # Remember last 5 turns
    
    def add_turn(self, turn: ConversationTurn):
        """Add a turn to context"""
        self.turns.append(turn)
        
        # Keep only last N turns
        if len(self.turns) > self.max_turns:
            self.turns = self.turns[-self.max_turns:]
    
    def get_context_text(self) -> str:
        """Get formatted context for the LLM"""
        if not self.turns:
            return ""
        
        context_parts = ["Recent conversation:"]
        for turn in self.turns[-3:]:  # Last 3 turns
            context_parts.append(f"User: {turn.user_input}")
            context_parts.append(f"Assistant: {turn.assistant_response}")
        
        return "\n".join(context_parts)
    
    def clear(self):
        """Clear conversation context"""
        self.turns.clear()


class VoiceOrchestrator:
    """
    Main voice interface orchestrator
    
    Features:
    - Hands-free voice commands
    - Natural interruptions
    - Context carryover between commands
    - Conversational responses
    """
    
    def __init__(
        self,
        zenus_orchestrator,
        stt_model: WhisperModel = WhisperModel.BASE,
        tts_engine: TTSEngine = TTSEngine.PIPER,
        tts_voice: Voice = Voice.FEMALE_WARM,
        device: str = "cpu"
    ):
        """
        Args:
            zenus_orchestrator: Zenus Orchestrator instance
            stt_model: Whisper model size
            tts_engine: TTS engine to use
            tts_voice: Voice profile
            device: "cpu" or "cuda"
        """
        self.zenus = zenus_orchestrator
        
        # Initialize STT and TTS
        print("Initializing voice interface...")
        self.stt = SpeechToText(stt_model, device)
        self.tts = TextToSpeech(tts_engine, tts_voice)
        print("✓ Voice interface ready")
        
        # Conversation management
        self.context = ConversationContext()
        self.state = ConversationState.IDLE
        
        # Configuration
        self.use_voice_responses = True
        self.tts_config = TTSConfig(voice=tts_voice, speed=1.1)
        
        # Interruption handling
        self.interrupt_requested = False
    
    def listen_and_execute(self, use_context: bool = True) -> Optional[str]:
        """
        Listen for voice command and execute it
        
        Args:
            use_context: Use conversation context for better understanding
        
        Returns:
            Result text (or None if interrupted)
        """
        try:
            # Update state
            self.state = ConversationState.LISTENING
            
            # Listen for speech
            transcription = self.stt.listen_and_transcribe(
                on_speech_start=self._on_speech_start,
                on_speech_end=self._on_speech_end
            )
            
            if not transcription.text:
                self._respond("I didn't catch that. Could you repeat?")
                return None
            
            user_input = transcription.text
            print(f"\n🗣️  You said: {user_input}")
            
            # Check for special commands
            if self._handle_special_command(user_input):
                return None
            
            # Update state
            self.state = ConversationState.PROCESSING
            
            # Build enhanced input with context
            if use_context and self.context.turns:
                context_text = self.context.get_context_text()
                enhanced_input = f"{context_text}\n\nUser: {user_input}"
            else:
                enhanced_input = user_input
            
            # Execute command with Zenus
            result = self.zenus.execute_command(enhanced_input)
            
            # Prepare response
            response = self._make_conversational(result)
            
            # Record turn
            turn = ConversationTurn(
                timestamp=datetime.now().isoformat(),
                user_input=user_input,
                assistant_response=response,
                confidence=transcription.confidence,
                duration=transcription.duration
            )
            self.context.add_turn(turn)
            
            # Speak response
            if self.use_voice_responses:
                self._respond(response)
            else:
                print(f"\n💬 {response}")
            
            self.state = ConversationState.IDLE
            
            return result
            
        except KeyboardInterrupt:
            print("\n\n⏸️  Interrupted")
            self.state = ConversationState.INTERRUPTED
            return None
        except Exception as e:
            error_msg = f"Sorry, I encountered an error: {str(e)}"
            self._respond(error_msg)
            self.state = ConversationState.IDLE
            return None
    
    def continuous_mode(self, exit_phrases: Optional[List[str]] = None):
        """
        Run in continuous listening mode
        
        Keeps listening for commands until user says exit phrase.
        
        Args:
            exit_phrases: Phrases that exit continuous mode (default: ["stop listening", "goodbye", "exit"])
        """
        exit_phrases = exit_phrases or ["stop listening", "goodbye", "exit", "quit"]
        
        self._respond("Voice control activated. Say 'stop listening' to exit.")
        
        while True:
            try:
                result = self.listen_and_execute()
                
                # Check if user wants to exit
                if result and any(phrase in result.lower() for phrase in exit_phrases):
                    self._respond("Goodbye!")
                    break
                
            except KeyboardInterrupt:
                self._respond("Exiting voice control.")
                break
    
    def ask(self, question: str) -> Optional[str]:
        """
        Ask user a question and get voice response
        
        Args:
            question: Question to ask
        
        Returns:
            Transcribed response
        """
        self._respond(question)
        
        transcription = self.stt.listen_and_transcribe()
        
        if transcription.text:
            print(f"🗣️  You said: {transcription.text}")
            return transcription.text
        
        return None
    
    def confirm(self, prompt: str) -> bool:
        """
        Ask for yes/no confirmation
        
        Args:
            prompt: Confirmation prompt
        
        Returns:
            True for yes, False for no
        """
        response = self.ask(f"{prompt} (yes or no)")
        
        if response:
            response_lower = response.lower()
            return any(word in response_lower for word in ["yes", "yeah", "yep", "sure", "okay", "ok"])
        
        return False
    
    def _handle_special_command(self, text: str) -> bool:
        """
        Handle special voice commands
        
        Returns:
            True if handled, False otherwise
        """
        text_lower = text.lower()
        
        if "stop" in text_lower or "cancel" in text_lower or "nevermind" in text_lower:
            self._respond("Okay, cancelled.")
            return True
        
        if "clear context" in text_lower or "forget conversation" in text_lower:
            self.context.clear()
            self._respond("Context cleared.")
            return True
        
        if "repeat" in text_lower or "say that again" in text_lower:
            if self.context.turns:
                last_response = self.context.turns[-1].assistant_response
                self._respond(last_response)
            else:
                self._respond("Nothing to repeat.")
            return True
        
        return False
    
    def _make_conversational(self, result: str) -> str:
        """
        Make result text more conversational for speech
        
        Args:
            result: Raw result from Zenus
        
        Returns:
            Conversational response
        """
        # Remove technical jargon
        result = result.replace("✓", "Done.")
        result = result.replace("✗", "Failed.")
        result = result.replace("→", "then")
        
        # Add natural language
        if "successfully" in result.lower():
            return f"Alright, {result}"
        elif "error" in result.lower() or "failed" in result.lower():
            return f"Hmm, {result}"
        else:
            return result
    
    def _respond(self, text: str):
        """Speak response using TTS"""
        self.state = ConversationState.SPEAKING
        
        print(f"\n💬 {text}")
        
        if self.use_voice_responses:
            self.tts.speak(text, self.tts_config)
        
        self.state = ConversationState.IDLE
    
    def _on_speech_start(self):
        """Callback when speech starts"""
        print("🎤 Speech detected...")
    
    def _on_speech_end(self):
        """Callback when speech ends"""
        print("🎤 Processing...")
    
    def set_voice_responses(self, enabled: bool):
        """Enable or disable voice responses"""
        self.use_voice_responses = enabled
        if enabled:
            self._respond("Voice responses enabled")
        else:
            print("💬 Voice responses disabled (text only)")
    
    def set_voice(self, voice: Voice):
        """Change TTS voice"""
        self.tts_config.voice = voice
        self._respond(f"Voice changed to {voice.value}")
    
    def set_speed(self, speed: float):
        """Change TTS speed (0.5-2.0)"""
        self.tts_config.speed = max(0.5, min(2.0, speed))
        self._respond(f"Speed set to {speed}")


def create_voice_interface(zenus_orchestrator, **kwargs) -> VoiceOrchestrator:
    """
    Create voice interface for Zenus
    
    Args:
        zenus_orchestrator: Zenus Orchestrator instance
        **kwargs: Additional configuration (stt_model, tts_engine, etc.)
    
    Returns:
        VoiceOrchestrator instance
    """
    return VoiceOrchestrator(zenus_orchestrator, **kwargs)

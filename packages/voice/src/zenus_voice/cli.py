"""
CLI entry point for Zenus Voice
"""

import argparse
import sys
from zenus_voice import (
    create_voice_interface,
    WhisperModel,
    TTSEngine,
    Voice,
    WakeWord,
    create_wake_detector
)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Zenus Voice - Hands-free voice control"
    )
    
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Run in continuous listening mode"
    )
    
    parser.add_argument(
        "--wake-word",
        type=str,
        choices=["hey_zenus", "computer", "jarvis"],
        help="Enable wake word detection"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        choices=["tiny", "base", "small", "medium", "large"],
        default="base",
        help="Whisper model size (default: base)"
    )
    
    parser.add_argument(
        "--voice",
        type=str,
        choices=["female_warm", "female_neutral", "male_deep", "male_neutral"],
        default="female_warm",
        help="TTS voice (default: female_warm)"
    )
    
    parser.add_argument(
        "--speed",
        type=float,
        default=1.0,
        help="TTS speed (0.5-2.0, default: 1.0)"
    )
    
    parser.add_argument(
        "--no-voice-responses",
        action="store_true",
        help="Disable voice responses (text only)"
    )
    
    parser.add_argument(
        "--device",
        type=str,
        choices=["cpu", "cuda"],
        default="cpu",
        help="Device for Whisper (cpu or cuda)"
    )
    
    args = parser.parse_args()
    
    print("🎤 Zenus Voice")
    print("=" * 40)
    
    try:
        # Import Zenus orchestrator
        from zenus_core.cli.orchestrator import Orchestrator
        
        # Create orchestrator
        print("Initializing Zenus...")
        orch = Orchestrator()
        
        # Map arguments to enums
        model_map = {
            "tiny": WhisperModel.TINY,
            "base": WhisperModel.BASE,
            "small": WhisperModel.SMALL,
            "medium": WhisperModel.MEDIUM,
            "large": WhisperModel.LARGE
        }
        
        voice_map = {
            "female_warm": Voice.FEMALE_WARM,
            "female_neutral": Voice.FEMALE_NEUTRAL,
            "male_deep": Voice.MALE_DEEP,
            "male_neutral": Voice.MALE_NEUTRAL
        }
        
        # Create voice interface
        voice = create_voice_interface(
            orch,
            stt_model=model_map[args.model],
            tts_engine=TTSEngine.PIPER,
            tts_voice=voice_map[args.voice],
            device=args.device
        )
        
        # Configure voice
        voice.set_speed(args.speed)
        if args.no_voice_responses:
            voice.set_voice_responses(False)
        
        print("\n✓ Voice interface ready")
        print("=" * 40)
        
        # Wake word mode
        if args.wake_word:
            wake_word_map = {
                "hey_zenus": WakeWord.HEY_ZENUS,
                "computer": WakeWord.COMPUTER,
                "jarvis": WakeWord.JARVIS
            }
            
            def on_wake():
                voice.listen_and_execute()
            
            detector = create_wake_detector(
                use_porcupine=False,  # Use simple detector by default
                wake_word=wake_word_map[args.wake_word],
                on_wake=on_wake
            )
            
            detector.start_listening()
        
        # Continuous mode
        elif args.continuous:
            voice.continuous_mode()
        
        # Single command mode
        else:
            print("\nSpeak your command...")
            voice.listen_and_execute()
        
    except KeyboardInterrupt:
        print("\n\nExiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

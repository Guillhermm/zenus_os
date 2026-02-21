"""
Special CLI Commands

Built-in commands that don't go through intent translation.
"""

import sys
from memory.session_memory import SessionMemory
from memory.world_model import WorldModel
from memory.intent_history import IntentHistory


def handle_status_command(orchestrator):
    """Show Zenus status"""
    print("\n╔════════════════════════════════════╗")
    print("║        Zenus OS Status             ║")
    print("╚════════════════════════════════════╝\n")
    
    # Session stats
    if orchestrator.use_memory:
        session_stats = orchestrator.session_memory.get_session_stats()
        print(f"Session Duration: {session_stats['session_duration_seconds']:.0f}s")
        print(f"Commands Executed: {session_stats['total_intents']}")
        print(f"Context References: {session_stats['context_refs']}")
        print()
    
    # World model stats
    if orchestrator.use_memory:
        try:
            world_summary = orchestrator.world_model.get_summary()
            print(world_summary)
        except Exception as e:
            print(f"World model: Error loading ({e})")
        print()
    
    # LLM backend
    import os
    backend = os.getenv("ZENUS_LLM", "openai")
    print(f"LLM Backend: {backend}")
    
    if backend == "ollama":
        model = os.getenv("OLLAMA_MODEL", "phi3:mini")
        print(f"Model: {model}")
    
    print()


def handle_memory_command(orchestrator, subcommand: str = "stats"):
    """Memory management commands"""
    
    if not orchestrator.use_memory:
        print("Memory is disabled")
        return
    
    if subcommand == "stats":
        session_stats = orchestrator.session_memory.get_session_stats()
        print(f"\n📊 Memory Statistics:\n")
        print(f"Session:")
        print(f"  Intents: {session_stats['total_intents']}")
        print(f"  References: {session_stats['context_refs']}")
        print(f"  Duration: {session_stats['session_duration_seconds']:.0f}s")
        print()
        
        frequent = orchestrator.world_model.get_frequent_paths(5)
        if frequent:
            print(f"Frequent Paths:")
            for path in frequent:
                print(f"  - {path}")
        print()
    
    elif subcommand == "clear":
        confirm = input("Clear session memory? (y/n): ")
        if confirm.lower() == 'y':
            orchestrator.session_memory.clear()
            print("✓ Session memory cleared")
    
    else:
        print(f"Unknown memory command: {subcommand}")
        print("Available: stats, clear")


def handle_update_command():
    """Update Zenus OS"""
    import subprocess
    
    print("\n🔄 Updating Zenus OS...")
    print()
    
    # Update git repo
    print("Pulling latest changes...")
    try:
        subprocess.run(["git", "pull"], check=True)
    except:
        print("⚠️  Not a git repository, skipping git pull")
    
    # Update dependencies
    print("Updating Python dependencies...")
    subprocess.run(
        ["pip", "install", "-q", "--upgrade", "-r", "requirements.txt"],
        check=True
    )
    
    print()
    print("✓ Update complete!")
    print("  Restart Zenus to apply changes")
    print()

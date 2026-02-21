"""
Special CLI Commands

Built-in commands that don't go through intent translation.
"""

import sys
from zenus_core.memory.session_memory import SessionMemory
from zenus_core.memory.world_model import WorldModel
from zenus_core.memory.intent_history import IntentHistory


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
    import os
    
    print("\n🔄 Updating Zenus OS...")
    print()
    
    # Update git repo
    print("Pulling latest changes...")
    try:
        result = subprocess.run(["git", "pull"], capture_output=True, text=True)
        print(result.stdout.strip())
    except Exception as e:
        print(f"⚠️  Git pull failed: {e}")
    
    # Update dependencies via Poetry
    print("\nUpdating Python dependencies...")
    try:
        # Get the project root (2 levels up from cli package)
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
        
        # Update core package
        core_dir = os.path.join(project_root, "packages/core")
        if os.path.exists(core_dir):
            print("  → Updating zenus-core...")
            subprocess.run(["poetry", "install"], cwd=core_dir, check=True, capture_output=True)
        
        # Update CLI package
        cli_dir = os.path.join(project_root, "packages/cli")
        if os.path.exists(cli_dir):
            print("  → Updating zenus-cli...")
            subprocess.run(["poetry", "install"], cwd=cli_dir, check=True, capture_output=True)
        
        print("✓ Dependencies updated")
    except Exception as e:
        print(f"⚠️  Dependency update failed: {e}")
    
    print("\n✓ Update complete!")
    print("  Restart Zenus to apply changes")
    print()

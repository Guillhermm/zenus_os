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
        # Get the project root (2 levels up from core package)
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


def handle_explain_command(orchestrator, arg: str = "last"):
    """Explain a past execution"""
    from zenus_core.cli.explainability import get_explainability_dashboard
    
    dashboard = get_explainability_dashboard()
    
    if arg == "last":
        dashboard.explain_last(verbose=True)
    elif arg == "history":
        dashboard.show_history(limit=20)
    elif arg.isdigit():
        index = -int(arg)
        dashboard.explain_execution(index, verbose=True)
    else:
        print(f"Unknown explain command: {arg}")
        print("Usage: explain [last|history|N]")



def check_and_suggest_patterns(orchestrator):
    """
    Check for patterns and suggest automation
    
    Should be called periodically in interactive mode
    (e.g., every 10 commands)
    """
    from zenus_core.brain.pattern_detector import get_pattern_detector
    from zenus_core.brain.pattern_memory import get_pattern_memory
    from zenus_core.memory.intent_history import IntentHistory
    from rich.console import Console
    from rich.panel import Panel
    
    console = Console()
    
    # Get pattern detector and memory
    detector = get_pattern_detector()
    memory = get_pattern_memory()
    
    # Get execution history
    history = IntentHistory()
    
    try:
        # Load history records
        history_records = []
        for record in history.history:
            history_records.append({
                'user_input': record.get('user_input', ''),
                'timestamp': record.get('timestamp', ''),
                'intent': record.get('intent', {})
            })
        
        # Detect patterns
        patterns = detector.detect_patterns(history_records, lookback_days=30)
        
        # Filter to high-confidence patterns we haven't suggested yet
        high_confidence = []
        for p in patterns:
            if p.confidence >= 0.8:
                # Create unique key for this pattern
                pattern_key = f"{p.pattern_type}:{p.description[:50]}"
                if not memory.has_suggested(pattern_key):
                    high_confidence.append((p, pattern_key))
        
        if not high_confidence:
            return
        
        # Show first pattern suggestion
        pattern, pattern_key = high_confidence[0]
        
        # Mark as suggested (so we don't repeat)
        memory.mark_suggested(pattern_key)
        
        if pattern.pattern_type == 'recurring' and pattern.suggested_cron:
            console.print()
            console.print(Panel.fit(
                f"[cyan]💡 Pattern Detected[/cyan]\n\n"
                f"I noticed {pattern.description}.\n\n"
                f"Would you like me to set up an automatic {pattern.frequency} task?",
                border_style="cyan",
                title="[bold]Suggestion[/bold]"
            ))
            
            choice = input("\n[Y]es / [N]o / [S]how more: ").strip().lower()
            
            if choice == 'y':
                # Create cron job
                cmd = pattern.commands[-1] if pattern.commands else pattern.description
                
                console.print(f"\n[green]Creating cron job:[/green]")
                console.print(f"  Schedule: {pattern.suggested_cron}")
                console.print(f"  Command: {cmd}")
                console.print(f"\n[dim]Note: Cron integration coming soon![/dim]")
                console.print(f"[dim]For now, you can manually add this to your crontab.[/dim]")
            
            elif choice == 's':
                # Show all patterns
                console.print("\n[cyan]Detected Patterns:[/cyan]\n")
                for i, (p, _) in enumerate(high_confidence[:5], 1):
                    console.print(f"{i}. {p.description}")
                    console.print(f"   [dim]Confidence: {p.confidence:.0%}, Occurrences: {p.occurrences}[/dim]")
                    if p.suggested_cron:
                        console.print(f"   [dim]Cron: {p.suggested_cron}[/dim]")
                    console.print()
    
    except Exception as e:
        # Silently fail - pattern detection is optional
        pass

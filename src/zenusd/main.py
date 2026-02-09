"""
Zenus OS - Main Entry Point

CLI-first, agent-driven operating layer
Routes commands through: CLI → Intent → Plan → Execute
"""

import sys
from cli.router import CommandRouter
from cli.orchestrator import Orchestrator


def main():
    """Main entry point for Zenus OS"""
    
    router = CommandRouter()
    orchestrator = Orchestrator()
    
    # Parse CLI arguments (skip program name)
    args = sys.argv[1:]
    command = router.parse(args)
    
    # Route to appropriate handler
    if command.mode == "help":
        router.show_help()
    
    elif command.mode == "version":
        router.show_version()
    
    elif command.mode == "interactive":
        orchestrator.interactive_shell()
    
    elif command.mode == "direct":
        # Direct execution (auto-confirm for non-interactive use)
        result = orchestrator.process(command.input_text, auto_confirm=True)
        if result:
            print(result)


if __name__ == "__main__":
    main()

"""
Zenus OS - Main Entry Point

CLI-first, agent-driven operating layer
Routes commands through: CLI to Intent to Plan to Execute
"""

import sys
from cli.router import CommandRouter
from cli.orchestrator import Orchestrator, OrchestratorError


def main():
    """Main entry point for Zenus OS"""
    
    router = CommandRouter()
    orchestrator = Orchestrator()
    
    # Parse CLI arguments (skip program name)
    args = sys.argv[1:]
    command = router.parse(args)
    
    # Route to appropriate handler
    try:
        if command.mode == "help":
            router.show_help()
        
        elif command.mode == "version":
            router.show_version()
        
        elif command.mode == "interactive":
            orchestrator.interactive_shell()
        
        elif command.mode == "direct":
            # Direct execution
            dry_run = command.flags.get("dry_run", False)
            result = orchestrator.execute_command(
                command.input_text, 
                dry_run=dry_run
            )
            if result:
                print(result)
    
    except OrchestratorError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted")
        sys.exit(130)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

"""
CLI Command Router

Responsible for:
- Parsing CLI arguments
- Routing to appropriate handlers (interactive/direct/help)
- Maintaining clear separation between parse, intent, execute
"""

import sys
from typing import Optional, List
from dataclasses import dataclass, field


@dataclass
class CLICommand:
    """Represents a parsed CLI command"""
    mode: str  # 'interactive', 'direct', 'help', 'version'
    input_text: Optional[str] = None
    flags: dict = field(default_factory=dict)


class CommandRouter:
    """Routes CLI invocations to appropriate handlers"""

    def __init__(self):
        self.version = "0.1.0-alpha"

    def parse(self, args: List[str]) -> CLICommand:
        """
        Parse command line arguments into a CLICommand
        
        Modes:
        - No args or 'shell' -> interactive REPL
        - 'help' / '--help' / '-h' -> help message
        - 'version' / '--version' / '-v' -> version info
        - '--dry-run <text>' -> show plan but do not execute
        - Direct text -> immediate intent execution
        """
        
        # Check for flags
        dry_run = False
        filtered_args = []
        
        for arg in args:
            if arg == "--dry-run":
                dry_run = True
            else:
                filtered_args.append(arg)
        
        args = filtered_args
        
        if not args or args[0] == "shell":
            return CLICommand(mode="interactive")
        
        if args[0] in ("help", "--help", "-h"):
            return CLICommand(mode="help")
        
        if args[0] in ("version", "--version", "-v"):
            return CLICommand(mode="version")
        
        # Everything else is a direct command
        input_text = " ".join(args)
        return CLICommand(
            mode="direct", 
            input_text=input_text,
            flags={"dry_run": dry_run}
        )

    def show_help(self):
        """Display help message"""
        help_text = f"""
Zenus OS v{self.version}
A developer-centric, CLI-first, agent-driven operating layer

USAGE:
    zenus [OPTIONS] [COMMAND]

COMMANDS:
    shell               Start interactive REPL (default)
    help                Show this help message
    version             Show version information
    <direct command>    Execute command immediately

OPTIONS:
    --dry-run           Show plan but do not execute

EXAMPLES:
    zenus                                    # Start interactive shell
    zenus shell                              # Same as above
    zenus "list files in ~/Documents"        # Direct execution
    zenus organize my downloads by type      # Direct execution (no quotes)
    zenus --dry-run "delete all tmp files"   # Preview without executing

INTERACTIVE MODE:
    zenus > --dry-run organize my downloads  # Preview in shell mode
    zenus > organize my downloads            # Execute in shell mode

ENVIRONMENT:
    ZENUS_LLM           LLM backend: 'openai' (default) or 'deepseek'
    OPENAI_API_KEY      OpenAI API key
    DEEPSEEK_API_KEY    DeepSeek API key

LOGS:
    Audit logs: ~/.zenus/logs/

For more information, visit: https://github.com/your-repo/zenus_os
        """.strip()
        print(help_text)

    def show_version(self):
        """Display version information"""
        print(f"Zenus OS v{self.version}")

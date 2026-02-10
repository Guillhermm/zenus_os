"""
Command Orchestrator

High-level orchestration of:
- Intent translation
- Memory management  
- Plan execution
- Audit logging
"""

from typing import Optional
from brain.llm.factory import get_llm
from brain.planner import execute_plan
from brain.adaptive_planner import AdaptivePlanner
from brain.sandboxed_planner import SandboxedAdaptivePlanner
from brain.llm.schemas import IntentIR
from audit.logger import get_logger
from memory.session_memory import SessionMemory
from memory.world_model import WorldModel
from memory.intent_history import IntentHistory
from cli.progress import ProgressIndicator
from cli.feedback import FeedbackGenerator
from cli.explain import ExplainMode
from cli.formatter import (
    print_success, print_error, print_goal, 
    print_step, console
)


class IntentTranslationError(Exception):
    """Raised when LLM fails to translate user intent"""
    pass


class OrchestratorError(Exception):
    """Raised for orchestration failures"""
    pass


class Orchestrator:
    """
    Orchestrates the full Zenus pipeline
    
    Responsibilities:
    1. Translate natural language → Intent IR
    2. Build context from memory
    3. Execute plan (with retry if adaptive)
    4. Update memory with results
    5. Log everything for audit
    """
    
    def __init__(
        self, 
        adaptive: bool = True, 
        use_memory: bool = True,
        use_sandbox: bool = True,
        show_progress: bool = True
    ):
        self.llm = get_llm()
        self.logger = get_logger()
        self.adaptive = adaptive
        self.use_memory = use_memory
        self.use_sandbox = use_sandbox
        self.show_progress = show_progress
        
        if adaptive:
            if use_sandbox:
                # Use sandboxed adaptive planner
                self.adaptive_planner = SandboxedAdaptivePlanner(self.logger)
            else:
                # Use basic adaptive planner
                self.adaptive_planner = AdaptivePlanner(self.logger)
        
        if use_memory:
            self.session_memory = SessionMemory()
            self.world_model = WorldModel()
            self.intent_history = IntentHistory()
        
        self.progress = ProgressIndicator() if show_progress else None
        self.feedback = FeedbackGenerator(self.llm)
        
        # Semantic search for command history (lazy import)
        self.semantic_search = None
        try:
            from memory.semantic_search import SemanticSearch
            self.semantic_search = SemanticSearch()
        except ImportError as e:
            # sentence-transformers not installed, semantic search disabled
            pass
        except Exception as e:
            # Other error, log it
            self.logger.log_error(f"Semantic search unavailable: {e}")
        
        self.explain_mode = ExplainMode(self.semantic_search)
    
    def execute_command(
        self, 
        user_input: str, 
        dry_run: bool = False,
        explain: bool = False
    ) -> str:
        """
        Execute a natural language command
        
        Args:
            user_input: Natural language command
            dry_run: If True, show plan without executing
            explain: If True, show detailed explanation before executing
        
        Returns:
            Human-readable result
        """
        try:
            # Step 1: Build context from memory
            context = ""
            if self.use_memory:
                context = self._build_context(user_input)
            
            # Step 2: Translate intent with context
            try:
                # Show thinking indicator
                if self.progress:
                    with self.progress.thinking("Understanding your request"):
                        if context:
                            enhanced_input = f"{user_input}\n{context}"
                            intent = self.llm.translate_intent(enhanced_input)
                        else:
                            intent = self.llm.translate_intent(user_input)
                else:
                    if context:
                        enhanced_input = f"{user_input}\n{context}"
                        intent = self.llm.translate_intent(enhanced_input)
                    else:
                        intent = self.llm.translate_intent(user_input)
            except Exception as e:
                error_msg = f"Failed to understand command: {str(e)}"
                self.logger.log_error(error_msg, {"user_input": user_input})
                raise IntentTranslationError(error_msg) from e
            
            # Step 3: Show explanation if requested
            if explain:
                self.explain_mode.explain(user_input, intent)
                
                # Ask for confirmation
                if not self.explain_mode.confirm():
                    return "Execution cancelled by user"
            
            # Step 4: Log intent
            self.logger.log_intent(user_input, intent)
            
            # Step 5: Store context in memory
            if self.use_memory:
                self.session_memory.add_intent(intent)
            
            # Step 6: Execute plan
            if dry_run:
                return self._format_dry_run(intent)
            
            # Show goal
            print_goal(intent.goal)
            
            execution_success = False
            step_results = []
            
            if self.adaptive:
                step_results = self.adaptive_planner.execute_with_retry(
                    intent, max_retries=2
                )
                execution_success = True
            else:
                step_results = execute_plan(intent, self.logger)
                execution_success = True
            
            # Print steps with formatting
            for i, (step, result) in enumerate(zip(intent.steps, step_results), 1):
                print_step(i, step.tool, step.action, step.risk, result)
            
            # Step 7: Update memory with results
            if self.use_memory:
                # Extract paths from results
                for result in step_results:
                    if "path" in str(result).lower():
                        # Simple heuristic: extract file paths
                        words = str(result).split()
                        for word in words:
                            if "/" in word and not word.startswith("http"):
                                self.world_model.update_path_frequency(word)
                
                self.intent_history.record(user_input, intent, step_results)
            
            # Step 8: Add to semantic search
            if self.semantic_search and execution_success:
                try:
                    self.semantic_search.add_command(
                        user_input=user_input,
                        goal=intent.goal,
                        steps=[s.model_dump() for s in intent.steps],
                        success=True
                    )
                except Exception as e:
                    # Non-critical, just log
                    self.logger.log_error(f"Failed to add to semantic search: {e}")
            
            print_success("Plan executed successfully")
            return "Plan executed successfully"
        
        except IntentTranslationError as e:
            error_msg = str(e)
            self.logger.log_error(error_msg, {"user_input": user_input})
            
            # Record failure in semantic search
            if self.semantic_search:
                try:
                    self.semantic_search.add_command(
                        user_input=user_input,
                        goal="Translation failed",
                        steps=[],
                        success=False
                    )
                except:
                    pass
            
            print_error(f"Failed to understand command: {error_msg}")
            return f"Error: {error_msg}"
        
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.logger.log_error(error_msg, {"user_input": user_input})
            
            # Record failure in semantic search
            if self.semantic_search:
                try:
                    self.semantic_search.add_command(
                        user_input=user_input,
                        goal="Execution failed",
                        steps=[],
                        success=False
                    )
                except:
                    pass
            
            print_error(error_msg)
            return error_msg
    
    def _build_context(self, user_input: str) -> str:
        """Build context string from memory"""
        context_parts = []
        
        # Recent intents
        summary = self.session_memory.get_context_summary(max_intents=3)
        if summary:
            context_parts.append(f"Recent activity: {summary}")
        
        # Frequent paths (if query mentions files/directories)
        if any(word in user_input.lower() for word in ["file", "folder", "directory", "path"]):
            frequent_paths = self.world_model.get_frequent_paths(limit=5)
            if frequent_paths:
                context_parts.append(f"Frequent paths: {', '.join(frequent_paths)}")
        
        return "\n".join(context_parts)
    
    def _format_dry_run(self, intent: IntentIR) -> str:
        """Format dry-run output"""
        output = [f"DRY RUN - Would execute: {intent.goal}\n"]
        
        for i, step in enumerate(intent.steps, 1):
            output.append(
                f"{i}. {step.tool}.{step.action}({step.args}) [risk={step.risk}]"
            )
        
        return "\n".join(output)
    
    def interactive_shell(self):
        """Run interactive REPL mode"""
        # Enable readline for command history and arrow keys
        try:
            import readline
            import os
            
            # Set up history file
            history_file = os.path.expanduser("~/.zenus/history.txt")
            os.makedirs(os.path.dirname(history_file), exist_ok=True)
            
            # Load history if exists
            try:
                readline.read_history_file(history_file)
            except FileNotFoundError:
                pass
            
            # Set history size
            readline.set_history_length(1000)
            
            # Save history on exit
            import atexit
            atexit.register(readline.write_history_file, history_file)
            
        except ImportError:
            # readline not available (Windows without pyreadline)
            pass
        
        console.print("\n[bold cyan]Zenus OS Interactive Shell[/bold cyan]")
        console.print("Type 'exit' or 'quit' to exit")
        console.print("Special commands: status, memory, update, explain")
        console.print("Use ↑↓ arrows for command history\n")
        
        while True:
            try:
                user_input = input("\nzenus > ").strip()
                
                if not user_input:
                    continue
                
                if user_input in ("exit", "quit"):
                    console.print("[dim]Goodbye![/dim]")
                    break
                
                # Handle special commands
                if user_input == "status":
                    from cli.commands import handle_status_command
                    handle_status_command(self)
                    continue
                
                if user_input.startswith("memory"):
                    from cli.commands import handle_memory_command
                    parts = user_input.split()
                    subcommand = parts[1] if len(parts) > 1 else "stats"
                    handle_memory_command(self, subcommand)
                    continue
                
                if user_input == "update":
                    from cli.commands import handle_update_command
                    handle_update_command()
                    continue
                
                # Check for --explain flag
                explain = False
                if "--explain" in user_input:
                    explain = True
                    user_input = user_input.replace("--explain", "").strip()
                
                # Execute command
                result = self.execute_command(user_input, explain=explain)
                
            except KeyboardInterrupt:
                console.print("\n[dim]Use 'exit' to quit[/dim]")
                continue
            except EOFError:
                console.print("\n[dim]Goodbye![/dim]")
                break
            except Exception as e:
                print_error(f"Shell error: {e}")

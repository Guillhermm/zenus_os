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
from brain.task_analyzer import TaskAnalyzer
from brain.failure_analyzer import FailureAnalyzer
from brain.dependency_analyzer import DependencyAnalyzer
from brain.llm.schemas import IntentIR
from memory.action_tracker import get_action_tracker
from execution.parallel_executor import get_parallel_executor
from audit.logger import get_logger
from memory.session_memory import SessionMemory
from memory.world_model import WorldModel
from memory.intent_history import IntentHistory
from context.context_manager import get_context_manager
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
        show_progress: bool = True,
        enable_parallel: bool = True
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
        self.failure_analyzer = FailureAnalyzer()
        self.action_tracker = get_action_tracker()
        self.enable_parallel = enable_parallel
        self.dependency_analyzer = DependencyAnalyzer() if enable_parallel else None
        self.parallel_executor = get_parallel_executor() if enable_parallel else None
        
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
        
        # Task analyzer for auto-detecting iterative vs one-shot
        self.task_analyzer = TaskAnalyzer(self.llm)
    
    def execute_command(
        self, 
        user_input: str, 
        dry_run: bool = False,
        explain: bool = False,
        force_oneshot: bool = False
    ) -> str:
        """
        Execute a natural language command
        
        Automatically detects if task needs iterative execution.
        
        Args:
            user_input: Natural language command
            dry_run: If True, show plan without executing
            explain: If True, show detailed explanation before executing
            force_oneshot: If True, skip iterative detection and use one-shot
        
        Returns:
            Human-readable result
        """
        try:
            # Step 0: Analyze task complexity (auto-detect iterative need)
            if not force_oneshot:
                task_complexity = self.task_analyzer.analyze(user_input)
                
                if task_complexity.needs_iteration:
                    # Automatically use iterative mode for complex tasks
                    console.print(f"[dim]Detected complex task (confidence: {task_complexity.confidence:.0%})[/dim]")
                    console.print(f"[dim]Using iterative execution ({task_complexity.reasoning})[/dim]\n")
                    return self.execute_iterative(
                        user_input,
                        max_iterations=task_complexity.estimated_steps * 2,  # Dynamic max
                        dry_run=dry_run
                    )
            
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
            
            # Step 2.5: Analyze for potential failures (learning from past mistakes)
            pre_analysis = self.failure_analyzer.analyze_before_execution(user_input, intent)
            
            if pre_analysis["has_warnings"] and not dry_run:
                console.print("\n[yellow]📚 Learning from past experience:[/yellow]")
                
                # Show warnings
                for warning in pre_analysis["warnings"]:
                    console.print(f"  {warning}")
                
                # Show suggestions
                if pre_analysis["suggestions"]:
                    console.print("\n[cyan]💡 Suggestions based on past failures:[/cyan]")
                    for suggestion in pre_analysis["suggestions"]:
                        console.print(f"  • {suggestion}")
                
                # Show success probability
                prob = pre_analysis["success_probability"]
                if prob < 0.7:
                    console.print(f"\n  [yellow]Success probability: {prob:.0%}[/yellow]")
                    
                    if not explain:  # If not already in explain mode, ask for confirmation
                        response = console.input("\n[bold]Proceed anyway?[/bold] (y/n): ")
                        if response.lower() not in ('y', 'yes'):
                            return "Execution cancelled due to high failure risk"
            
            # Auto-explain high-risk operations
            if not explain:
                max_risk = max([step.risk for step in intent.steps])
                if max_risk >= 3 and not dry_run:
                    console.print("\n[yellow]⚠️  High-risk operation detected[/yellow]")
                    from cli.explainer import get_explainer
                    explainer = get_explainer()
                    explainer.explain_intent(user_input, intent)
                    
                    if not explainer.confirm("This operation is destructive. Proceed?"):
                        return "Execution cancelled by user (high-risk operation)"
            
            # Step 3: Show explanation if requested
            if explain:
                from cli.explainer import get_explainer
                explainer = get_explainer()
                
                # Show detailed explanation
                explainer.explain_intent(user_input, intent)
                
                # Show environmental context
                ctx_mgr = get_context_manager()
                explainer.explain_context(ctx_mgr.get_full_context())
                
                # Ask for confirmation
                if not explainer.confirm():
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
            
            # Start transaction for rollback capability
            transaction_id = self.action_tracker.start_transaction(user_input, intent.goal)
            
            execution_success = False
            step_results = []
            
            try:
                if self.adaptive:
                    step_results = self.adaptive_planner.execute_with_retry(
                        intent, max_retries=2
                    )
                    execution_success = True
                else:
                    step_results = execute_plan(intent, self.logger)
                    execution_success = True
                
                # Track each action for rollback
                for step, result in zip(intent.steps, step_results):
                    self.action_tracker.track_action(
                        tool=step.tool,
                        operation=step.action,
                        params=step.args,
                        result=result,
                        transaction_id=transaction_id
                    )
                
                # End transaction successfully
                self.action_tracker.end_transaction(transaction_id, "completed")
            
            except Exception as e:
                # End transaction with failure status
                self.action_tracker.end_transaction(transaction_id, "failed")
                raise
            
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
            
            # Analyze failure and provide intelligent suggestions
            ctx_mgr = get_context_manager()
            failure_analysis = self.failure_analyzer.analyze_failure(
                user_input=user_input,
                intent_goal=intent.goal if 'intent' in locals() else "Unknown",
                tool="orchestrator",
                error_message=str(e),
                context=ctx_mgr.get_full_context()
            )
            
            # Show intelligent error message
            console.print(f"\n[red]❌ Execution failed:[/red] {error_msg}")
            
            # Show recovery suggestions
            if failure_analysis["suggestions"]:
                console.print("\n[cyan]💡 Suggestions to fix this:[/cyan]")
                for i, suggestion in enumerate(failure_analysis["suggestions"], 1):
                    console.print(f"  {i}. {suggestion}")
            
            # Show similar failures
            if failure_analysis["is_recurring"]:
                console.print("\n[yellow]⚠️  This failure has occurred before[/yellow]")
                console.print("  Consider reviewing the suggestions above carefully")
            
            # Show recovery plan if available
            if failure_analysis["similar_failures"]:
                from cli.formatter import console
                most_recent = failure_analysis["similar_failures"][0]
                recovery_plan = self.failure_analyzer.generate_recovery_plan(most_recent)
                if recovery_plan:
                    console.print("\n[cyan]📋 Recovery plan:[/cyan]")
                    console.print(f"  {recovery_plan}")
            
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
    
    def execute_iterative(
        self,
        user_input: str,
        max_iterations: int = 10,
        dry_run: bool = False
    ) -> str:
        """
        Execute a command with iterative ReAct loop
        
        This method implements the ReAct (Reasoning + Acting) pattern:
        1. Plan based on current context
        2. Execute plan
        3. Observe results
        4. Check if goal achieved
        5. If not, re-plan with new observations
        6. Repeat until goal achieved or max iterations
        
        Args:
            user_input: Natural language command
            max_iterations: Maximum iterations to prevent infinite loops
            dry_run: If True, show plan without executing
        
        Returns:
            Human-readable result
        """
        from brain.goal_tracker import GoalTracker
        
        # Initialize goal tracker
        goal_tracker = GoalTracker(max_iterations=max_iterations)
        
        # Accumulator for observations
        all_observations = []
        
        # Initial context from memory
        context = ""
        if self.use_memory:
            context = self._build_context(user_input)
        
        print_goal(f"Starting iterative execution: {user_input}")
        console.print(f"[dim]Max iterations: {max_iterations}[/dim]\n")
        
        iteration = 0
        goal_achieved = False
        
        try:
            while not goal_achieved and iteration < max_iterations:
                iteration += 1
                console.print(f"\n[bold cyan]═══ Iteration {iteration}/{max_iterations} ═══[/bold cyan]")
                
                # Build enhanced input with context and observations
                enhanced_input = user_input
                if context:
                    enhanced_input += f"\n\nContext: {context}"
                if all_observations:
                    obs_text = "\n".join([f"- {obs}" for obs in all_observations[-5:]])  # Last 5 observations
                    enhanced_input += f"\n\nPrevious observations:\n{obs_text}"
                
                # Step 1: Translate intent with accumulated context
                if self.progress:
                    with self.progress.thinking("Planning next steps"):
                        intent = self.llm.translate_intent(enhanced_input)
                else:
                    intent = self.llm.translate_intent(enhanced_input)
                
                # Log intent
                self.logger.log_intent(user_input, intent)
                
                # Show goal for this iteration
                console.print(f"[yellow]→ Goal:[/yellow] {intent.goal}")
                
                if dry_run:
                    console.print(self._format_dry_run(intent))
                    continue
                
                # Step 2: Execute plan
                step_results = []
                iteration_observations = []
                
                if self.adaptive:
                    step_results = self.adaptive_planner.execute_with_retry(
                        intent, max_retries=2
                    )
                else:
                    step_results = execute_plan(intent, self.logger)
                
                # Step 3: Collect observations
                for i, (step, result) in enumerate(zip(intent.steps, step_results), 1):
                    print_step(i, step.tool, step.action, step.risk, result)
                    
                    # Create observation
                    observation = f"{step.tool}.{step.action} → {str(result)[:200]}"  # Truncate long results
                    iteration_observations.append(observation)
                
                # Add to all observations
                all_observations.extend(iteration_observations)
                
                # Step 4: Update memory
                if self.use_memory:
                    self.session_memory.add_intent(intent)
                    for result in step_results:
                        if "path" in str(result).lower():
                            words = str(result).split()
                            for word in words:
                                if "/" in word and not word.startswith("http"):
                                    self.world_model.update_path_frequency(word)
                    
                    self.intent_history.record(user_input, intent, step_results)
                
                # Step 5: Check if goal achieved
                console.print("\n")  # Blank line before reflection
                
                goal_status = goal_tracker.check_goal(
                    user_goal=user_input,
                    original_intent=intent,
                    observations=iteration_observations,
                    stream=True  # Enable streaming for real-time reflection
                )
                
                # Display reflection
                if goal_status.achieved:
                    console.print(f"\n[bold green]✓ Goal Achieved![/bold green]")
                    console.print(f"[dim]{goal_status.reasoning}[/dim]")
                    goal_achieved = True
                else:
                    console.print(f"\n[yellow]⟳ Goal not yet achieved[/yellow]")
                    console.print(f"[dim]Confidence: {goal_status.confidence:.0%}[/dim]")
                    console.print(f"[dim]Reasoning: {goal_status.reasoning}[/dim]")
                    
                    if goal_status.next_steps:
                        console.print(f"\n[cyan]Next steps suggested:[/cyan]")
                        for step in goal_status.next_steps:
                            console.print(f"  • {step}")
                    
                    # Update context for next iteration
                    context = f"Previous attempt: {intent.goal}. Observations: {', '.join(iteration_observations[-3:])}"
            
            # Final result
            if goal_achieved:
                print_success(f"Task completed in {iteration} iteration(s)")
                
                # Add to semantic search
                if self.semantic_search:
                    try:
                        self.semantic_search.add_command(
                            user_input=user_input,
                            goal=intent.goal,
                            steps=[s.model_dump() for s in intent.steps],
                            success=True
                        )
                    except:
                        pass
                
                return f"Task completed successfully in {iteration} iteration(s)"
            else:
                # Max iterations reached - ask for confirmation to continue
                console.print(f"\n[yellow]⚠ Maximum iterations ({max_iterations}) reached[/yellow]")
                console.print(f"[dim]Observations so far: {len(all_observations)} steps completed[/dim]")
                console.print(f"[dim]Goal not yet achieved with high confidence[/dim]\n")
                
                # Ask user if they want to continue
                console.print("[cyan]Would you like to continue for more iterations?[/cyan]")
                user_choice = input("Continue? [y/N]: ").strip().lower()
                
                if user_choice in ['y', 'yes']:
                    # Continue with more iterations
                    console.print("\n[green]Continuing execution...[/green]")
                    additional_iterations = 5  # Add 5 more iterations
                    max_iterations += additional_iterations
                    console.print(f"[dim]New max: {max_iterations} iterations[/dim]\n")
                    
                    # Continue the loop (but we're outside the while, so need recursion)
                    # Instead, let's just tell the user to re-run with higher limit
                    console.print(f"[yellow]Please re-run with: --max-iterations {max_iterations}[/yellow]")
                    return f"Task paused after {iteration} iterations. User can continue with higher limit."
                else:
                    console.print("\n[dim]Stopping execution as requested.[/dim]")
                    return f"Task incomplete after {max_iterations} iterations (user chose to stop)"
        
        except Exception as e:
            error_msg = f"Iterative execution error: {str(e)}"
            self.logger.log_error(error_msg, {"user_input": user_input})
            print_error(error_msg)
            return error_msg
    
    def _build_context(self, user_input: str) -> str:
        """Build context string from memory and environment"""
        context_parts = []
        
        # Environmental context (new!)
        ctx_mgr = get_context_manager()
        env_context = ctx_mgr.get_contextual_prompt()
        if env_context:
            context_parts.append("=== Current Environment ===")
            context_parts.append(env_context)
        
        # Recent intents
        if self.use_memory:
            summary = self.session_memory.get_context_summary(max_intents=3)
            if summary:
                context_parts.append(f"\n=== Recent Activity ===\n{summary}")
        
        # Frequent paths (if query mentions files/directories)
        if any(word in user_input.lower() for word in ["file", "folder", "directory", "path"]):
            if self.use_memory:
                frequent_paths = self.world_model.get_frequent_paths(limit=5)
                if frequent_paths:
                    context_parts.append(f"\n=== Frequent Paths ===\n{', '.join(frequent_paths)}")
        
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
                # Use ANSI codes with readline escape sequences
                # \001 and \002 mark non-printing characters for readline
                prompt = "\n\001\033[1;32m\002zenus >\001\033[0m\002 "
                user_input = input(prompt).strip()
                
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
                
                # Check for --iterative flag
                iterative = False
                if "--iterative" in user_input:
                    iterative = True
                    user_input = user_input.replace("--iterative", "").strip()
                
                # Execute command
                if iterative:
                    result = self.execute_iterative(user_input)
                else:
                    result = self.execute_command(user_input, explain=explain)
                
            except KeyboardInterrupt:
                console.print("\n[dim]Use 'exit' to quit[/dim]")
                continue
            except EOFError:
                console.print("\n[dim]Goodbye![/dim]")
                break
            except Exception as e:
                print_error(f"Shell error: {e}")

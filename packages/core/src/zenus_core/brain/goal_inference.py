"""
Goal Inference - Understand high-level intent and propose complete workflows

Instead of just executing what the user says, understand their TRUE goal
and suggest complete workflows with all implicit steps included.

Key innovations:
- Infer high-level goals from low-level commands
- Detect missing implicit steps
- Propose complete end-to-end workflows
- Learn common workflow patterns
- Suggest best practices automatically
"""

import json
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path


class GoalType(Enum):
    """Types of high-level goals"""
    DEPLOY = "deploy"  # Deploy an application
    DEVELOP = "develop"  # Set up development environment
    DEBUG = "debug"  # Troubleshoot an issue
    MIGRATE = "migrate"  # Migrate data or infrastructure
    BACKUP = "backup"  # Backup data
    MONITOR = "monitor"  # Set up monitoring
    OPTIMIZE = "optimize"  # Improve performance
    SECURITY = "security"  # Secure a system
    TEST = "test"  # Test functionality
    SETUP = "setup"  # Initial setup/installation
    CLEANUP = "cleanup"  # Clean up resources
    UNKNOWN = "unknown"  # Can't infer goal


@dataclass
class ImplicitStep:
    """A step that should be included but wasn't explicitly requested"""
    action: str
    reasoning: str
    importance: str  # "critical", "recommended", "optional"
    when: str  # "before", "after", "during"
    category: str  # "safety", "best_practice", "optimization"


@dataclass
class WorkflowSuggestion:
    """A complete workflow suggestion with all steps"""
    goal: str
    goal_type: GoalType
    explicit_steps: List[str]  # What user asked for
    implicit_steps: List[ImplicitStep]  # What we should add
    complete_workflow: List[str]  # Full ordered workflow
    reasoning: str  # Why these steps?
    estimated_time: str
    risk_assessment: str
    prerequisites: List[str]
    post_actions: List[str]  # What to do after
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result['goal_type'] = self.goal_type.value
        return result


@dataclass
class GoalPattern:
    """A learned pattern for common goals"""
    goal_type: GoalType
    keywords: List[str]
    typical_steps: List[str]
    implicit_requirements: List[str]
    success_count: int = 0
    failure_count: int = 0


class GoalInference:
    """
    Infer user's true intent and propose complete workflows
    
    This makes Zenus proactive - it doesn't just do what you say,
    it figures out what you MEAN and suggests the complete solution!
    """
    
    def __init__(self, llm, logger):
        self.llm = llm
        self.logger = logger
        
        # Storage for learned patterns
        self.storage_dir = Path.home() / ".zenus" / "goals"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.patterns_file = self.storage_dir / "patterns.json"
        
        # Load learned patterns
        self.patterns: List[GoalPattern] = self._load_patterns()
        
        # Initialize common patterns if empty
        if not self.patterns:
            self._initialize_common_patterns()
    
    def infer_goal(self, user_input: str, context: str = "") -> WorkflowSuggestion:
        """
        Infer user's high-level goal and suggest complete workflow
        
        Args:
            user_input: User's natural language command
            context: Additional context from memory
        
        Returns:
            WorkflowSuggestion with complete workflow
        """
        # Step 1: Detect goal type
        goal_type = self._detect_goal_type(user_input)
        
        # Step 2: Extract explicit steps (what user asked for)
        explicit_steps = self._extract_explicit_steps(user_input)
        
        # Step 3: Infer implicit steps (what's missing)
        implicit_steps = self._infer_implicit_steps(
            user_input, 
            goal_type, 
            explicit_steps,
            context
        )
        
        # Step 4: Build complete workflow
        complete_workflow = self._build_complete_workflow(
            explicit_steps,
            implicit_steps
        )
        
        # Step 5: Generate reasoning and metadata
        reasoning = self._generate_reasoning(goal_type, implicit_steps)
        estimated_time = self._estimate_time(complete_workflow)
        risk = self._assess_risk(goal_type, complete_workflow)
        prerequisites = self._identify_prerequisites(goal_type, user_input)
        post_actions = self._suggest_post_actions(goal_type)
        
        # Create suggestion
        suggestion = WorkflowSuggestion(
            goal=self._extract_goal_description(user_input),
            goal_type=goal_type,
            explicit_steps=explicit_steps,
            implicit_steps=implicit_steps,
            complete_workflow=complete_workflow,
            reasoning=reasoning,
            estimated_time=estimated_time,
            risk_assessment=risk,
            prerequisites=prerequisites,
            post_actions=post_actions
        )
        
        # Log for learning
        self.logger.log_info(
            "goal_inference",
            {
                "user_input": user_input,
                "inferred_goal": goal_type.value,
                "implicit_steps_added": len(implicit_steps)
            }
        )
        
        return suggestion
    
    def _detect_goal_type(self, user_input: str) -> GoalType:
        """Detect high-level goal type from user input"""
        input_lower = user_input.lower()
        
        # Goal type detection rules
        goal_rules = {
            GoalType.DEPLOY: ["deploy", "release", "ship", "publish", "production"],
            GoalType.DEVELOP: ["setup dev", "development environment", "dev env", "start developing"],
            GoalType.DEBUG: ["debug", "troubleshoot", "fix", "error", "not working", "broken"],
            GoalType.MIGRATE: ["migrate", "move to", "switch to", "transfer", "upgrade from"],
            GoalType.BACKUP: ["backup", "save", "snapshot", "archive"],
            GoalType.MONITOR: ["monitor", "watch", "alert", "metrics", "observability"],
            GoalType.OPTIMIZE: ["optimize", "speed up", "improve performance", "make faster"],
            GoalType.SECURITY: ["secure", "harden", "protect", "firewall", "vulnerability"],
            GoalType.TEST: ["test", "verify", "check", "validate", "run tests"],
            GoalType.SETUP: ["setup", "install", "configure", "initialize", "set up"],
            GoalType.CLEANUP: ["cleanup", "clean up", "remove", "delete old", "free space"],
        }
        
        # Check each goal type
        for goal_type, keywords in goal_rules.items():
            if any(kw in input_lower for kw in keywords):
                return goal_type
        
        return GoalType.UNKNOWN
    
    def _extract_explicit_steps(self, user_input: str) -> List[str]:
        """Extract steps explicitly mentioned by user"""
        # Simple extraction - could be enhanced with NLP
        steps = []
        
        # Common action words
        action_words = [
            "create", "build", "run", "start", "stop",
            "install", "configure", "setup", "deploy",
            "test", "check", "verify", "update", "upgrade"
        ]
        
        input_lower = user_input.lower()
        for action in action_words:
            if action in input_lower:
                steps.append(action)
        
        return steps if steps else ["execute task"]
    
    def _infer_implicit_steps(
        self,
        user_input: str,
        goal_type: GoalType,
        explicit_steps: List[str],
        context: str
    ) -> List[ImplicitStep]:
        """
        Infer steps that should be included but weren't explicitly mentioned
        
        This is the MAGIC - understanding what the user NEEDS but didn't ask for!
        """
        implicit_steps = []
        
        # Goal-specific implicit steps
        if goal_type == GoalType.DEPLOY:
            implicit_steps.extend([
                ImplicitStep(
                    action="Run tests before deployment",
                    reasoning="Ensure code works before shipping to production",
                    importance="critical",
                    when="before",
                    category="safety"
                ),
                ImplicitStep(
                    action="Create backup of current deployment",
                    reasoning="Enable quick rollback if deployment fails",
                    importance="critical",
                    when="before",
                    category="safety"
                ),
                ImplicitStep(
                    action="Check if services are healthy",
                    reasoning="Verify deployment succeeded",
                    importance="critical",
                    when="after",
                    category="best_practice"
                ),
                ImplicitStep(
                    action="Monitor error rates for 5 minutes",
                    reasoning="Catch issues early after deployment",
                    importance="recommended",
                    when="after",
                    category="best_practice"
                )
            ])
        
        elif goal_type == GoalType.DEVELOP:
            implicit_steps.extend([
                ImplicitStep(
                    action="Check system requirements",
                    reasoning="Ensure system meets minimum requirements",
                    importance="critical",
                    when="before",
                    category="best_practice"
                ),
                ImplicitStep(
                    action="Setup version control",
                    reasoning="Enable collaboration and code history",
                    importance="recommended",
                    when="during",
                    category="best_practice"
                ),
                ImplicitStep(
                    action="Configure pre-commit hooks",
                    reasoning="Maintain code quality automatically",
                    importance="recommended",
                    when="during",
                    category="best_practice"
                )
            ])
        
        elif goal_type == GoalType.MIGRATE:
            implicit_steps.extend([
                ImplicitStep(
                    action="Backup current data",
                    reasoning="Prevent data loss during migration",
                    importance="critical",
                    when="before",
                    category="safety"
                ),
                ImplicitStep(
                    action="Run migration in dry-run mode first",
                    reasoning="Verify migration works before applying",
                    importance="critical",
                    when="before",
                    category="safety"
                ),
                ImplicitStep(
                    action="Verify data integrity after migration",
                    reasoning="Ensure no data was corrupted",
                    importance="critical",
                    when="after",
                    category="safety"
                )
            ])
        
        elif goal_type == GoalType.SECURITY:
            implicit_steps.extend([
                ImplicitStep(
                    action="Audit current vulnerabilities",
                    reasoning="Know what needs fixing",
                    importance="critical",
                    when="before",
                    category="best_practice"
                ),
                ImplicitStep(
                    action="Review exposed ports and services",
                    reasoning="Minimize attack surface",
                    importance="critical",
                    when="during",
                    category="security"
                ),
                ImplicitStep(
                    action="Run security scan after hardening",
                    reasoning="Verify security improvements",
                    importance="recommended",
                    when="after",
                    category="security"
                )
            ])
        
        elif goal_type == GoalType.CLEANUP:
            implicit_steps.extend([
                ImplicitStep(
                    action="List what will be deleted",
                    reasoning="Preview changes before deleting",
                    importance="critical",
                    when="before",
                    category="safety"
                ),
                ImplicitStep(
                    action="Confirm deletion with user",
                    reasoning="Prevent accidental data loss",
                    importance="critical",
                    when="before",
                    category="safety"
                )
            ])
        
        # Check for database operations
        if any(kw in user_input.lower() for kw in ["database", "db", "sql", "postgres", "mysql"]):
            implicit_steps.append(
                ImplicitStep(
                    action="Backup database before modification",
                    reasoning="Database changes can be destructive",
                    importance="critical",
                    when="before",
                    category="safety"
                )
            )
        
        # Check for file operations
        if any(kw in user_input.lower() for kw in ["delete", "remove", "rm"]):
            implicit_steps.append(
                ImplicitStep(
                    action="Use trash instead of permanent deletion",
                    reasoning="Enable recovery of accidentally deleted files",
                    importance="recommended",
                    when="during",
                    category="safety"
                )
            )
        
        return implicit_steps
    
    def _build_complete_workflow(
        self,
        explicit_steps: List[str],
        implicit_steps: List[ImplicitStep]
    ) -> List[str]:
        """Build complete ordered workflow from explicit and implicit steps"""
        workflow = []
        
        # Add "before" implicit steps (critical first)
        before_critical = [s for s in implicit_steps if s.when == "before" and s.importance == "critical"]
        before_recommended = [s for s in implicit_steps if s.when == "before" and s.importance == "recommended"]
        
        workflow.extend([f"[SAFETY] {s.action}" for s in before_critical])
        workflow.extend([f"[RECOMMENDED] {s.action}" for s in before_recommended])
        
        # Add explicit steps (what user asked for)
        workflow.extend(explicit_steps)
        
        # Add "during" implicit steps
        during_steps = [s for s in implicit_steps if s.when == "during"]
        workflow.extend([f"[RECOMMENDED] {s.action}" for s in during_steps])
        
        # Add "after" implicit steps
        after_critical = [s for s in implicit_steps if s.when == "after" and s.importance == "critical"]
        after_recommended = [s for s in implicit_steps if s.when == "after" and s.importance == "recommended"]
        
        workflow.extend([f"[VERIFY] {s.action}" for s in after_critical])
        workflow.extend([f"[RECOMMENDED] {s.action}" for s in after_recommended])
        
        return workflow
    
    def _generate_reasoning(
        self,
        goal_type: GoalType,
        implicit_steps: List[ImplicitStep]
    ) -> str:
        """Generate human-readable reasoning for workflow suggestion"""
        reasoning = f"Detected goal: {goal_type.value}. "
        
        critical_steps = [s for s in implicit_steps if s.importance == "critical"]
        if critical_steps:
            reasoning += f"Added {len(critical_steps)} critical safety step(s) "
            reasoning += "to prevent data loss and ensure safe execution. "
        
        recommended_steps = [s for s in implicit_steps if s.importance == "recommended"]
        if recommended_steps:
            reasoning += f"Suggested {len(recommended_steps)} best practice step(s) "
            reasoning += "based on common workflows. "
        
        return reasoning
    
    def _estimate_time(self, workflow: List[str]) -> str:
        """Estimate workflow execution time"""
        num_steps = len(workflow)
        
        if num_steps <= 3:
            return "~1-2 minutes"
        elif num_steps <= 7:
            return "~5-10 minutes"
        elif num_steps <= 12:
            return "~15-30 minutes"
        else:
            return "~30+ minutes"
    
    def _assess_risk(self, goal_type: GoalType, workflow: List[str]) -> str:
        """Assess risk level of workflow"""
        high_risk_goals = [GoalType.DEPLOY, GoalType.MIGRATE, GoalType.CLEANUP]
        
        has_safety_steps = any("[SAFETY]" in step for step in workflow)
        
        if goal_type in high_risk_goals and not has_safety_steps:
            return "HIGH - No safety measures detected"
        elif goal_type in high_risk_goals and has_safety_steps:
            return "MEDIUM - Safety measures in place"
        else:
            return "LOW - Reversible operations"
    
    def _identify_prerequisites(self, goal_type: GoalType, user_input: str) -> List[str]:
        """Identify prerequisites for the goal"""
        prereqs = []
        
        if goal_type == GoalType.DEPLOY:
            prereqs = [
                "All tests passing",
                "Code reviewed and approved",
                "Staging deployment successful",
                "Rollback plan prepared"
            ]
        elif goal_type == GoalType.DEVELOP:
            prereqs = [
                "Required tools installed",
                "Access credentials configured",
                "Repository cloned"
            ]
        elif goal_type == GoalType.MIGRATE:
            prereqs = [
                "Target system ready",
                "Sufficient storage space",
                "Backup completed",
                "Migration tested on staging"
            ]
        
        return prereqs
    
    def _suggest_post_actions(self, goal_type: GoalType) -> List[str]:
        """Suggest actions to do after workflow completes"""
        post_actions = []
        
        if goal_type == GoalType.DEPLOY:
            post_actions = [
                "Monitor application metrics for 30 minutes",
                "Check error logging dashboard",
                "Announce deployment in team chat",
                "Update deployment documentation"
            ]
        elif goal_type == GoalType.DEVELOP:
            post_actions = [
                "Run initial tests to verify setup",
                "Create a hello-world commit",
                "Review project documentation"
            ]
        elif goal_type == GoalType.SECURITY:
            post_actions = [
                "Schedule regular security audits",
                "Document security changes",
                "Update team on new security policies"
            ]
        
        return post_actions
    
    def _extract_goal_description(self, user_input: str) -> str:
        """Extract a concise goal description"""
        # Simple approach - could use LLM for better results
        return user_input[:100] + ("..." if len(user_input) > 100 else "")
    
    def _initialize_common_patterns(self):
        """Initialize common workflow patterns"""
        self.patterns = [
            GoalPattern(
                goal_type=GoalType.DEPLOY,
                keywords=["deploy", "ship", "release"],
                typical_steps=["test", "build", "backup", "deploy", "verify"],
                implicit_requirements=["tests pass", "backup exists", "monitoring active"]
            ),
            GoalPattern(
                goal_type=GoalType.DEVELOP,
                keywords=["setup", "dev", "development"],
                typical_steps=["install", "configure", "test"],
                implicit_requirements=["dependencies installed", "config files present"]
            )
        ]
        self._save_patterns()
    
    def _load_patterns(self) -> List[GoalPattern]:
        """Load learned patterns from disk"""
        if not self.patterns_file.exists():
            return []
        
        try:
            with open(self.patterns_file) as f:
                data = json.load(f)
            
            patterns = []
            for p in data:
                p['goal_type'] = GoalType(p['goal_type'])
                patterns.append(GoalPattern(**p))
            
            return patterns
        except Exception as e:
            self.logger.log_error(f"Failed to load goal patterns: {e}")
            return []
    
    def _save_patterns(self):
        """Save patterns to disk"""
        try:
            data = []
            for p in self.patterns:
                pattern_dict = asdict(p)
                pattern_dict['goal_type'] = p.goal_type.value
                data.append(pattern_dict)
            
            with open(self.patterns_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.log_error(f"Failed to save goal patterns: {e}")


# Singleton instance
_goal_inference_instance = None


def get_goal_inference(llm, logger) -> GoalInference:
    """Get or create GoalInference instance"""
    global _goal_inference_instance
    if _goal_inference_instance is None:
        _goal_inference_instance = GoalInference(llm, logger)
    return _goal_inference_instance

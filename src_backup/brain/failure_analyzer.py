"""
Failure Analyzer

Analyzes failure patterns and suggests corrections.
"""

from typing import Optional, Dict, List, Tuple
from memory.failure_logger import get_failure_logger, Failure
from brain.llm.schemas import IntentIR
import re


class FailureAnalyzer:
    """
    Analyzes failures and provides intelligent suggestions
    
    Capabilities:
    - Detect similar past failures
    - Suggest corrections based on patterns
    - Calculate success probability
    - Generate recovery strategies
    """
    
    def __init__(self):
        self.logger = get_failure_logger()
        
        # Built-in error patterns and fixes
        self.known_patterns = {
            "permission_denied": {
                "indicators": ["permission denied", "access denied", "not permitted"],
                "suggestions": [
                    "Try using 'sudo' for elevated permissions",
                    "Check file/directory permissions with 'ls -la'",
                    "Verify you own the file/directory"
                ]
            },
            "file_not_found": {
                "indicators": ["no such file", "not found", "does not exist"],
                "suggestions": [
                    "Check the file path is correct",
                    "Verify the file exists with 'ls' or 'find'",
                    "Check for typos in the filename"
                ]
            },
            "command_not_found": {
                "indicators": ["command not found", "not recognized as"],
                "suggestions": [
                    "Install the required package",
                    "Check if the command is in your PATH",
                    "Verify the command name spelling"
                ]
            },
            "syntax_error": {
                "indicators": ["syntax error", "invalid syntax", "unexpected token"],
                "suggestions": [
                    "Check for missing quotes or brackets",
                    "Verify command syntax with --help",
                    "Review the command structure"
                ]
            },
            "network_error": {
                "indicators": ["connection refused", "network unreachable", "timeout"],
                "suggestions": [
                    "Check your internet connection",
                    "Verify the server is accessible",
                    "Try again after a moment"
                ]
            },
            "disk_space": {
                "indicators": ["no space left", "disk full", "quota exceeded"],
                "suggestions": [
                    "Free up disk space",
                    "Check disk usage with 'df -h'",
                    "Remove unnecessary files"
                ]
            },
            "package_conflict": {
                "indicators": ["dependency conflict", "version mismatch", "incompatible"],
                "suggestions": [
                    "Update package dependencies",
                    "Check for version conflicts",
                    "Try installing in a virtual environment"
                ]
            }
        }
    
    def analyze_before_execution(
        self,
        user_input: str,
        intent: IntentIR
    ) -> Dict:
        """
        Analyze potential issues before execution
        
        Args:
            user_input: Original user command
            intent: Translated intent
        
        Returns:
            Analysis results with warnings and suggestions
        """
        analysis = {
            "has_warnings": False,
            "warnings": [],
            "suggestions": [],
            "success_probability": 1.0,
            "similar_failures": []
        }
        
        # Check for similar past failures
        for step in intent.steps:
            similar = self.logger.get_similar_failures(
                user_input=user_input,
                tool=step.tool,
                limit=3
            )
            
            if similar:
                analysis["has_warnings"] = True
                analysis["similar_failures"].extend(similar)
                
                # Calculate success probability based on past failures
                failure_count = len(similar)
                if failure_count >= 3:
                    analysis["success_probability"] *= 0.5
                elif failure_count == 2:
                    analysis["success_probability"] *= 0.7
                else:
                    analysis["success_probability"] *= 0.85
                
                # Add warnings
                analysis["warnings"].append(
                    f"⚠️  Tool '{step.tool}' has failed {failure_count} time(s) recently"
                )
                
                # Get pattern suggestions
                for failure in similar:
                    suggestion = self.logger.get_pattern_suggestions(
                        tool=failure.tool,
                        error_message=failure.error_message
                    )
                    if suggestion and suggestion not in analysis["suggestions"]:
                        analysis["suggestions"].append(suggestion)
        
        return analysis
    
    def analyze_failure(
        self,
        user_input: str,
        intent_goal: str,
        tool: str,
        error_message: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Analyze a failure and provide recovery suggestions
        
        Args:
            user_input: Original user command
            intent_goal: Intent goal that failed
            tool: Tool that failed
            error_message: Error message
            context: Execution context
        
        Returns:
            Analysis with categorization and suggestions
        """
        error_type = self._categorize_error(error_message)
        
        # Log the failure
        failure_id = self.logger.log_failure(
            user_input=user_input,
            intent_goal=intent_goal,
            tool=tool,
            error_type=error_type,
            error_message=error_message,
            context=context
        )
        
        # Get suggestions
        suggestions = self._generate_suggestions(error_type, error_message, tool)
        
        # Check for learned patterns
        pattern_suggestion = self.logger.get_pattern_suggestions(tool, error_message)
        if pattern_suggestion:
            suggestions.insert(0, f"💡 Learned fix: {pattern_suggestion}")
        
        # Get similar past failures
        similar = self.logger.get_similar_failures(user_input, tool, limit=3)
        
        return {
            "failure_id": failure_id,
            "error_type": error_type,
            "suggestions": suggestions,
            "similar_failures": similar,
            "is_recurring": len(similar) >= 2
        }
    
    def _categorize_error(self, error_message: str) -> str:
        """
        Categorize error by type
        
        Args:
            error_message: Error message
        
        Returns:
            Error category
        """
        error_lower = error_message.lower()
        
        for category, pattern_info in self.known_patterns.items():
            for indicator in pattern_info["indicators"]:
                if indicator in error_lower:
                    return category
        
        # Check for other common patterns
        if "timeout" in error_lower or "timed out" in error_lower:
            return "timeout"
        
        if "parse" in error_lower or "parsing" in error_lower:
            return "parse_error"
        
        if "memory" in error_lower or "out of memory" in error_lower:
            return "memory_error"
        
        if "killed" in error_lower or "signal" in error_lower:
            return "process_killed"
        
        return "unknown"
    
    def _generate_suggestions(
        self,
        error_type: str,
        error_message: str,
        tool: str
    ) -> List[str]:
        """
        Generate suggestions for recovery
        
        Args:
            error_type: Categorized error type
            error_message: Full error message
            tool: Tool that failed
        
        Returns:
            List of suggestions
        """
        suggestions = []
        
        # Add known pattern suggestions
        if error_type in self.known_patterns:
            suggestions.extend(self.known_patterns[error_type]["suggestions"])
        
        # Add tool-specific suggestions
        tool_suggestions = self._get_tool_specific_suggestions(tool, error_message)
        suggestions.extend(tool_suggestions)
        
        # Generic fallback
        if not suggestions:
            suggestions.append("Review the error message for details")
            suggestions.append("Check the command syntax and arguments")
            suggestions.append("Verify prerequisites are met")
        
        return suggestions[:5]  # Limit to 5 suggestions
    
    def _get_tool_specific_suggestions(self, tool: str, error_message: str) -> List[str]:
        """Get tool-specific suggestions"""
        
        suggestions = []
        error_lower = error_message.lower()
        
        if tool == "FileOps":
            if "permission" in error_lower:
                suggestions.append("Check file ownership and permissions")
            if "not found" in error_lower:
                suggestions.append("Verify the file path is correct")
        
        elif tool == "BrowserOps":
            if "timeout" in error_lower:
                suggestions.append("The page might be slow to load - try increasing timeout")
            if "element" in error_lower:
                suggestions.append("The webpage structure might have changed")
        
        elif tool == "PackageOps":
            if "not found" in error_lower:
                suggestions.append("Update package lists: sudo apt update")
            if "conflict" in error_lower:
                suggestions.append("Try resolving conflicts: sudo apt --fix-broken install")
        
        elif tool == "GitOps":
            if "conflict" in error_lower:
                suggestions.append("Resolve merge conflicts manually")
            if "remote" in error_lower:
                suggestions.append("Check git remote configuration")
        
        elif tool == "ContainerOps":
            if "not found" in error_lower:
                suggestions.append("Pull the container image first")
            if "permission" in error_lower:
                suggestions.append("Add your user to the docker group")
        
        elif tool == "NetworkOps":
            if "connection" in error_lower:
                suggestions.append("Check network connectivity")
            if "timeout" in error_lower:
                suggestions.append("Server might be slow or unreachable")
        
        return suggestions
    
    def get_success_probability(
        self,
        user_input: str,
        tool: str
    ) -> Tuple[float, str]:
        """
        Calculate success probability based on history
        
        Args:
            user_input: User command
            tool: Tool to be used
        
        Returns:
            (probability 0-1, confidence level)
        """
        similar = self.logger.get_similar_failures(user_input, tool, limit=10)
        
        if not similar:
            return (0.95, "high")  # No failures = high confidence
        
        failure_count = len(similar)
        
        # Calculate based on failure frequency
        if failure_count >= 5:
            return (0.3, "low")
        elif failure_count >= 3:
            return (0.5, "medium")
        elif failure_count >= 2:
            return (0.7, "medium")
        else:
            return (0.85, "high")
    
    def generate_recovery_plan(
        self,
        failure: Failure
    ) -> Optional[str]:
        """
        Generate a recovery plan for a failure
        
        Args:
            failure: Failure object
        
        Returns:
            Recovery plan description
        """
        error_type = self._categorize_error(failure.error_message)
        
        recovery_templates = {
            "permission_denied": (
                "1. Check permissions with 'ls -la <path>'\n"
                "2. Fix permissions with 'chmod' or 'chown'\n"
                "3. Or retry with 'sudo' if appropriate"
            ),
            "file_not_found": (
                "1. Verify the file path\n"
                "2. Check spelling and case sensitivity\n"
                "3. Use 'find' to locate the file"
            ),
            "command_not_found": (
                "1. Install the required package\n"
                "2. Or check if it's installed but not in PATH\n"
                "3. Verify the command name"
            ),
            "network_error": (
                "1. Check internet connection\n"
                "2. Verify firewall settings\n"
                "3. Wait and retry if server is temporarily down"
            )
        }
        
        return recovery_templates.get(error_type)
    
    def should_retry(
        self,
        failure: Failure,
        attempt_count: int
    ) -> Tuple[bool, str]:
        """
        Determine if operation should be retried
        
        Args:
            failure: Failure object
            attempt_count: Current attempt count
        
        Returns:
            (should_retry, reason)
        """
        error_type = self._categorize_error(failure.error_message)
        
        # Never retry these errors
        no_retry_types = [
            "permission_denied",
            "file_not_found",
            "command_not_found",
            "syntax_error"
        ]
        
        if error_type in no_retry_types:
            return (False, f"{error_type} errors require manual intervention")
        
        # Retry transient errors
        retry_types = ["network_error", "timeout", "memory_error"]
        
        if error_type in retry_types:
            if attempt_count < 3:
                return (True, f"{error_type} might be transient")
            else:
                return (False, "Max retry attempts reached")
        
        # Unknown errors - allow one retry
        if attempt_count < 2:
            return (True, "Unknown error - trying once more")
        
        return (False, "Not safe to retry")

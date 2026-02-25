"""
Enhanced Error Handler

Provides user-friendly error messages and actionable suggestions:
- Structured error types
- Context-aware explanations
- Recovery suggestions
- Fallback strategies
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum


class ErrorCategory(Enum):
    """Error categories for better handling"""
    PERMISSION = "permission"
    NOT_FOUND = "not_found"
    NETWORK = "network"
    TIMEOUT = "timeout"
    INVALID_INPUT = "invalid_input"
    RESOURCE_LIMIT = "resource_limit"
    DEPENDENCY = "dependency"
    UNKNOWN = "unknown"


@dataclass
class EnhancedError:
    """Enhanced error with context and suggestions"""
    category: ErrorCategory
    message: str
    user_friendly: str
    suggestions: List[str]
    fallback_commands: List[str]
    context: Dict[str, Any]
    
    def format(self) -> str:
        """Format error for display"""
        lines = []
        
        # Main error
        lines.append(f"❌ {self.user_friendly}\n")
        
        # Technical details
        if self.message:
            lines.append(f"[dim]Reason: {self.message}[/dim]\n")
        
        # Suggestions
        if self.suggestions:
            lines.append("[cyan]💡 Suggestions:[/cyan]")
            for i, suggestion in enumerate(self.suggestions, 1):
                lines.append(f"  {i}. {suggestion}")
            lines.append("")
        
        # Fallback commands
        if self.fallback_commands:
            lines.append("[yellow]🔄 Try these instead:[/yellow]")
            for cmd in self.fallback_commands:
                lines.append(f"  zenus \"{cmd}\"")
        
        return "\n".join(lines)


class ErrorHandler:
    """
    Enhanced error handler with context-aware messages
    
    Analyzes errors and provides:
    - User-friendly explanations
    - Actionable suggestions
    - Fallback strategies
    - Tool alternatives
    """
    
    # Common error patterns
    ERROR_PATTERNS = {
        'permission denied': ErrorCategory.PERMISSION,
        'access denied': ErrorCategory.PERMISSION,
        'not permitted': ErrorCategory.PERMISSION,
        'not found': ErrorCategory.NOT_FOUND,
        'no such file': ErrorCategory.NOT_FOUND,
        'does not exist': ErrorCategory.NOT_FOUND,
        'package not found': ErrorCategory.NOT_FOUND,
        'connection refused': ErrorCategory.NETWORK,
        'network unreachable': ErrorCategory.NETWORK,
        'no route to host': ErrorCategory.NETWORK,
        'timeout': ErrorCategory.TIMEOUT,
        'timed out': ErrorCategory.TIMEOUT,
        'invalid': ErrorCategory.INVALID_INPUT,
        'syntax error': ErrorCategory.INVALID_INPUT,
        'memory': ErrorCategory.RESOURCE_LIMIT,
        'disk': ErrorCategory.RESOURCE_LIMIT,
        'quota': ErrorCategory.RESOURCE_LIMIT,
        'dependency': ErrorCategory.DEPENDENCY,
        'missing': ErrorCategory.DEPENDENCY,
    }
    
    def __init__(self):
        pass
    
    def handle(
        self,
        error: Exception,
        tool: str,
        action: str,
        args: Dict[str, Any],
        context: Optional[Dict] = None
    ) -> EnhancedError:
        """
        Handle error with enhanced messaging
        
        Args:
            error: Original exception
            tool: Tool that failed
            action: Action that failed
            args: Arguments passed
            context: Additional context
        
        Returns:
            EnhancedError with suggestions
        """
        error_str = str(error).lower()
        
        # Categorize error
        category = self._categorize(error_str)
        
        # Generate user-friendly message
        user_friendly = self._generate_message(category, tool, action, args, error_str)
        
        # Generate suggestions
        suggestions = self._generate_suggestions(category, tool, action, args, error_str)
        
        # Generate fallback commands
        fallbacks = self._generate_fallbacks(category, tool, action, args)
        
        return EnhancedError(
            category=category,
            message=str(error),
            user_friendly=user_friendly,
            suggestions=suggestions,
            fallback_commands=fallbacks,
            context=context or {},
        )
    
    def _categorize(self, error_str: str) -> ErrorCategory:
        """Categorize error by pattern matching"""
        for pattern, category in self.ERROR_PATTERNS.items():
            if pattern in error_str:
                return category
        
        return ErrorCategory.UNKNOWN
    
    def _generate_message(
        self,
        category: ErrorCategory,
        tool: str,
        action: str,
        args: Dict,
        error_str: str
    ) -> str:
        """Generate user-friendly error message"""
        if category == ErrorCategory.PERMISSION:
            return f"Permission denied accessing {args.get('path', 'resource')}"
        
        elif category == ErrorCategory.NOT_FOUND:
            if tool == 'PackageOps':
                package = args.get('package', 'package')
                return f"Package '{package}' not found in repositories"
            else:
                path = args.get('path', args.get('source', 'resource'))
                return f"File or directory '{path}' not found"
        
        elif category == ErrorCategory.NETWORK:
            return "Network connection failed"
        
        elif category == ErrorCategory.TIMEOUT:
            return "Operation took too long and timed out"
        
        elif category == ErrorCategory.INVALID_INPUT:
            return "Invalid input or syntax error"
        
        elif category == ErrorCategory.RESOURCE_LIMIT:
            if 'memory' in error_str:
                return "Insufficient memory to complete operation"
            elif 'disk' in error_str:
                return "Insufficient disk space"
            else:
                return "Resource limit reached"
        
        elif category == ErrorCategory.DEPENDENCY:
            return "Missing dependency or requirement"
        
        else:
            return f"{tool}.{action} failed"
    
    def _generate_suggestions(
        self,
        category: ErrorCategory,
        tool: str,
        action: str,
        args: Dict,
        error_str: str
    ) -> List[str]:
        """Generate actionable suggestions"""
        suggestions = []
        
        if category == ErrorCategory.PERMISSION:
            suggestions.append("Try running with sudo (use 'install with sudo' or similar)")
            suggestions.append("Check file/directory permissions")
            suggestions.append("Verify you're the owner of the resource")
        
        elif category == ErrorCategory.NOT_FOUND:
            if tool == 'PackageOps':
                package = args.get('package', 'package')
                suggestions.append(f"Search for the package: zenus \"search for {package}\"")
                suggestions.append("Update package lists: zenus \"update package lists\"")
                suggestions.append("Check if it's available in different repositories")
                suggestions.append(f"Try alternative package managers (snap, flatpak)")
            else:
                path = args.get('path', 'file')
                suggestions.append(f"Check if '{path}' exists")
                suggestions.append("Verify the path is correct (typos?)")
                suggestions.append("List directory contents to find it")
        
        elif category == ErrorCategory.NETWORK:
            suggestions.append("Check your internet connection")
            suggestions.append("Verify the URL or host is correct")
            suggestions.append("Try again in a few moments")
            suggestions.append("Check if a firewall is blocking the connection")
        
        elif category == ErrorCategory.TIMEOUT:
            suggestions.append("Try again (may be temporary)")
            suggestions.append("Check system resources (CPU, memory)")
            suggestions.append("Increase timeout if possible")
        
        elif category == ErrorCategory.INVALID_INPUT:
            suggestions.append("Check the command syntax")
            suggestions.append("Verify all required parameters are provided")
            suggestions.append("Try rephrasing the command")
        
        elif category == ErrorCategory.RESOURCE_LIMIT:
            if 'memory' in error_str:
                suggestions.append("Close unnecessary programs")
                suggestions.append("Check memory usage: zenus \"check memory\"")
                suggestions.append("Increase swap space if possible")
            elif 'disk' in error_str:
                suggestions.append("Free up disk space")
                suggestions.append("Check disk usage: zenus \"check disk usage\"")
                suggestions.append("Remove large unused files")
        
        elif category == ErrorCategory.DEPENDENCY:
            suggestions.append("Install missing dependencies")
            suggestions.append("Check system requirements")
            suggestions.append("Update relevant packages")
        
        return suggestions
    
    def _generate_fallbacks(
        self,
        category: ErrorCategory,
        tool: str,
        action: str,
        args: Dict
    ) -> List[str]:
        """Generate fallback commands"""
        fallbacks = []
        
        if category == ErrorCategory.NOT_FOUND and tool == 'PackageOps':
            package = args.get('package', 'package')
            fallbacks.append(f"search for {package} package")
            fallbacks.append(f"install {package} from snap")
            fallbacks.append(f"check if {package} is already installed")
        
        elif category == ErrorCategory.PERMISSION:
            path = args.get('path', args.get('source', ''))
            if path:
                fallbacks.append(f"check permissions of {path}")
                fallbacks.append(f"show owner of {path}")
        
        elif category == ErrorCategory.RESOURCE_LIMIT:
            if 'memory' in str(args).lower():
                fallbacks.append("check memory usage")
                fallbacks.append("list top memory processes")
            elif 'disk' in str(args).lower():
                fallbacks.append("check disk usage")
                fallbacks.append("find large files")
        
        return fallbacks


# Global handler
_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """Get singleton error handler"""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler

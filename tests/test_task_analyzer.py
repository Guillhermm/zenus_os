"""
Tests for TaskAnalyzer

Validates task complexity detection and iterative need classification
"""

import pytest
from brain.task_analyzer import TaskAnalyzer, TaskComplexity


def test_task_analyzer_initialization():
    """Test TaskAnalyzer initializes correctly"""
    analyzer = TaskAnalyzer()
    
    assert analyzer.llm is None  # No LLM by default
    assert len(analyzer.ITERATIVE_KEYWORDS) > 0
    assert len(analyzer.ONESHOT_KEYWORDS) > 0


def test_simple_oneshot_tasks():
    """Test that simple tasks are classified as one-shot"""
    analyzer = TaskAnalyzer()
    
    simple_tasks = [
        "list files in ~/Documents",
        "show disk usage",
        "create folder ~/test",
        "display memory info",
        "what is the CPU usage"
    ]
    
    for task in simple_tasks:
        result = analyzer.analyze(task)
        assert result.needs_iteration == False, f"Task '{task}' should be one-shot"
        assert result.confidence >= 0.5


def test_complex_iterative_tasks():
    """Test that complex tasks are classified as iterative"""
    analyzer = TaskAnalyzer()
    
    complex_tasks = [
        "read my LaTeX project and improve chapter 3",
        "organize my downloads folder by type and then by date",
        "analyze the code and suggest refactorings",
        "find all Python files, understand them, and generate documentation",
        "examine the project structure and identify improvements"
    ]
    
    for task in complex_tasks:
        result = analyzer.analyze(task)
        assert result.needs_iteration == True, f"Task '{task}' should be iterative"
        assert result.confidence >= 0.5


def test_multi_step_detection():
    """Test detection of multi-step tasks"""
    analyzer = TaskAnalyzer()
    
    # Task with explicit multi-step language
    task = "scan the folder, then move PDFs to a new directory, and finally delete temp files"
    result = analyzer.analyze(task)
    
    assert result.needs_iteration == True
    assert result.estimated_steps >= 2


def test_conditional_task_detection():
    """Test detection of conditional tasks"""
    analyzer = TaskAnalyzer()
    
    # Task with conditional logic
    task = "find files that are older than 30 days and move them to archive"
    result = analyzer.analyze(task)
    
    assert result.needs_iteration == True


def test_estimated_steps():
    """Test that estimated steps scale with complexity"""
    analyzer = TaskAnalyzer()
    
    simple_task = "list files"
    complex_task = "read project, analyze structure, identify issues, suggest improvements, and generate report"
    
    simple_result = analyzer.analyze(simple_task)
    complex_result = analyzer.analyze(complex_task)
    
    assert simple_result.estimated_steps < complex_result.estimated_steps


def test_task_complexity_representation():
    """Test TaskComplexity string representation"""
    complexity = TaskComplexity(
        needs_iteration=True,
        confidence=0.85,
        reasoning="Complex multi-step task",
        estimated_steps=5
    )
    
    repr_str = repr(complexity)
    assert "ITERATIVE" in repr_str
    assert "0.85" in repr_str
    assert "5" in repr_str


def test_iterative_keywords_detection():
    """Test that iterative keywords are properly detected"""
    analyzer = TaskAnalyzer()
    
    # Tasks with strong iterative keywords
    tasks_with_keywords = [
        "analyze the codebase",  # analyze
        "understand the project structure",  # understand
        "improve the documentation",  # improve
        "organize files based on their type",  # based on
        "find duplicates and then move them"  # multi-step + then
    ]
    
    for task in tasks_with_keywords:
        result = analyzer.analyze(task)
        assert result.needs_iteration == True, f"Task '{task}' should be iterative but got: {result}"


def test_oneshot_keywords_detection():
    """Test that one-shot keywords are properly detected"""
    analyzer = TaskAnalyzer()
    
    # Tasks with strong one-shot keywords
    tasks_with_keywords = [
        "list all files",  # list
        "show system status",  # show
        "display process info",  # display
        "create empty file test.txt",  # create empty
        "make folder backup"  # make folder
    ]
    
    for task in tasks_with_keywords:
        result = analyzer.analyze(task)
        assert result.needs_iteration == False


def test_word_count_heuristic():
    """Test that very long commands are considered complex"""
    analyzer = TaskAnalyzer()
    
    short_task = "list files"
    long_task = "I need you to scan my entire project directory recursively find all Python files check if they follow PEP8 standards identify any issues and then generate a comprehensive report with suggestions for improvements"
    
    short_result = analyzer.analyze(short_task)
    long_result = analyzer.analyze(long_task)
    
    # Long task should have higher complexity score
    assert long_result.needs_iteration or long_result.confidence < short_result.confidence


def test_file_operations_with_conditions():
    """Test that file operations with conditions are complex"""
    analyzer = TaskAnalyzer()
    
    task = "move files where the name contains 'backup' to the archive folder"
    result = analyzer.analyze(task)
    
    assert result.needs_iteration == True


def test_reasoning_provided():
    """Test that reasoning is always provided"""
    analyzer = TaskAnalyzer()
    
    tasks = [
        "list files",
        "organize downloads by type",
        "analyze code and refactor"
    ]
    
    for task in tasks:
        result = analyzer.analyze(task)
        assert result.reasoning is not None
        assert len(result.reasoning) > 0
        assert isinstance(result.reasoning, str)


def test_confidence_ranges():
    """Test that confidence is always between 0 and 1"""
    analyzer = TaskAnalyzer()
    
    tasks = [
        "list files",
        "maybe organize some stuff",
        "definitely analyze the entire codebase thoroughly"
    ]
    
    for task in tasks:
        result = analyzer.analyze(task)
        assert 0.0 <= result.confidence <= 1.0

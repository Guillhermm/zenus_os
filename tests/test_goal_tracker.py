"""
Tests for GoalTracker

Validates goal achievement detection and iteration limiting
"""

import pytest
from brain.goal_tracker import GoalTracker, GoalStatus
from brain.llm.schemas import IntentIR, Step


def test_goal_tracker_initialization():
    """Test GoalTracker initializes correctly"""
    tracker = GoalTracker(max_iterations=5)
    
    assert tracker.max_iterations == 5
    assert tracker.current_iteration == 0
    assert tracker.observation_history == []


def test_goal_tracker_iteration_limit():
    """Test that GoalTracker stops at max_iterations"""
    tracker = GoalTracker(max_iterations=3)
    
    # Create a simple intent
    intent = IntentIR(
        goal="Test goal",
        requires_confirmation=False,
        steps=[
            Step(tool="FileOps", action="scan", args={"path": "."}, risk=0)
        ]
    )
    
    # Simulate 3 iterations (should hit limit)
    for i in range(3):
        status = tracker.check_goal(
            user_goal="Test goal",
            original_intent=intent,
            observations=[f"Observation {i+1}"]
        )
    
    # Should now indicate max iterations reached
    assert status.achieved == False
    assert "Maximum iterations" in status.reasoning
    assert tracker.current_iteration == 3


def test_goal_tracker_reset():
    """Test that GoalTracker resets correctly"""
    tracker = GoalTracker(max_iterations=5)
    
    intent = IntentIR(
        goal="Test goal",
        requires_confirmation=False,
        steps=[]
    )
    
    # Do some iterations
    tracker.check_goal("Goal 1", intent, ["obs1"])
    tracker.check_goal("Goal 1", intent, ["obs2"])
    
    assert tracker.current_iteration == 2
    assert len(tracker.observation_history) == 2
    
    # Reset
    tracker.reset()
    
    assert tracker.current_iteration == 0
    assert tracker.observation_history == []


def test_goal_status_representation():
    """Test GoalStatus string representation"""
    status = GoalStatus(
        achieved=True,
        confidence=0.95,
        reasoning="Task completed successfully",
        next_steps=[]
    )
    
    repr_str = repr(status)
    assert "ACHIEVED" in repr_str
    assert "0.95" in repr_str


def test_build_reflection_prompt():
    """Test that reflection prompt is built correctly"""
    tracker = GoalTracker()
    
    intent = IntentIR(
        goal="List files",
        requires_confirmation=False,
        steps=[
            Step(tool="FileOps", action="scan", args={"path": "."}, risk=0)
        ]
    )
    
    observations = ["File1.txt", "File2.txt"]
    
    prompt = tracker._build_reflection_prompt(
        user_goal="Show me all files",
        original_intent=intent,
        observations=observations
    )
    
    # Check that all components are present
    assert "Show me all files" in prompt
    assert "FileOps.scan" in prompt  # Step action is in the prompt
    assert "File1.txt" in prompt
    assert "File2.txt" in prompt
    assert "ACHIEVED:" in prompt
    assert "CONFIDENCE:" in prompt
    assert "REASONING:" in prompt
    assert "NEXT_STEPS:" in prompt


def test_parse_reflection():
    """Test parsing of LLM reflection"""
    tracker = GoalTracker()
    
    # Test achieved reflection
    reflection_text = """
ACHIEVED: Yes
CONFIDENCE: 0.9
REASONING: All files were successfully listed
NEXT_STEPS: None
"""
    
    status = tracker._parse_reflection(reflection_text)
    
    assert status.achieved == True
    assert status.confidence == 0.9
    assert "successfully listed" in status.reasoning
    assert status.next_steps == []
    
    # Test not achieved reflection
    reflection_text = """
ACHIEVED: No
CONFIDENCE: 0.5
REASONING: Only partial listing obtained
NEXT_STEPS: Retry with recursive scan, Check permissions
"""
    
    status = tracker._parse_reflection(reflection_text)
    
    assert status.achieved == False
    assert status.confidence == 0.5
    assert "partial" in status.reasoning
    assert len(status.next_steps) == 2
    assert "Retry with recursive scan" in status.next_steps


def test_observation_accumulation():
    """Test that observations accumulate across iterations"""
    tracker = GoalTracker(max_iterations=10)
    
    intent = IntentIR(goal="Test", requires_confirmation=False, steps=[])
    
    # First iteration
    tracker.check_goal("Goal", intent, ["obs1", "obs2"])
    assert len(tracker.observation_history) == 2
    
    # Second iteration
    tracker.check_goal("Goal", intent, ["obs3"])
    assert len(tracker.observation_history) == 3
    
    # Third iteration
    tracker.check_goal("Goal", intent, ["obs4", "obs5"])
    assert len(tracker.observation_history) == 5

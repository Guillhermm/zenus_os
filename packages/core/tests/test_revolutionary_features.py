"""
Tests for revolutionary features: Tree of Thoughts, Prompt Evolution, Goal Inference
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from zenus_core.brain.tree_of_thoughts import TreeOfThoughts, SolutionPath, PathQuality, GoalType
from zenus_core.brain.prompt_evolution import PromptEvolution, PromptVersion
from zenus_core.brain.goal_inference import GoalInference, GoalType, ImplicitStep
from zenus_core.brain.llm.schemas import IntentIR, Step
from zenus_core.audit.logger import AuditLogger


class TestTreeOfThoughts:
    """Test Tree of Thoughts feature"""
    
    @pytest.fixture
    def mock_llm(self):
        llm = Mock()
        llm.generate = Mock(return_value='{"paths": [{"description": "Test path", "steps": [], "confidence": 0.8, "pros": ["Fast"], "cons": ["Limited"], "estimated_steps": 2, "estimated_time": "fast", "risk_level": "low", "reasoning": "Test"}]}')
        llm.translate_intent = Mock(return_value=IntentIR(
            goal="Test goal",
            steps=[Step(action="test", args={}, goal="test")],
            explanation="Test",
            expected_result="Success"
        ))
        return llm
    
    @pytest.fixture
    def mock_logger(self):
        logger = Mock(spec=AuditLogger)
        logger.log_info = Mock()
        logger.log_error = Mock()
        return logger
    
    @pytest.fixture
    def tot(self, mock_llm, mock_logger):
        return TreeOfThoughts(mock_llm, mock_logger)
    
    def test_explore_generates_paths(self, tot):
        """Test that explore generates multiple solution paths"""
        tree = tot.explore("deploy my app", num_paths=3)
        
        assert tree is not None
        assert len(tree.paths) > 0
        assert tree.selected_path is not None
        assert tree.exploration_time > 0
    
    def test_path_scoring(self, tot):
        """Test that path scoring works correctly"""
        path1 = SolutionPath(
            path_id=1, description="High confidence", intent=Mock(),
            confidence=0.9, pros=["Fast", "Safe"], cons=[], estimated_steps=2,
            estimated_time="fast", risk_level="low", quality=PathQuality.EXCELLENT,
            reasoning="Test"
        )
        
        path2 = SolutionPath(
            path_id=2, description="Low confidence", intent=Mock(),
            confidence=0.4, pros=["Flexible"], cons=["Slow", "Risky"], estimated_steps=5,
            estimated_time="slow", risk_level="high", quality=PathQuality.RISKY,
            reasoning="Test"
        )
        
        score1 = tot._calculate_path_score(path1)
        score2 = tot._calculate_path_score(path2)
        
        assert score1 > score2  # Higher confidence path should score better
    
    def test_fallback_on_error(self, tot, mock_llm):
        """Test fallback to single path if generation fails"""
        # Make generate fail
        mock_llm.generate = Mock(side_effect=Exception("API error"))
        
        tree = tot.explore("test command")
        
        # Should still return a tree with fallback path
        assert tree is not None
        assert len(tree.paths) >= 1
        assert tree.paths[0].description == "Standard approach (fallback)"


class TestPromptEvolution:
    """Test Prompt Evolution feature"""
    
    @pytest.fixture
    def temp_storage(self, tmp_path):
        return tmp_path / "prompts"
    
    @pytest.fixture
    def prompt_evo(self, temp_storage):
        return PromptEvolution(storage_dir=temp_storage)
    
    def test_get_prompt_returns_default(self, prompt_evo):
        """Test getting default prompt"""
        prompt, version_id = prompt_evo.get_prompt("test command")
        
        assert prompt is not None
        assert version_id == "default"
        assert "test command" in prompt
    
    def test_record_result_updates_stats(self, prompt_evo):
        """Test recording results updates version statistics"""
        # Get initial version
        _, version_id = prompt_evo.get_prompt("test")
        version = prompt_evo.versions[version_id]
        
        initial_uses = version.total_uses
        
        # Record success
        prompt_evo.record_result(
            version_id,
            "test command",
            {"goal": "test"},
            success=True,
            result="Success"
        )
        
        # Check stats updated
        assert version.total_uses == initial_uses + 1
        assert version.success_count == 1
    
    def test_domain_detection(self, prompt_evo):
        """Test domain detection from user input"""
        assert prompt_evo._detect_domain("git commit changes") == "git"
        assert prompt_evo._detect_domain("docker build image") == "docker"
        assert prompt_evo._detect_domain("copy file to directory") == "files"
        assert prompt_evo._detect_domain("just do something") is None
    
    def test_variant_creation(self, prompt_evo):
        """Test creating A/B test variants"""
        variant_id = prompt_evo.create_variant(
            "default",
            "Added error handling",
            "Should improve success rate"
        )
        
        assert variant_id in prompt_evo.variants
        assert variant_id in prompt_evo.active_tests
        assert prompt_evo.variants[variant_id].base_version == "default"
    
    def test_few_shot_examples(self, prompt_evo):
        """Test that successful examples are added"""
        _, version_id = prompt_evo.get_prompt("test")
        
        # Record successful execution with result
        prompt_evo.record_result(
            version_id,
            "list files",
            {"goal": "list files"},
            success=True,
            result="file1.txt\nfile2.txt"
        )
        
        version = prompt_evo.versions[version_id]
        assert len(version.examples) > 0
        assert version.examples[0]["input"] == "list files"


class TestGoalInference:
    """Test Goal Inference feature"""
    
    @pytest.fixture
    def mock_llm(self):
        return Mock()
    
    @pytest.fixture
    def mock_logger(self):
        logger = Mock(spec=AuditLogger)
        logger.log_info = Mock()
        logger.log_error = Mock()
        return logger
    
    @pytest.fixture
    def goal_inf(self, mock_llm, mock_logger):
        return GoalInference(mock_llm, mock_logger)
    
    def test_detect_deploy_goal(self, goal_inf):
        """Test detecting deployment goal"""
        goal_type = goal_inf._detect_goal_type("deploy my app to production")
        assert goal_type == GoalType.DEPLOY
    
    def test_detect_debug_goal(self, goal_inf):
        """Test detecting debug goal"""
        goal_type = goal_inf._detect_goal_type("fix the broken service")
        assert goal_type == GoalType.DEBUG
    
    def test_detect_setup_goal(self, goal_inf):
        """Test detecting setup goal"""
        goal_type = goal_inf._detect_goal_type("setup development environment")
        assert goal_type == GoalType.DEVELOP
    
    def test_infer_implicit_steps_for_deploy(self, goal_inf):
        """Test that deploy goal suggests safety steps"""
        suggestion = goal_inf.infer_goal("deploy my app to production")
        
        # Should include safety steps
        critical_steps = [s for s in suggestion.implicit_steps if s.importance == "critical"]
        assert len(critical_steps) > 0
        
        # Should include backup
        assert any("backup" in s.action.lower() for s in suggestion.implicit_steps)
        
        # Should include tests
        assert any("test" in s.action.lower() for s in suggestion.implicit_steps)
    
    def test_complete_workflow_includes_all_steps(self, goal_inf):
        """Test complete workflow includes explicit and implicit steps"""
        suggestion = goal_inf.infer_goal("deploy app")
        
        assert len(suggestion.complete_workflow) > len(suggestion.explicit_steps)
        assert len(suggestion.complete_workflow) >= len(suggestion.implicit_steps)
    
    def test_risk_assessment(self, goal_inf):
        """Test risk assessment for different goals"""
        deploy_suggestion = goal_inf.infer_goal("deploy to production")
        cleanup_suggestion = goal_inf.infer_goal("cleanup old files")
        test_suggestion = goal_inf.infer_goal("run tests")
        
        # Deploy and cleanup should be higher risk
        assert "HIGH" in deploy_suggestion.risk_assessment or "MEDIUM" in deploy_suggestion.risk_assessment
        
        # Test should be lower risk
        assert "LOW" in test_suggestion.risk_assessment
    
    def test_prerequisites_for_deploy(self, goal_inf):
        """Test that prerequisites are identified"""
        suggestion = goal_inf.infer_goal("deploy application")
        
        assert len(suggestion.prerequisites) > 0
        # Should mention tests or reviews
        prereq_text = " ".join(suggestion.prerequisites).lower()
        assert "test" in prereq_text or "review" in prereq_text
    
    def test_post_actions_suggested(self, goal_inf):
        """Test that post-actions are suggested"""
        suggestion = goal_inf.infer_goal("deploy app")
        
        assert len(suggestion.post_actions) > 0
        # Should mention monitoring or verification
        post_text = " ".join(suggestion.post_actions).lower()
        assert "monitor" in post_text or "check" in post_text


class TestIntegration:
    """Integration tests for revolutionary features"""
    
    def test_all_features_work_together(self):
        """Test that all three features can coexist"""
        mock_llm = Mock()
        mock_llm.generate = Mock(return_value='{"paths": [{"description": "Test", "steps": [], "confidence": 0.8, "pros": [], "cons": [], "estimated_steps": 1, "estimated_time": "fast", "risk_level": "low", "reasoning": "Test"}]}')
        mock_llm.translate_intent = Mock(return_value=IntentIR(
            goal="Test", steps=[], explanation="", expected_result=""
        ))
        
        mock_logger = Mock(spec=AuditLogger)
        mock_logger.log_info = Mock()
        mock_logger.log_error = Mock()
        
        # Create all three features
        tot = TreeOfThoughts(mock_llm, mock_logger)
        prompt_evo = PromptEvolution()
        goal_inf = GoalInference(mock_llm, mock_logger)
        
        # Use them in sequence
        goal_suggestion = goal_inf.infer_goal("deploy app")
        prompt, version_id = prompt_evo.get_prompt("deploy app")
        tree = tot.explore("deploy app", num_paths=2)
        
        # All should complete without errors
        assert goal_suggestion is not None
        assert prompt is not None
        assert tree is not None
        assert len(tree.paths) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

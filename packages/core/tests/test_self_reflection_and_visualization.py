"""
Tests for Self-Reflection and Data Visualization features
"""

import pytest
from unittest.mock import Mock, MagicMock
import json


class TestSelfReflection:
    """Test Self-Reflection feature"""
    
    @pytest.fixture
    def mock_llm(self):
        llm = Mock()
        llm.generate = Mock(return_value=json.dumps({
            "overall_confidence": 0.85,
            "step_reflections": [
                {
                    "step_index": 0,
                    "confidence": 0.9,
                    "issues": ["File might not exist"],
                    "assumptions": ["File path is valid"],
                    "risks": ["File might be large"],
                    "alternatives": ["Check file exists first"],
                    "prerequisites": ["Read permissions"],
                    "reasoning": "Step seems straightforward"
                }
            ],
            "critical_issues": [],
            "should_ask_user": False,
            "questions_for_user": [],
            "suggested_improvements": ["Add file validation"],
            "risk_assessment": "Low risk operation",
            "reasoning": "Plan looks good overall"
        }))
        return llm
    
    @pytest.fixture
    def mock_logger(self):
        logger = Mock()
        logger.log_info = Mock()
        logger.log_error = Mock()
        return logger
    
    @pytest.fixture
    def self_reflection(self, mock_llm, mock_logger):
        from zenus_core.brain.self_reflection import SelfReflection
        return SelfReflection(mock_llm, mock_logger)
    
    def test_reflection_creation(self, self_reflection):
        """Test creating reflection"""
        from zenus_core.brain.llm.schemas import IntentIR, Step
        
        intent = IntentIR(
            goal="Read file",
            steps=[Step(action="read_file", args={"path": "/tmp/test.txt"}, goal="Read test file")],
            explanation="Reading a file",
            expected_result="File contents"
        )
        
        reflection = self_reflection.reflect_on_plan("read the file", intent)
        
        assert reflection is not None
        assert reflection.overall_confidence_score == 0.85
        assert len(reflection.step_reflections) > 0
    
    def test_should_proceed(self, self_reflection):
        """Test should_proceed logic"""
        from zenus_core.brain.self_reflection import PlanReflection, ConfidenceLevel, StepReflection
        from zenus_core.brain.llm.schemas import IntentIR, Step
        
        intent = IntentIR(goal="test", steps=[Step(action="test", args={}, goal="test")], explanation="", expected_result="")
        
        # High confidence - should proceed
        reflection = PlanReflection(
            overall_confidence=ConfidenceLevel.HIGH,
            overall_confidence_score=0.8,
            step_reflections=[],
            critical_issues=[],
            should_ask_user=False,
            questions_for_user=[],
            suggested_improvements=[],
            risk_assessment="Low",
            estimated_success_probability=0.8,
            reasoning="Good"
        )
        
        should_proceed, reason = self_reflection.should_proceed(reflection)
        assert should_proceed is True
        
        # Low confidence - should NOT proceed
        reflection.overall_confidence = ConfidenceLevel.LOW
        reflection.overall_confidence_score = 0.3
        
        should_proceed, reason = self_reflection.should_proceed(reflection)
        assert should_proceed is False
    
    def test_confidence_levels(self, self_reflection):
        """Test confidence score to level conversion"""
        from zenus_core.brain.self_reflection import ConfidenceLevel
        
        assert self_reflection._score_to_level(0.95) == ConfidenceLevel.VERY_HIGH
        assert self_reflection._score_to_level(0.8) == ConfidenceLevel.HIGH
        assert self_reflection._score_to_level(0.6) == ConfidenceLevel.MEDIUM
        assert self_reflection._score_to_level(0.4) == ConfidenceLevel.LOW
        assert self_reflection._score_to_level(0.2) == ConfidenceLevel.VERY_LOW


class TestDataVisualization:
    """Test Data Visualization feature"""
    
    def test_chart_generation(self):
        """Test creating a chart"""
        from zenus_core.visualization.chart_generator import ChartGenerator, ChartType
        
        generator = ChartGenerator()
        
        # Simple bar chart data
        data = {"A": 10, "B": 20, "C": 15}
        
        chart_path = generator.create_chart(data, ChartType.BAR, title="Test Chart")
        
        assert chart_path.endswith(".png")
        import os
        assert os.path.exists(chart_path)
        
        # Cleanup
        os.remove(chart_path)
    
    def test_data_type_detection(self):
        """Test auto-detecting chart type"""
        from zenus_core.visualization.chart_generator import ChartGenerator, ChartType
        
        generator = ChartGenerator()
        
        # Numeric list -> histogram or line
        assert generator._detect_chart_type([1, 2, 3, 4, 5]) == ChartType.LINE
        assert generator._detect_chart_type(list(range(30))) == ChartType.HISTOGRAM
        
        # Dict with numbers -> bar or pie
        assert generator._detect_chart_type({"A": 1, "B": 2, "C": 3}) == ChartType.PIE
        assert generator._detect_chart_type({f"Item{i}": i for i in range(10)}) == ChartType.BAR
    
    def test_table_formatting(self):
        """Test formatting tables"""
        from zenus_core.visualization.table_formatter import TableFormatter
        
        formatter = TableFormatter()
        
        # List of dicts
        data = [
            {"Name": "Alice", "Age": 30, "City": "NYC"},
            {"Name": "Bob", "Age": 25, "City": "SF"}
        ]
        
        table_str = formatter.format_table(data, title="People")
        
        assert "Alice" in table_str
        assert "Bob" in table_str
        assert "People" in table_str
    
    def test_dict_property_table(self):
        """Test formatting dict as properties"""
        from zenus_core.visualization.table_formatter import TableFormatter
        
        formatter = TableFormatter()
        
        data = {"OS": "Linux", "Version": "5.15", "Arch": "x86_64"}
        
        table_str = formatter.format_dict_as_properties(data, title="System Info")
        
        assert "Linux" in table_str
        assert "System Info" in table_str
    
    def test_diff_viewer(self):
        """Test showing diffs"""
        from zenus_core.visualization.diff_viewer import DiffViewer
        
        viewer = DiffViewer()
        
        before = "Hello\nWorld\n"
        after = "Hello\nPython\nWorld\n"
        
        diff_str = viewer.show_diff(before, after, title="Test Diff")
        
        assert "Python" in diff_str
        assert "Test Diff" in diff_str
    
    def test_dict_diff(self):
        """Test dict diffing"""
        from zenus_core.visualization.diff_viewer import DiffViewer
        
        viewer = DiffViewer()
        
        before = {"a": 1, "b": 2, "c": 3}
        after = {"a": 1, "b": 5, "d": 4}  # b changed, c removed, d added
        
        diff_str = viewer._show_dict_diff(before, after, "Dict Changes")
        
        assert "Added" in diff_str or "Removed" in diff_str or "Changed" in diff_str
    
    def test_visualizer_auto_detection(self):
        """Test visualizer data type detection"""
        from zenus_core.visualization.visualizer import Visualizer, DataType
        
        viz = Visualizer()
        
        # Numeric series
        assert viz._detect_data_type([1, 2, 3, 4]) == DataType.NUMERIC_SERIES
        
        # Categorical
        assert viz._detect_data_type({"A": 10, "B": 20}) == DataType.CATEGORICAL
        
        # Tabular
        assert viz._detect_data_type([{"a": 1, "b": 2}]) == DataType.TABULAR
        
        # Properties
        assert viz._detect_data_type({"name": "test", "count": 5}) == DataType.DICT_PROPERTIES


class TestIntegration:
    """Integration tests"""
    
    def test_features_coexist(self):
        """Test that both features can coexist"""
        from zenus_core.brain.self_reflection import SelfReflection
        from zenus_core.visualization.visualizer import Visualizer
        
        mock_llm = Mock()
        mock_llm.generate = Mock(return_value='{"overall_confidence": 0.8, "step_reflections": [], "critical_issues": [], "should_ask_user": false, "questions_for_user": [], "suggested_improvements": [], "risk_assessment": "Low", "reasoning": "Test"}')
        
        mock_logger = Mock()
        mock_logger.log_info = Mock()
        mock_logger.log_error = Mock()
        
        # Create both
        reflection = SelfReflection(mock_llm, mock_logger)
        viz = Visualizer()
        
        assert reflection is not None
        assert viz is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

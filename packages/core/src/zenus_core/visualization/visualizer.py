"""
Main Visualizer

Coordinates all visualization capabilities.
Auto-detects data type and creates appropriate visualization.
"""

from typing import Union, List, Dict, Optional, Any
from enum import Enum

from zenus_core.visualization.chart_generator import ChartGenerator, ChartType
from zenus_core.visualization.table_formatter import TableFormatter, TableStyle
from zenus_core.visualization.diff_viewer import DiffViewer


class DataType(Enum):
    """Detected data types"""
    NUMERIC_SERIES = "numeric_series"    # List of numbers
    CATEGORICAL = "categorical"           # Categories with values
    TABULAR = "tabular"                  # Table data
    TEXT = "text"                        # Plain text
    DICT_PROPERTIES = "dict_properties"  # Key-value pairs
    DIFF = "diff"                        # Before/after comparison
    UNKNOWN = "unknown"


class Visualizer:
    """
    Main visualization coordinator
    
    Features:
    - Auto-detects data type
    - Creates appropriate visualization
    - Handles charts, tables, diffs
    - Smart formatting
    """
    
    def __init__(self):
        self.chart_gen = ChartGenerator()
        self.table_fmt = TableFormatter()
        self.diff_viewer = DiffViewer()
    
    def visualize(
        self,
        data: Any,
        title: Optional[str] = None,
        output_format: str = "auto"  # auto, chart, table, text
    ) -> str:
        """
        Automatically visualize data
        
        Args:
            data: Data to visualize
            title: Title for visualization
            output_format: Force specific format or auto-detect
        
        Returns:
            Formatted output (text with ANSI colors or path to chart)
        """
        # Detect data type
        data_type = self._detect_data_type(data)
        
        # Choose visualization based on type and format
        if output_format == "auto":
            return self._auto_visualize(data, data_type, title)
        elif output_format == "chart":
            return self._create_chart(data, title)
        elif output_format == "table":
            return self._create_table(data, title)
        else:
            return str(data)
    
    def _detect_data_type(self, data: Any) -> DataType:
        """Detect what type of data this is"""
        
        # List of numbers -> numeric series
        if isinstance(data, list) and data and all(isinstance(x, (int, float)) for x in data):
            return DataType.NUMERIC_SERIES
        
        # Dict with numeric values -> categorical
        elif isinstance(data, dict) and data and all(isinstance(v, (int, float)) for v in data.values()):
            return DataType.CATEGORICAL
        
        # List of dicts -> tabular
        elif isinstance(data, list) and data and isinstance(data[0], dict):
            return DataType.TABULAR
        
        # List of lists/tuples -> tabular
        elif isinstance(data, list) and data and isinstance(data[0], (list, tuple)):
            return DataType.TABULAR
        
        # Dict with mixed values -> properties
        elif isinstance(data, dict) and not all(isinstance(v, (list, dict)) for v in data.values()):
            return DataType.DICT_PROPERTIES
        
        # String -> text
        elif isinstance(data, str):
            return DataType.TEXT
        
        return DataType.UNKNOWN
    
    def _auto_visualize(self, data: Any, data_type: DataType, title: Optional[str]) -> str:
        """Auto-select best visualization"""
        
        if data_type == DataType.NUMERIC_SERIES:
            # Numbers -> chart
            if len(data) > 10:
                # Many values -> histogram
                chart_path = self.chart_gen.create_chart(
                    data,
                    ChartType.HISTOGRAM,
                    title=title or "Distribution"
                )
                return f"📊 Chart saved to: {chart_path}"
            else:
                # Few values -> line chart
                chart_path = self.chart_gen.create_chart(
                    data,
                    ChartType.LINE,
                    title=title or "Values"
                )
                return f"📊 Chart saved to: {chart_path}"
        
        elif data_type == DataType.CATEGORICAL:
            # Categories -> bar or pie chart
            if len(data) <= 6:
                # Few categories -> pie chart
                chart_path = self.chart_gen.create_chart(
                    data,
                    ChartType.PIE,
                    title=title or "Distribution"
                )
                return f"📊 Chart saved to: {chart_path}"
            else:
                # Many categories -> bar chart
                chart_path = self.chart_gen.create_chart(
                    data,
                    ChartType.BAR,
                    title=title or "Comparison"
                )
                return f"📊 Chart saved to: {chart_path}"
        
        elif data_type == DataType.TABULAR:
            # Tabular data -> table
            return self.table_fmt.format_table(data, title=title)
        
        elif data_type == DataType.DICT_PROPERTIES:
            # Properties -> property table
            return self.table_fmt.format_dict_as_properties(data, title=title)
        
        elif data_type == DataType.TEXT:
            # Text -> just return it
            return data
        
        else:
            # Unknown -> try table format
            try:
                return self.table_fmt.format_table(data, title=title)
            except:
                return str(data)
    
    def _create_chart(self, data: Any, title: Optional[str]) -> str:
        """Force chart creation"""
        chart_path = self.chart_gen.create_chart(
            data,
            ChartType.AUTO,
            title=title
        )
        return f"📊 Chart saved to: {chart_path}"
    
    def _create_table(self, data: Any, title: Optional[str]) -> str:
        """Force table creation"""
        return self.table_fmt.format_table(data, title=title)
    
    def show_diff(
        self,
        before: Any,
        after: Any,
        title: Optional[str] = None
    ) -> str:
        """Show diff between before and after"""
        return self.diff_viewer.show_diff(before, after, title=title)
    
    def show_summary_stats(self, data: List[Union[int, float]]) -> str:
        """Show statistical summary of numeric data"""
        import statistics
        
        if not data or not all(isinstance(x, (int, float)) for x in data):
            return "Data must be numeric"
        
        stats = {
            "Count": len(data),
            "Min": min(data),
            "Max": max(data),
            "Mean": statistics.mean(data),
            "Median": statistics.median(data),
            "Std Dev": statistics.stdev(data) if len(data) > 1 else 0
        }
        
        return self.table_fmt.format_dict_as_properties(stats, title="Statistics")
    
    def create_comparison_table(
        self,
        items: List[Dict],
        compare_keys: Optional[List[str]] = None
    ) -> str:
        """Create comparison table highlighting differences"""
        
        if not items:
            return "No items to compare"
        
        # If compare_keys not specified, use all keys
        if not compare_keys:
            all_keys = set()
            for item in items:
                all_keys.update(item.keys())
            compare_keys = sorted(all_keys)
        
        # Build comparison data
        comparison_data = []
        for key in compare_keys:
            row = {"Property": key}
            for i, item in enumerate(items):
                row[f"Item {i+1}"] = item.get(key, "—")
            comparison_data.append(row)
        
        return self.table_fmt.format_table(
            comparison_data,
            title="Comparison"
        )


# Singleton instance
_visualizer_instance = None


def get_visualizer() -> Visualizer:
    """Get or create visualizer instance"""
    global _visualizer_instance
    if _visualizer_instance is None:
        _visualizer_instance = Visualizer()
    return _visualizer_instance

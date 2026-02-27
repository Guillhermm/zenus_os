"""
Chart Generator

Auto-generates charts from data using matplotlib.
Detects data type and creates appropriate visualizations.
"""

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict, Optional, Union, Tuple
from enum import Enum
from pathlib import Path
import tempfile


class ChartType(Enum):
    """Supported chart types"""
    AUTO = "auto"          # Auto-detect best chart
    LINE = "line"          # Line chart
    BAR = "bar"            # Bar chart
    SCATTER = "scatter"    # Scatter plot
    PIE = "pie"            # Pie chart
    HISTOGRAM = "histogram"  # Histogram
    HEATMAP = "heatmap"    # Heatmap


class ChartGenerator:
    """
    Automatically generates charts from data
    
    Features:
    - Auto-detects appropriate chart type
    - Handles various data formats
    - Beautiful default styling
    - Saves to file or displays
    """
    
    def __init__(self):
        # Set nice default style
        plt.style.use('seaborn-v0_8-darkgrid' if 'seaborn-v0_8-darkgrid' in plt.style.available else 'default')
        
        # Default figure size
        self.figsize = (10, 6)
        self.dpi = 100
    
    def create_chart(
        self,
        data: Union[List, Dict, np.ndarray],
        chart_type: ChartType = ChartType.AUTO,
        title: Optional[str] = None,
        xlabel: Optional[str] = None,
        ylabel: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> str:
        """
        Create a chart from data
        
        Args:
            data: Data to visualize (list, dict, or numpy array)
            chart_type: Type of chart (or AUTO to detect)
            title: Chart title
            xlabel: X-axis label
            ylabel: Y-axis label
            output_path: Where to save (or temp file if None)
        
        Returns:
            Path to generated chart image
        """
        # Auto-detect chart type if needed
        if chart_type == ChartType.AUTO:
            chart_type = self._detect_chart_type(data)
        
        # Create figure
        fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)
        
        # Generate appropriate chart
        if chart_type == ChartType.LINE:
            self._create_line_chart(ax, data)
        elif chart_type == ChartType.BAR:
            self._create_bar_chart(ax, data)
        elif chart_type == ChartType.SCATTER:
            self._create_scatter_plot(ax, data)
        elif chart_type == ChartType.PIE:
            self._create_pie_chart(ax, data)
        elif chart_type == ChartType.HISTOGRAM:
            self._create_histogram(ax, data)
        elif chart_type == ChartType.HEATMAP:
            self._create_heatmap(ax, data)
        else:
            # Fallback to bar chart
            self._create_bar_chart(ax, data)
        
        # Set labels
        if title:
            ax.set_title(title, fontsize=14, fontweight='bold')
        if xlabel:
            ax.set_xlabel(xlabel, fontsize=11)
        if ylabel:
            ax.set_ylabel(ylabel, fontsize=11)
        
        # Improve layout
        plt.tight_layout()
        
        # Save to file
        if not output_path:
            tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            output_path = tmp.name
        
        plt.savefig(output_path, bbox_inches='tight', dpi=self.dpi)
        plt.close()
        
        return output_path
    
    def _detect_chart_type(self, data: Union[List, Dict]) -> ChartType:
        """Auto-detect best chart type for data"""
        
        if isinstance(data, dict):
            # Dict with numbers -> bar or pie chart
            values = list(data.values())
            if all(isinstance(v, (int, float)) for v in values):
                if len(values) <= 5:
                    return ChartType.PIE
                else:
                    return ChartType.BAR
        
        elif isinstance(data, list):
            # List of numbers -> histogram or line
            if all(isinstance(v, (int, float)) for v in data):
                if len(data) > 20:
                    return ChartType.HISTOGRAM
                else:
                    return ChartType.LINE
            
            # List of tuples/lists -> scatter or line
            elif all(isinstance(v, (list, tuple)) and len(v) == 2 for v in data):
                return ChartType.SCATTER
        
        # Default
        return ChartType.BAR
    
    def _create_line_chart(self, ax, data):
        """Create line chart"""
        if isinstance(data, dict):
            x = list(data.keys())
            y = list(data.values())
        elif isinstance(data, list):
            x = list(range(len(data)))
            y = data
        else:
            y = data
            x = list(range(len(y)))
        
        ax.plot(x, y, marker='o', linewidth=2, markersize=6)
        ax.grid(True, alpha=0.3)
    
    def _create_bar_chart(self, ax, data):
        """Create bar chart"""
        if isinstance(data, dict):
            labels = list(data.keys())
            values = list(data.values())
        elif isinstance(data, list):
            labels = [str(i) for i in range(len(data))]
            values = data
        else:
            labels = [str(i) for i in range(len(data))]
            values = list(data)
        
        # Truncate long labels
        labels = [l[:20] + '...' if len(str(l)) > 20 else str(l) for l in labels]
        
        bars = ax.bar(labels, values, color='#3498db', alpha=0.8)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}',
                   ha='center', va='bottom', fontsize=9)
        
        # Rotate labels if many
        if len(labels) > 5:
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    def _create_scatter_plot(self, ax, data):
        """Create scatter plot"""
        if isinstance(data, list) and all(isinstance(v, (list, tuple)) for v in data):
            x = [v[0] for v in data]
            y = [v[1] for v in data]
        else:
            # Assume data has x and y
            x = data.get('x', range(len(data.get('y', []))))
            y = data.get('y', [])
        
        ax.scatter(x, y, alpha=0.6, s=50, color='#e74c3c')
        ax.grid(True, alpha=0.3)
    
    def _create_pie_chart(self, ax, data):
        """Create pie chart"""
        if isinstance(data, dict):
            labels = list(data.keys())
            values = list(data.values())
        else:
            labels = [f"Item {i}" for i in range(len(data))]
            values = data
        
        # Truncate long labels
        labels = [l[:15] + '...' if len(str(l)) > 15 else str(l) for l in labels]
        
        colors = plt.cm.Set3(range(len(values)))
        ax.pie(values, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
        ax.axis('equal')
    
    def _create_histogram(self, ax, data):
        """Create histogram"""
        if isinstance(data, dict):
            data = list(data.values())
        
        ax.hist(data, bins=min(20, len(data)//5 + 1), color='#2ecc71', alpha=0.7, edgecolor='black')
        ax.grid(True, alpha=0.3, axis='y')
    
    def _create_heatmap(self, ax, data):
        """Create heatmap (requires 2D data)"""
        if isinstance(data, list) and all(isinstance(row, list) for row in data):
            matrix = np.array(data)
        elif isinstance(data, np.ndarray) and len(data.shape) == 2:
            matrix = data
        else:
            # Can't create heatmap, fall back to bar
            self._create_bar_chart(ax, data)
            return
        
        im = ax.imshow(matrix, cmap='YlOrRd', aspect='auto')
        plt.colorbar(im, ax=ax)
        
        # Add values
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                text = ax.text(j, i, f'{matrix[i, j]:.1f}',
                              ha="center", va="center", color="black", fontsize=8)


def create_chart(
    data: Union[List, Dict],
    chart_type: ChartType = ChartType.AUTO,
    **kwargs
) -> str:
    """
    Quick function to create a chart
    
    Returns:
        Path to generated chart image
    """
    generator = ChartGenerator()
    return generator.create_chart(data, chart_type, **kwargs)

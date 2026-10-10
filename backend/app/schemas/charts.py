"""Pydantic schemas for data visualization and Recharts rendering."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ChartType(str, Enum):
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    SCATTER = "scatter"
    AREA = "area"
    HISTOGRAM = "histogram"


class ChartSeries(BaseModel):
    """Specification for a visual series in the chart."""
    key: str = Field(..., description="Data key in records for the Y value or metric")
    name: str = Field(..., description="Human-readable legend title")
    color: Optional[str] = Field(default=None, description="Hex/HSL color override")


class ChartSpec(BaseModel):
    """Validated structured chart payload consumable by frontend Recharts."""
    chart_type: ChartType = Field(..., description="Visualization type (bar, line, pie, scatter, area, histogram)")
    title: str = Field(..., description="Chart headline")
    description: Optional[str] = Field(default=None, description="Analytical context or subtitle")
    x_axis_key: str = Field(..., description="Field name used for X-axis categories or timeline")
    x_axis_label: Optional[str] = Field(default=None, description="Label displayed along X axis")
    y_axis_label: Optional[str] = Field(default=None, description="Label displayed along Y axis")
    series: List[ChartSeries] = Field(default_factory=list, description="One or more series to plot")
    data: List[Dict[str, Any]] = Field(..., description="Aggregated rows ready for plotting")

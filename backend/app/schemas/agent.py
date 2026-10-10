"""Schemas for chat interactions, agent execution traces, and structured outputs."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.schemas.charts import ChartSpec


class ChatRequest(BaseModel):
    """User prompt sent to the analyst agent."""
    message: str = Field(..., min_length=1, description="Natural language question or request")
    confirmed_mappings: Optional[Dict[str, str]] = Field(
        default=None,
        description="Optional overrides mapping semantic roles to column names"
    )


class ToolCallRecord(BaseModel):
    """Trace record of an individual tool call executed by the agent."""
    tool_name: str = Field(..., description="Name of executed deterministic analysis tool")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Arguments supplied by LLM")
    result_summary: str = Field(..., description="Brief outcome or status summary")
    success: bool = Field(default=True, description="Whether tool execution succeeded")


class DataTable(BaseModel):
    """Structured tabular response for direct rendering."""
    title: Optional[str] = None
    columns: List[str]
    rows: List[Dict[str, Any]]
    total_count: int


class ChatResponse(BaseModel):
    """Rich structured response returned to the frontend."""
    dataset_id: str
    message: str = Field(..., description="Business explanation and answer from agent")
    data_table: Optional[DataTable] = Field(default=None, description="Tabular results if relevant")
    chart_spec: Optional[ChartSpec] = Field(default=None, description="Visual chart configuration if requested")
    tool_calls: List[ToolCallRecord] = Field(default_factory=list, description="Audit log of tools executed")
    follow_up_suggestions: List[str] = Field(default_factory=list, description="Relevant next questions to ask")
    limitations: Optional[List[str]] = Field(default=None, description="Disclaimers, assumptions, or missing data notes")


class MappingConfirmationRequest(BaseModel):
    """Request to update or confirm semantic mappings for a dataset."""
    mappings: Dict[str, str] = Field(
        ...,
        description="Dictionary mapping semantic roles (e.g. 'revenue') to actual column names"
    )

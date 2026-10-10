"""Pydantic models for CSV profiling, semantic mapping, and dataset preview."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ColumnGeneralType(str, Enum):
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    TEXT = "text"
    UNKNOWN = "unknown"


class SemanticRole(str, Enum):
    REVENUE = "revenue"
    UNIT_PRICE = "unit_price"
    QUANTITY = "quantity"
    ORDER_ID = "order_id"
    ORDER_DATE = "order_date"
    PRODUCT = "product"
    CATEGORY = "category"
    CUSTOMER_ID = "customer_id"
    REGION = "region"
    DISCOUNT = "discount"
    PROFIT = "profit"
    SHIPPING_COST = "shipping_cost"
    RATING = "rating"
    OTHER = "other"


class NumericStats(BaseModel):
    min: Optional[float] = None
    max: Optional[float] = None
    mean: Optional[float] = None
    median: Optional[float] = None
    std: Optional[float] = None
    q25: Optional[float] = None
    q75: Optional[float] = None


class ColumnProfile(BaseModel):
    name: str = Field(..., description="Original column name in dataset")
    data_type: str = Field(..., description="Pandas dtype as string")
    general_type: ColumnGeneralType = Field(..., description="Normalized high-level column category")
    missing_count: int = Field(..., description="Count of null or empty cells")
    missing_percentage: float = Field(..., description="Percentage of null values (0-100)")
    unique_count: int = Field(..., description="Number of unique values in column")
    sample_values: List[Any] = Field(default_factory=list, description="Up to 5 representative non-null values")
    suggested_role: Optional[SemanticRole] = Field(default=None, description="Inferred semantic e-commerce role")
    stats: Optional[NumericStats] = Field(default=None, description="Descriptive statistics if numeric")


class SemanticMapping(BaseModel):
    column_name: str = Field(..., description="Original dataset column name")
    mapped_role: SemanticRole = Field(..., description="Assigned business semantic role")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence of the mapping")
    is_confirmed: bool = Field(default=True, description="Whether user or system confirmed this mapping")
    notes: Optional[str] = Field(default=None, description="Explanation or ambiguity note")


class DatasetProfile(BaseModel):
    dataset_id: str = Field(..., description="Unique UUID for this uploaded session")
    filename: str = Field(..., description="Name of uploaded CSV file")
    file_size_bytes: int = Field(..., description="Original file size in bytes")
    row_count: int = Field(..., description="Total rows in dataset")
    column_count: int = Field(..., description="Total columns in dataset")
    duplicate_rows: int = Field(..., description="Count of duplicate rows")
    columns: List[ColumnProfile] = Field(..., description="Detailed profile per column")
    semantic_mappings: Dict[str, SemanticMapping] = Field(
        default_factory=dict,
        description="Active mapping from semantic role (or column name) to semantic assignment"
    )
    suggested_questions: List[str] = Field(default_factory=list, description="Contextual sample questions")
    created_at: str = Field(..., description="ISO timestamp of upload")


class DatasetPreview(BaseModel):
    dataset_id: str = Field(..., description="Unique UUID for dataset")
    filename: str = Field(..., description="Original CSV filename")
    total_rows: int = Field(..., description="Total rows in full dataset")
    columns: List[str] = Field(..., description="Ordered list of column names")
    preview_rows: List[Dict[str, Any]] = Field(..., description="First N rows formatted as dicts")

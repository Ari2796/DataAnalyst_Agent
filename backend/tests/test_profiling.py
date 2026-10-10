"""Tests for data profiling, column classification, and semantic schema mapping."""

import pandas as pd
from app.schemas.dataset import ColumnGeneralType, SemanticRole
from app.services.profiling_service import ProfilingService
from app.services.schema_mapping_service import SchemaMappingService


def test_profiling_service_structure(sample_df: pd.DataFrame):
    """Verifies that profiling extracts correct row counts, column counts, and types."""
    profile = ProfilingService.profile_dataset(
        dataset_id="test-123",
        filename="ecommerce.csv",
        file_size_bytes=1024,
        df=sample_df,
    )

    assert profile.dataset_id == "test-123"
    assert profile.row_count == len(sample_df)
    assert profile.column_count == len(sample_df.columns)
    assert profile.duplicate_rows == 0

    col_map = {c.name: c for c in profile.columns}
    assert col_map["sales_amount"].general_type == ColumnGeneralType.NUMERIC
    assert col_map["category"].general_type == ColumnGeneralType.CATEGORICAL
    assert col_map["order_date"].general_type == ColumnGeneralType.DATETIME

    # Verify descriptive statistics
    sales_stats = col_map["sales_amount"].stats
    assert sales_stats is not None
    assert sales_stats.min == round(sample_df["sales_amount"].min(), 4)
    assert sales_stats.max == round(sample_df["sales_amount"].max(), 4)
    assert sales_stats.mean == round(sample_df["sales_amount"].mean(), 4)


def test_semantic_role_detection(sample_df: pd.DataFrame):
    """Verifies heuristic and keyword detection of e-commerce business roles."""
    profile = ProfilingService.profile_dataset(
        dataset_id="test-456",
        filename="ecommerce.csv",
        file_size_bytes=1024,
        df=sample_df,
    )

    mappings = profile.semantic_mappings
    assert "revenue" in mappings
    assert mappings["revenue"].column_name == "sales_amount"
    assert mappings["revenue"].mapped_role == SemanticRole.REVENUE

    assert "order_id" in mappings
    assert mappings["order_id"].column_name == "order_id"

    assert "product" in mappings
    assert mappings["product"].column_name == "product_name"

    assert "category" in mappings
    assert mappings["category"].column_name == "category"

    assert "region" in mappings
    assert mappings["region"].column_name == "region"


def test_schema_mapping_resolution(sample_df: pd.DataFrame):
    """Verifies resolution of semantic roles to concrete columns."""
    profile = ProfilingService.profile_dataset(
        dataset_id="test-789",
        filename="ecommerce.csv",
        file_size_bytes=1024,
        df=sample_df,
    )

    # Resolving 'revenue' should map to 'sales_amount'
    resolved, err = SchemaMappingService.resolve_column(
        df=sample_df, identifier="revenue", profile=profile
    )
    assert err is None
    assert resolved == "sales_amount"

    # Resolving direct column name 'region'
    resolved, err = SchemaMappingService.resolve_column(
        df=sample_df, identifier="region", profile=profile
    )
    assert err is None
    assert resolved == "region"

    # Non-existent column returns controlled error
    resolved, err = SchemaMappingService.resolve_column(
        df=sample_df, identifier="non_existent_field", profile=profile
    )
    assert resolved is None
    assert "Could not resolve 'non_existent_field'" in err

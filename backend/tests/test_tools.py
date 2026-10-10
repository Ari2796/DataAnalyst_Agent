"""Tests for deterministic analysis service and tool calculations."""

import pandas as pd
from app.services.analysis_service import AnalysisService
from app.services.chart_service import ChartService
from app.services.profiling_service import ProfilingService
from app.services.session_service import session_service
from app.agent.tools import execute_tool


def test_calculate_metric_total_revenue(sample_df: pd.DataFrame):
    """Verifies that total revenue matches exact pandas sum."""
    expected_sum = round(float(sample_df["sales_amount"].sum()), 4)
    res = AnalysisService.calculate_metric(
        df=sample_df,
        metric_column="sales_amount",
        aggregation="sum",
    )
    assert res["value"] == expected_sum
    assert res["rows_evaluated"] == len(sample_df)


def test_calculate_metric_with_region_filter(sample_df: pd.DataFrame):
    """Verifies filtered metric computation for region == 'North'."""
    expected_north_sum = round(float(sample_df[sample_df["region"] == "North"]["sales_amount"].sum()), 4)
    res = AnalysisService.calculate_metric(
        df=sample_df,
        metric_column="sales_amount",
        aggregation="sum",
        filter_column="region",
        filter_operator="==",
        filter_value="North",
    )
    assert res["value"] == expected_north_sum
    assert res["rows_evaluated"] == len(sample_df[sample_df["region"] == "North"])


def test_group_and_aggregate_category_revenue(sample_df: pd.DataFrame):
    """Verifies grouping by category and aggregating sales_amount."""
    res = AnalysisService.group_and_aggregate(
        df=sample_df,
        group_by="category",
        metric_column="sales_amount",
        aggregation="sum",
        sort_descending=True,
    )
    results = res["results"]
    assert len(results) > 0
    # Verify sorted descending
    values = [r["sales_amount"] for r in results]
    assert values == sorted(values, reverse=True)


def test_get_top_n_products(sample_df: pd.DataFrame):
    """Verifies top-N ranking returns highest products."""
    res = AnalysisService.get_top_n(
        df=sample_df,
        entity_column="product_name",
        metric_column="sales_amount",
        n=5,
    )
    results = res["results"]
    assert len(results) == 5
    top_product = results[0]["product_name"]
    # Check that top product has highest cumulative revenue
    prod_totals = sample_df.groupby("product_name")["sales_amount"].sum()
    assert top_product == prod_totals.idxmax()


def test_compare_groups(sample_df: pd.DataFrame):
    """Verifies head-to-head comparison between regions North and South."""
    res = AnalysisService.compare_groups(
        df=sample_df,
        dimension_column="region",
        group_a="North",
        group_b="South",
        metric_column="sales_amount",
    )
    assert res["dimension"] == "region"
    assert "North" in res["group_a"]["name"]
    assert "South" in res["group_b"]["name"]
    assert res["absolute_difference"] == round(res["group_a"]["value"] - res["group_b"]["value"], 4)


def test_analyze_time_trend(sample_df: pd.DataFrame):
    """Verifies monthly aggregation across order_date."""
    res = AnalysisService.analyze_time_trend(
        df=sample_df,
        metric_column="sales_amount",
        date_column="order_date",
        freq="M",
    )
    trend = res["trend"]
    assert len(trend) >= 3  # Jan, Feb, Mar, Apr
    periods = [t["period"] for t in trend]
    assert "2024-01" in periods
    assert "2024-02" in periods


def test_detect_anomalies(sample_df: pd.DataFrame):
    """Verifies IQR outlier detection."""
    res = AnalysisService.detect_basic_anomalies(
        df=sample_df,
        metric_column="sales_amount",
    )
    assert "total_anomalies" in res
    assert "lower_bound" in res
    assert "upper_bound" in res


def test_chart_generation(sample_df: pd.DataFrame):
    """Verifies structured ChartSpec generation for bar and line charts."""
    # Bar chart
    bar_spec = ChartService.generate_chart(
        df=sample_df,
        chart_type="bar",
        x_axis="category",
        y_axis="sales_amount",
    )
    assert bar_spec["chart_type"] == "bar"
    assert bar_spec["x_axis_key"] == "category"
    assert len(bar_spec["data"]) > 0

    # Line chart over time
    line_spec = ChartService.generate_chart(
        df=sample_df,
        chart_type="line",
        x_axis="order_date",
        y_axis="sales_amount",
    )
    assert line_spec["chart_type"] == "line"
    assert len(line_spec["data"]) > 0


def test_execute_tool_with_invalid_column(sample_df: pd.DataFrame):
    """Verifies controlled error on non-existent column in execute_tool."""
    session = session_service.create_session("sess-1", "test.csv", sample_df, 100)
    session.profile = ProfilingService.profile_dataset("sess-1", "test.csv", 100, sample_df)

    res, succ = execute_tool(
        "calculate_metric",
        {"metric_column": "completely_fake_column", "aggregation": "sum"},
        session,
    )
    assert not succ
    assert "error" in res
    assert "Could not resolve 'completely_fake_column'" in res["error"]

"""Tool definitions, schemas, and execution dispatcher for the Data Analyst Agent."""

import json
from typing import Any, Dict, List, Tuple
import pandas as pd
from app.services.analysis_service import AnalysisService
from app.services.chart_service import ChartService
from app.services.session_service import SessionData

# OpenAI function specifications for deterministic analytical tools
ANALYSIS_TOOLS_SPEC = [
    {
        "type": "function",
        "function": {
            "name": "get_dataset_summary",
            "description": "Returns dataset dimensions, detected business roles (revenue, order_id, dates, etc.), and overall summary metrics.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_column_info",
            "description": "Inspects a specific column for non-null count, distinct values, descriptive statistics, and sample values.",
            "parameters": {
                "type": "object",
                "properties": {
                    "column_name": {
                        "type": "string",
                        "description": "Name or semantic role of the column to inspect (e.g. 'revenue', 'order_date', 'category').",
                    }
                },
                "required": ["column_name"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_metric",
            "description": "Computes a single aggregated metric (sum, mean, median, min, max, count, nunique) on a numeric or categorical column with optional filtering.",
            "parameters": {
                "type": "object",
                "properties": {
                    "metric_column": {
                        "type": "string",
                        "description": "Column name or role to aggregate (e.g. 'revenue', 'sales_amount', 'quantity', 'unit_price').",
                    },
                    "aggregation": {
                        "type": "string",
                        "enum": ["sum", "mean", "median", "min", "max", "count", "nunique"],
                        "description": "Statistical aggregation to perform.",
                    },
                    "filter_column": {
                        "type": "string",
                        "description": "Optional column to filter by (e.g. 'region', 'category', 'year').",
                    },
                    "filter_operator": {
                        "type": "string",
                        "enum": ["==", "!=", ">", ">=", "<", "<=", "contains"],
                        "description": "Comparison operator for filter.",
                    },
                    "filter_value": {
                        "type": "string",
                        "description": "Target value to compare against in the filter.",
                    },
                },
                "required": ["metric_column", "aggregation"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "group_and_aggregate",
            "description": "Groups records by a category/dimension and aggregates a numeric metric (sum, mean, median, count, nunique). Sorts by result.",
            "parameters": {
                "type": "object",
                "properties": {
                    "group_by": {
                        "type": "string",
                        "description": "Dimension column or role to group by (e.g. 'category', 'region', 'product').",
                    },
                    "metric_column": {
                        "type": "string",
                        "description": "Metric column or role to aggregate (e.g. 'revenue', 'quantity').",
                    },
                    "aggregation": {
                        "type": "string",
                        "enum": ["sum", "mean", "median", "count", "nunique", "min", "max"],
                        "description": "Aggregation function.",
                    },
                    "sort_descending": {
                        "type": "boolean",
                        "description": "Whether to sort high-to-low (default true).",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of groups to return (default 10).",
                    },
                },
                "required": ["group_by", "metric_column"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_n",
            "description": "Ranks top or bottom N entities by a metric (e.g. top 10 products by revenue, or bottom 5 underperforming products).",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_column": {
                        "type": "string",
                        "description": "Entity column (e.g. 'product_name', 'category', 'customer_id').",
                    },
                    "metric_column": {
                        "type": "string",
                        "description": "Metric to rank by (e.g. 'revenue', 'quantity', 'sales_amount').",
                    },
                    "n": {
                        "type": "integer",
                        "description": "Number of items to return (default 10).",
                    },
                    "ascending": {
                        "type": "boolean",
                        "description": "Set to true for bottom/underperforming N, false for top N.",
                    },
                },
                "required": ["entity_column", "metric_column"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_groups",
            "description": "Directly compares two cohort values within a dimension across a metric (e.g., compare 'North' vs 'South' or 'Jan' vs 'Feb').",
            "parameters": {
                "type": "object",
                "properties": {
                    "dimension_column": {
                        "type": "string",
                        "description": "Dimension column (e.g. 'region', 'category').",
                    },
                    "group_a": {
                        "type": "string",
                        "description": "First group identifier (e.g. 'North').",
                    },
                    "group_b": {
                        "type": "string",
                        "description": "Second group identifier (e.g. 'South').",
                    },
                    "metric_column": {
                        "type": "string",
                        "description": "Metric column (e.g. 'revenue').",
                    },
                    "aggregation": {
                        "type": "string",
                        "enum": ["sum", "mean", "median", "count"],
                        "description": "Aggregation function (default sum).",
                    },
                },
                "required": ["dimension_column", "group_a", "group_b", "metric_column"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_time_trend",
            "description": "Analyzes metrics across time periods (daily, weekly, monthly, yearly) using dates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "metric_column": {
                        "type": "string",
                        "description": "Metric column (e.g. 'revenue', 'quantity').",
                    },
                    "date_column": {
                        "type": "string",
                        "description": "Date column name or 'order_date'.",
                    },
                    "freq": {
                        "type": "string",
                        "enum": ["M", "W", "D", "Y"],
                        "description": "Period frequency: 'M' for monthly, 'W' for weekly, 'D' for daily, 'Y' for yearly.",
                    },
                    "aggregation": {
                        "type": "string",
                        "enum": ["sum", "mean", "count"],
                        "description": "Aggregation type (default sum).",
                    },
                },
                "required": ["metric_column"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_growth",
            "description": "Calculates percentage growth and period-over-period changes between months or specified time periods.",
            "parameters": {
                "type": "object",
                "properties": {
                    "metric_column": {
                        "type": "string",
                        "description": "Metric column (e.g. 'revenue').",
                    },
                    "date_column": {
                        "type": "string",
                        "description": "Date column or role.",
                    },
                    "period_a": {
                        "type": "string",
                        "description": "Optional initial period (e.g. '2024-01' or 'January').",
                    },
                    "period_b": {
                        "type": "string",
                        "description": "Optional target period (e.g. '2024-02' or 'February').",
                    },
                },
                "required": ["metric_column"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "detect_basic_anomalies",
            "description": "Detects statistical outliers in a numeric column using Interquartile Range (IQR).",
            "parameters": {
                "type": "object",
                "properties": {
                    "metric_column": {
                        "type": "string",
                        "description": "Numeric column to check for anomalies (e.g. 'sales_amount', 'quantity', 'discount').",
                    },
                    "threshold_iqr_multiplier": {
                        "type": "number",
                        "description": "IQR multiplier for outlier fences (default 1.5).",
                    },
                },
                "required": ["metric_column"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_chart_data",
            "description": "Generates aggregated visualization specification (bar, line, pie, scatter, histogram) for rendering in the dashboard.",
            "parameters": {
                "type": "object",
                "properties": {
                    "chart_type": {
                        "type": "string",
                        "enum": ["bar", "line", "pie", "scatter", "histogram"],
                        "description": "Type of visualization.",
                    },
                    "x_axis": {
                        "type": "string",
                        "description": "Column or role for X-axis (e.g. 'category', 'order_date', 'product_name').",
                    },
                    "y_axis": {
                        "type": "string",
                        "description": "Column or role for Y-axis (e.g. 'revenue', 'quantity', 'unit_price').",
                    },
                    "aggregation": {
                        "type": "string",
                        "enum": ["sum", "mean", "count"],
                        "description": "Aggregation function (default 'sum').",
                    },
                    "title": {
                        "type": "string",
                        "description": "Descriptive headline for the chart.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max categories to display (default 10).",
                    },
                },
                "required": ["chart_type", "x_axis", "y_axis"],
                "additionalProperties": False,
            },
        },
    },
]


def execute_tool(
    tool_name: str,
    args: Dict[str, Any],
    session: SessionData,
) -> Tuple[Dict[str, Any], bool]:
    """Executes a registered tool deterministically on the session's DataFrame.
    
    Returns:
        Tuple[result_dict, is_success]
    """
    df = session.df
    confirmed = session.confirmed_mappings
    profile = session.profile

    try:
        if tool_name == "get_dataset_summary":
            res = AnalysisService.get_dataset_summary(df, profile=profile)
            return res, True

        elif tool_name == "get_column_info":
            res = AnalysisService.get_column_info(
                df=df,
                column_name=args.get("column_name", ""),
                confirmed_mappings=confirmed,
                profile=profile,
            )
            return res, "error" not in res

        elif tool_name == "calculate_metric":
            res = AnalysisService.calculate_metric(
                df=df,
                metric_column=args.get("metric_column", ""),
                aggregation=args.get("aggregation", "sum"),
                filter_column=args.get("filter_column"),
                filter_operator=args.get("filter_operator"),
                filter_value=args.get("filter_value"),
                confirmed_mappings=confirmed,
                profile=profile,
            )
            return res, "error" not in res

        elif tool_name == "group_and_aggregate":
            res = AnalysisService.group_and_aggregate(
                df=df,
                group_by=args.get("group_by", ""),
                metric_column=args.get("metric_column", ""),
                aggregation=args.get("aggregation", "sum"),
                sort_descending=args.get("sort_descending", True),
                limit=args.get("limit", 10),
                confirmed_mappings=confirmed,
                profile=profile,
            )
            return res, "error" not in res

        elif tool_name == "get_top_n":
            res = AnalysisService.get_top_n(
                df=df,
                entity_column=args.get("entity_column", ""),
                metric_column=args.get("metric_column", ""),
                n=args.get("n", 10),
                ascending=args.get("ascending", False),
                confirmed_mappings=confirmed,
                profile=profile,
            )
            return res, "error" not in res

        elif tool_name == "compare_groups":
            res = AnalysisService.compare_groups(
                df=df,
                dimension_column=args.get("dimension_column", ""),
                group_a=args.get("group_a", ""),
                group_b=args.get("group_b", ""),
                metric_column=args.get("metric_column", ""),
                aggregation=args.get("aggregation", "sum"),
                confirmed_mappings=confirmed,
                profile=profile,
            )
            return res, "error" not in res

        elif tool_name == "analyze_time_trend":
            res = AnalysisService.analyze_time_trend(
                df=df,
                metric_column=args.get("metric_column", ""),
                date_column=args.get("date_column"),
                freq=args.get("freq", "M"),
                aggregation=args.get("aggregation", "sum"),
                confirmed_mappings=confirmed,
                profile=profile,
            )
            return res, "error" not in res

        elif tool_name == "calculate_growth":
            res = AnalysisService.calculate_growth(
                df=df,
                metric_column=args.get("metric_column", ""),
                date_column=args.get("date_column"),
                period_a=args.get("period_a"),
                period_b=args.get("period_b"),
                confirmed_mappings=confirmed,
                profile=profile,
            )
            return res, "error" not in res

        elif tool_name == "detect_basic_anomalies":
            res = AnalysisService.detect_basic_anomalies(
                df=df,
                metric_column=args.get("metric_column", ""),
                threshold_iqr_multiplier=args.get("threshold_iqr_multiplier", 1.5),
                confirmed_mappings=confirmed,
                profile=profile,
            )
            return res, "error" not in res

        elif tool_name == "generate_chart_data":
            res = ChartService.generate_chart(
                df=df,
                chart_type=args.get("chart_type", "bar"),
                x_axis=args.get("x_axis", ""),
                y_axis=args.get("y_axis", ""),
                aggregation=args.get("aggregation", "sum"),
                title=args.get("title"),
                limit=args.get("limit", 10),
                confirmed_mappings=confirmed,
                profile=profile,
            )
            return res, "error" not in res

        else:
            return {"error": f"Tool '{tool_name}' is not recognized in the analytics registry."}, False

    except Exception as e:
        return {"error": f"Tool execution failed: {str(e)}"}, False

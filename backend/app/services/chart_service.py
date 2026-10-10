"""Chart data generation service for structured Recharts visualization."""

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from app.schemas.charts import ChartSeries, ChartSpec, ChartType
from app.schemas.dataset import DatasetProfile
from app.services.analysis_service import AnalysisService
from app.services.schema_mapping_service import SchemaMappingService

DEFAULT_PALETTE = [
    "#3B82F6",  # Blue
    "#10B981",  # Emerald
    "#F59E0B",  # Amber
    "#EC4899",  # Pink
    "#8B5CF6",  # Purple
    "#06B6D4",  # Cyan
    "#F97316",  # Orange
    "#6366F1",  # Indigo
]


class ChartService:
    """Generates clean, aggregated ChartSpec objects for the frontend."""

    @classmethod
    def generate_chart(
        cls,
        df: pd.DataFrame,
        chart_type: str,
        x_axis: str,
        y_axis: str,
        aggregation: str = "sum",
        title: Optional[str] = None,
        limit: int = 10,
        confirmed_mappings: Optional[Dict[str, str]] = None,
        profile: Optional[DatasetProfile] = None,
    ) -> Dict[str, Any]:
        """Prepares a validated ChartSpec dictionary from the dataset."""
        chart_type_norm = chart_type.lower().strip()

        # Resolve X and Y columns
        x_col, x_err = SchemaMappingService.resolve_column(
            df, x_axis, confirmed_mappings, profile
        )
        if x_err or not x_col:
            return {"error": f"X-axis column error: {x_err}"}

        y_col, y_err = SchemaMappingService.resolve_column(
            df, y_axis, confirmed_mappings, profile
        )
        if y_err or not y_col:
            return {"error": f"Y-axis column error: {y_err}"}

        # 1. Line chart over time
        if chart_type_norm == "line":
            time_res = AnalysisService.analyze_time_trend(
                df=df,
                metric_column=y_col,
                date_column=x_col,
                freq="M",
                aggregation=aggregation,
                confirmed_mappings=confirmed_mappings,
                profile=profile,
            )
            if "error" in time_res:
                # If date parsing failed, try regular grouping
                return cls._build_categorical_chart(
                    df=df,
                    chart_type=ChartType.LINE,
                    x_col=x_col,
                    y_col=y_col,
                    aggregation=aggregation,
                    title=title or f"{aggregation.capitalize()} of {y_col} across {x_col}",
                    limit=limit,
                )
            
            trend_data = time_res["trend"]
            # Convert trend to chart data
            chart_data = [
                {"period": t["period"], y_col: t["value"]} for t in trend_data
            ]
            spec = ChartSpec(
                chart_type=ChartType.LINE,
                title=title or f"{y_col.replace('_', ' ').title()} Over Time",
                description=f"{aggregation.capitalize()} grouped by {time_res.get('frequency', 'Monthly')}",
                x_axis_key="period",
                x_axis_label="Period",
                y_axis_label=y_col.replace("_", " ").title(),
                series=[
                    ChartSeries(
                        key=y_col,
                        name=y_col.replace("_", " ").title(),
                        color=DEFAULT_PALETTE[0],
                    )
                ],
                data=chart_data,
            )
            return spec.model_dump()

        # 2. Scatter plot (unaggregated correlation between two numeric metrics)
        elif chart_type_norm == "scatter":
            if not pd.api.types.is_numeric_dtype(df[x_col]) or not pd.api.types.is_numeric_dtype(df[y_col]):
                return {"error": f"Scatter plots require both X ('{x_col}') and Y ('{y_col}') to be numeric."}

            clean_df = df[[x_col, y_col]].dropna().head(100)
            data_points = []
            for _, r in clean_df.iterrows():
                data_points.append({
                    x_col: round(float(r[x_col]), 2),
                    y_col: round(float(r[y_col]), 2),
                })

            spec = ChartSpec(
                chart_type=ChartType.SCATTER,
                title=title or f"{y_col.title()} vs {x_col.title()}",
                description="Distribution of individual records",
                x_axis_key=x_col,
                x_axis_label=x_col.replace("_", " ").title(),
                y_axis_label=y_col.replace("_", " ").title(),
                series=[
                    ChartSeries(
                        key=y_col,
                        name=f"{y_col} vs {x_col}",
                        color=DEFAULT_PALETTE[1],
                    )
                ],
                data=data_points,
            )
            return spec.model_dump()

        # 3. Histogram / Distribution
        elif chart_type_norm == "histogram":
            if not pd.api.types.is_numeric_dtype(df[x_col]):
                return {"error": f"Histogram requires numeric column '{x_col}'."}

            num_series = pd.to_numeric(df[x_col], errors="coerce").dropna()
            counts, bin_edges = np.histogram(num_series, bins=min(10, max(4, int(len(num_series) / 5))))
            hist_data = []
            for i in range(len(counts)):
                label = f"{bin_edges[i]:.1f}-{bin_edges[i+1]:.1f}"
                hist_data.append({"bucket": label, "count": int(counts[i])})

            spec = ChartSpec(
                chart_type=ChartType.BAR,
                title=title or f"Distribution of {x_col.replace('_', ' ').title()}",
                description=f"Frequency histogram across {len(counts)} buckets",
                x_axis_key="bucket",
                x_axis_label=x_col.replace("_", " ").title(),
                y_axis_label="Record Count",
                series=[
                    ChartSeries(
                        key="count",
                        name="Frequency",
                        color=DEFAULT_PALETTE[2],
                    )
                ],
                data=hist_data,
            )
            return spec.model_dump()

        # 4. Pie chart
        elif chart_type_norm == "pie":
            res = AnalysisService.group_and_aggregate(
                df=df,
                group_by=x_col,
                metric_column=y_col,
                aggregation=aggregation,
                sort_descending=True,
                limit=limit or 7,
                confirmed_mappings=confirmed_mappings,
                profile=profile,
            )
            if "error" in res:
                return res

            data = res["results"]
            spec = ChartSpec(
                chart_type=ChartType.PIE,
                title=title or f"{y_col.replace('_', ' ').title()} Share by {x_col.replace('_', ' ').title()}",
                description=f"Proportional breakdown ({aggregation})",
                x_axis_key=x_col,
                x_axis_label=x_col.replace("_", " ").title(),
                y_axis_label=y_col.replace("_", " ").title(),
                series=[
                    ChartSeries(
                        key=y_col,
                        name=y_col.replace("_", " ").title(),
                        color=DEFAULT_PALETTE[3],
                    )
                ],
                data=data,
            )
            return spec.model_dump()

        # 5. Default: Bar chart
        else:
            return cls._build_categorical_chart(
                df=df,
                chart_type=ChartType.BAR,
                x_col=x_col,
                y_col=y_col,
                aggregation=aggregation,
                title=title or f"{y_col.replace('_', ' ').title()} by {x_col.replace('_', ' ').title()}",
                limit=limit,
                confirmed_mappings=confirmed_mappings,
                profile=profile,
            )

    @classmethod
    def _build_categorical_chart(
        cls,
        df: pd.DataFrame,
        chart_type: ChartType,
        x_col: str,
        y_col: str,
        aggregation: str,
        title: str,
        limit: int = 10,
        confirmed_mappings: Optional[Dict[str, str]] = None,
        profile: Optional[DatasetProfile] = None,
    ) -> Dict[str, Any]:
        """Helper to build aggregated categorical chart."""
        res = AnalysisService.group_and_aggregate(
            df=df,
            group_by=x_col,
            metric_column=y_col,
            aggregation=aggregation,
            sort_descending=True,
            limit=limit,
            confirmed_mappings=confirmed_mappings,
            profile=profile,
        )
        if "error" in res:
            return res

        data = res["results"]
        spec = ChartSpec(
            chart_type=chart_type,
            title=title,
            description=f"{aggregation.capitalize()} grouped by {x_col.replace('_', ' ').title()}",
            x_axis_key=x_col,
            x_axis_label=x_col.replace("_", " ").title(),
            y_axis_label=y_col.replace("_", " ").title(),
            series=[
                ChartSeries(
                    key=y_col,
                    name=y_col.replace("_", " ").title(),
                    color=DEFAULT_PALETTE[0],
                )
            ],
            data=data,
        )
        return spec.model_dump()

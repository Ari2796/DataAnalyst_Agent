"""Deterministic pandas and numpy analytics engine for e-commerce data."""

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from app.schemas.dataset import DatasetProfile
from app.services.schema_mapping_service import SchemaMappingService


class AnalysisService:
    """Executes deterministic analytical operations on Pandas DataFrames."""

    @classmethod
    def get_dataset_summary(
        cls, df: pd.DataFrame, profile: Optional[DatasetProfile] = None
    ) -> Dict[str, Any]:
        """Provides a high-level statistical snapshot of the dataset."""
        role_map = SchemaMappingService.get_role_column_map(df, profile=profile)
        
        # Order count nunique if order_id exists, otherwise row count with note
        order_col = role_map.get("order_id")
        unique_orders = int(df[order_col].nunique()) if order_col and order_col in df.columns else None

        rev_col = role_map.get("revenue")
        total_revenue = round(float(df[rev_col].dropna().sum()), 2) if rev_col and rev_col in df.columns else None

        summary: Dict[str, Any] = {
            "total_rows": int(len(df)),
            "total_columns": int(len(df.columns)),
            "columns": list(df.columns),
            "unique_orders": unique_orders,
            "order_count_note": (
                f"Count based on unique '{order_col}' identifiers"
                if unique_orders is not None
                else "No order_id detected; row count represents individual line items"
            ),
            "total_revenue": total_revenue,
            "revenue_column_used": rev_col,
            "detected_roles": role_map,
        }
        return summary

    @classmethod
    def get_column_info(
        cls,
        df: pd.DataFrame,
        column_name: str,
        confirmed_mappings: Optional[Dict[str, str]] = None,
        profile: Optional[DatasetProfile] = None,
    ) -> Dict[str, Any]:
        """Returns deep statistics and distribution for a specific column."""
        resolved_col, err = SchemaMappingService.resolve_column(
            df, column_name, confirmed_mappings, profile
        )
        if err or not resolved_col:
            return {"error": err}

        series = df[resolved_col]
        info: Dict[str, Any] = {
            "column_name": resolved_col,
            "data_type": str(series.dtype),
            "total_count": int(len(series)),
            "non_null_count": int(series.count()),
            "missing_count": int(series.isna().sum()),
            "unique_count": int(series.nunique(dropna=True)),
            "sample_values": [
                x if not pd.isna(x) else None
                for x in series.dropna().head(5).tolist()
            ],
        }

        if pd.api.types.is_numeric_dtype(series) and not series.dropna().empty:
            clean_s = series.dropna().astype(float)
            info["statistics"] = {
                "min": round(float(clean_s.min()), 4),
                "max": round(float(clean_s.max()), 4),
                "mean": round(float(clean_s.mean()), 4),
                "median": round(float(clean_s.median()), 4),
                "std": round(float(clean_s.std()), 4) if len(clean_s) > 1 else 0.0,
                "sum": round(float(clean_s.sum()), 4),
            }

        return info

    @classmethod
    def calculate_metric(
        cls,
        df: pd.DataFrame,
        metric_column: str,
        aggregation: str = "sum",
        filter_column: Optional[str] = None,
        filter_operator: Optional[str] = None,
        filter_value: Optional[Any] = None,
        confirmed_mappings: Optional[Dict[str, str]] = None,
        profile: Optional[DatasetProfile] = None,
    ) -> Dict[str, Any]:
        """Calculates a single scalar aggregate metric with optional filtering."""
        col, err = SchemaMappingService.resolve_column(df, metric_column, confirmed_mappings, profile)
        if err or not col:
            return {"error": err}

        working_df = df.copy()

        # Apply filter if provided
        if filter_column and filter_operator is not None and filter_value is not None:
            f_col, f_err = SchemaMappingService.resolve_column(
                df, filter_column, confirmed_mappings, profile
            )
            if f_err or not f_col:
                return {"error": f"Filter error: {f_err}"}

            working_df = cls._apply_filter(working_df, f_col, filter_operator, filter_value)

        series = working_df[col].dropna()
        agg = aggregation.lower().strip()

        if agg == "count":
            val = int(len(series))
        elif agg == "nunique":
            val = int(series.nunique())
        elif pd.api.types.is_numeric_dtype(series):
            num_s = series.astype(float)
            if num_s.empty:
                return {
                    "column": col,
                    "aggregation": agg,
                    "value": 0,
                    "rows_evaluated": 0,
                    "note": "No rows matched the filter criteria.",
                }
            if agg == "sum":
                val = round(float(num_s.sum()), 4)
            elif agg == "mean" or agg == "avg":
                val = round(float(num_s.mean()), 4)
            elif agg == "median":
                val = round(float(num_s.median()), 4)
            elif agg == "min":
                val = round(float(num_s.min()), 4)
            elif agg == "max":
                val = round(float(num_s.max()), 4)
            elif agg == "std":
                val = round(float(num_s.std()), 4) if len(num_s) > 1 else 0.0
            else:
                return {"error": f"Unsupported aggregation '{aggregation}' for numeric column."}
        else:
            return {
                "error": f"Column '{col}' is not numeric. Aggregation '{aggregation}' requires numeric data."
            }

        return {
            "column": col,
            "aggregation": agg,
            "value": val,
            "rows_evaluated": int(len(working_df)),
            "filter_applied": (
                f"{filter_column} {filter_operator} {filter_value}"
                if filter_column
                else None
            ),
        }

    @classmethod
    def group_and_aggregate(
        cls,
        df: pd.DataFrame,
        group_by: str,
        metric_column: str,
        aggregation: str = "sum",
        sort_descending: bool = True,
        limit: int = 10,
        confirmed_mappings: Optional[Dict[str, str]] = None,
        profile: Optional[DatasetProfile] = None,
    ) -> Dict[str, Any]:
        """Groups data by a dimension and computes aggregated metrics."""
        dim_col, dim_err = SchemaMappingService.resolve_column(
            df, group_by, confirmed_mappings, profile
        )
        if dim_err or not dim_col:
            return {"error": dim_err}

        met_col, met_err = SchemaMappingService.resolve_column(
            df, metric_column, confirmed_mappings, profile
        )
        if met_err or not met_col:
            return {"error": met_err}

        agg = aggregation.lower().strip()
        working = df[[dim_col, met_col]].dropna(subset=[dim_col]).copy()

        if agg == "count":
            grouped = working.groupby(dim_col)[met_col].count().reset_index()
        elif agg == "nunique":
            grouped = working.groupby(dim_col)[met_col].nunique().reset_index()
        else:
            if not pd.api.types.is_numeric_dtype(working[met_col]):
                return {"error": f"Metric column '{met_col}' must be numeric for aggregation '{agg}'."}
            working[met_col] = pd.to_numeric(working[met_col], errors="coerce")
            
            if agg == "sum":
                grouped = working.groupby(dim_col)[met_col].sum().reset_index()
            elif agg in ("mean", "avg"):
                grouped = working.groupby(dim_col)[met_col].mean().reset_index()
            elif agg == "median":
                grouped = working.groupby(dim_col)[met_col].median().reset_index()
            elif agg == "min":
                grouped = working.groupby(dim_col)[met_col].min().reset_index()
            elif agg == "max":
                grouped = working.groupby(dim_col)[met_col].max().reset_index()
            else:
                return {"error": f"Unsupported aggregation '{agg}'."}

        grouped[met_col] = grouped[met_col].round(2)
        grouped = grouped.sort_values(by=met_col, ascending=not sort_descending)

        total_groups = len(grouped)
        if limit and limit > 0:
            grouped = grouped.head(limit)

        results = grouped.to_dict(orient="records")
        # Format keys consistently
        formatted = []
        for r in results:
            formatted.append({
                str(dim_col): str(r[dim_col]),
                str(met_col): float(r[met_col]) if isinstance(r[met_col], (np.number, float, int)) else r[met_col]
            })

        return {
            "group_by": dim_col,
            "metric_column": met_col,
            "aggregation": agg,
            "total_groups": total_groups,
            "results": formatted,
        }

    @classmethod
    def get_top_n(
        cls,
        df: pd.DataFrame,
        entity_column: str,
        metric_column: str,
        n: int = 10,
        ascending: bool = False,
        aggregation: str = "sum",
        confirmed_mappings: Optional[Dict[str, str]] = None,
        profile: Optional[DatasetProfile] = None,
    ) -> Dict[str, Any]:
        """Returns top-N or bottom-N entities ordered by aggregated metric."""
        return cls.group_and_aggregate(
            df=df,
            group_by=entity_column,
            metric_column=metric_column,
            aggregation=aggregation,
            sort_descending=not ascending,
            limit=n,
            confirmed_mappings=confirmed_mappings,
            profile=profile,
        )

    @classmethod
    def compare_groups(
        cls,
        df: pd.DataFrame,
        dimension_column: str,
        group_a: str,
        group_b: str,
        metric_column: str,
        aggregation: str = "sum",
        confirmed_mappings: Optional[Dict[str, str]] = None,
        profile: Optional[DatasetProfile] = None,
    ) -> Dict[str, Any]:
        """Compares two specific cohort groups or categories across a metric."""
        dim_col, dim_err = SchemaMappingService.resolve_column(
            df, dimension_column, confirmed_mappings, profile
        )
        if dim_err or not dim_col:
            return {"error": dim_err}

        met_col, met_err = SchemaMappingService.resolve_column(
            df, metric_column, confirmed_mappings, profile
        )
        if met_err or not met_col:
            return {"error": met_err}

        # Case-insensitive matching for string values
        mask_a = df[dim_col].astype(str).str.lower() == str(group_a).lower()
        mask_b = df[dim_col].astype(str).str.lower() == str(group_b).lower()

        df_a = df[mask_a]
        df_b = df[mask_b]

        val_a = cls._calc_sub_metric(df_a, met_col, aggregation)
        val_b = cls._calc_sub_metric(df_b, met_col, aggregation)

        abs_diff = round(val_a - val_b, 4)
        pct_diff = round(((val_a - val_b) / val_b * 100), 2) if val_b != 0 else None

        return {
            "dimension": dim_col,
            "metric": met_col,
            "aggregation": aggregation,
            "group_a": {
                "name": str(group_a),
                "value": round(val_a, 2),
                "record_count": int(len(df_a)),
            },
            "group_b": {
                "name": str(group_b),
                "value": round(val_b, 2),
                "record_count": int(len(df_b)),
            },
            "absolute_difference": abs_diff,
            "percentage_difference": pct_diff,
            "higher_group": str(group_a) if val_a > val_b else (str(group_b) if val_b > val_a else "Tied"),
        }

    @classmethod
    def analyze_time_trend(
        cls,
        df: pd.DataFrame,
        metric_column: str,
        date_column: Optional[str] = None,
        freq: str = "M",  # D, W, M, Q, Y
        aggregation: str = "sum",
        confirmed_mappings: Optional[Dict[str, str]] = None,
        profile: Optional[DatasetProfile] = None,
    ) -> Dict[str, Any]:
        """Aggregates metrics across time periods (daily, weekly, monthly, etc.)."""
        # Resolve date column
        target_date = date_column or "order_date"
        d_col, d_err = SchemaMappingService.resolve_column(
            df, target_date, confirmed_mappings, profile
        )
        if d_err or not d_col:
            return {"error": f"Time analysis requires a valid date column: {d_err}"}

        met_col, m_err = SchemaMappingService.resolve_column(
            df, metric_column, confirmed_mappings, profile
        )
        if m_err or not met_col:
            return {"error": m_err}

        # Parse dates safely
        working = df[[d_col, met_col]].dropna().copy()
        try:
            working["_parsed_date"] = pd.to_datetime(working[d_col], errors="coerce")
        except Exception as e:
            return {"error": f"Failed to parse dates in column '{d_col}': {str(e)}"}

        working = working.dropna(subset=["_parsed_date"])
        if working.empty:
            return {"error": f"No valid dates could be parsed from column '{d_col}'."}

        working[met_col] = pd.to_numeric(working[met_col], errors="coerce")
        working = working.dropna(subset=[met_col])

        # Frequency mapping
        freq_norm = freq.upper()
        if freq_norm in ("MONTH", "MONTHLY", "M"):
            working["period"] = working["_parsed_date"].dt.to_period("M").astype(str)
        elif freq_norm in ("DAY", "DAILY", "D"):
            working["period"] = working["_parsed_date"].dt.to_period("D").astype(str)
        elif freq_norm in ("WEEK", "WEEKLY", "W"):
            working["period"] = working["_parsed_date"].dt.to_period("W").astype(str)
        elif freq_norm in ("YEAR", "YEARLY", "Y"):
            working["period"] = working["_parsed_date"].dt.to_period("Y").astype(str)
        else:
            working["period"] = working["_parsed_date"].dt.to_period("M").astype(str)

        agg = aggregation.lower()
        if agg == "sum":
            grouped = working.groupby("period")[met_col].sum().reset_index()
        elif agg in ("mean", "avg"):
            grouped = working.groupby("period")[met_col].mean().reset_index()
        elif agg == "count":
            grouped = working.groupby("period")[met_col].count().reset_index()
        else:
            grouped = working.groupby("period")[met_col].sum().reset_index()

        grouped[met_col] = grouped[met_col].round(2)
        grouped = grouped.sort_values(by="period")

        # Period-over-period change
        grouped["pct_change"] = grouped[met_col].pct_change().mul(100).round(2).fillna(0.0)

        trend_records = []
        for _, row in grouped.iterrows():
            trend_records.append({
                "period": str(row["period"]),
                "value": float(row[met_col]),
                "pct_change": float(row["pct_change"]),
            })

        return {
            "date_column": d_col,
            "metric_column": met_col,
            "frequency": freq_norm,
            "aggregation": agg,
            "periods_count": len(trend_records),
            "trend": trend_records,
        }

    @classmethod
    def calculate_growth(
        cls,
        df: pd.DataFrame,
        metric_column: str,
        date_column: Optional[str] = None,
        period_a: Optional[str] = None,
        period_b: Optional[str] = None,
        confirmed_mappings: Optional[Dict[str, str]] = None,
        profile: Optional[DatasetProfile] = None,
    ) -> Dict[str, Any]:
        """Calculates growth rate and percentage changes between consecutive periods or explicit dates."""
        trend_res = cls.analyze_time_trend(
            df=df,
            metric_column=metric_column,
            date_column=date_column,
            freq="M",
            confirmed_mappings=confirmed_mappings,
            profile=profile,
        )
        if "error" in trend_res:
            return trend_res

        trend = trend_res["trend"]
        if len(trend) < 2:
            return {
                "error": "Dataset does not span enough distinct time periods to compute growth."
            }

        if period_a and period_b:
            item_a = next((x for x in trend if period_a.lower() in x["period"].lower()), None)
            item_b = next((x for x in trend if period_b.lower() in x["period"].lower()), None)
            if not item_a or not item_b:
                return {
                    "error": f"Could not find matching periods for '{period_a}' and/or '{period_b}'. "
                             f"Available periods: {[x['period'] for x in trend]}."
                }
            val_a = item_a["value"]
            val_b = item_b["value"]
            diff = round(val_b - val_a, 2)
            growth_pct = round((diff / val_a * 100), 2) if val_a != 0 else None
            return {
                "period_initial": item_a["period"],
                "value_initial": val_a,
                "period_target": item_b["period"],
                "value_target": val_b,
                "absolute_change": diff,
                "growth_percentage": growth_pct,
            }

        # Otherwise compare the latest two periods
        first = trend[0]
        latest = trend[-1]
        overall_growth = round(((latest["value"] - first["value"]) / first["value"] * 100), 2) if first["value"] != 0 else None

        return {
            "first_period": first["period"],
            "first_value": first["value"],
            "latest_period": latest["period"],
            "latest_value": latest["value"],
            "overall_growth_percentage": overall_growth,
            "period_breakdowns": trend,
        }

    @classmethod
    def detect_basic_anomalies(
        cls,
        df: pd.DataFrame,
        metric_column: str,
        threshold_iqr_multiplier: float = 1.5,
        confirmed_mappings: Optional[Dict[str, str]] = None,
        profile: Optional[DatasetProfile] = None,
    ) -> Dict[str, Any]:
        """Detects numeric outliers using the Interquartile Range (IQR) technique."""
        col, err = SchemaMappingService.resolve_column(
            df, metric_column, confirmed_mappings, profile
        )
        if err or not col:
            return {"error": err}

        series = pd.to_numeric(df[col], errors="coerce").dropna()
        if len(series) < 5:
            return {"error": "Insufficient numeric data points to detect statistical anomalies."}

        q25 = float(series.quantile(0.25))
        q75 = float(series.quantile(0.75))
        iqr = q75 - q25
        lower_bound = q25 - (threshold_iqr_multiplier * iqr)
        upper_bound = q75 + (threshold_iqr_multiplier * iqr)

        high_outliers = series[series > upper_bound]
        low_outliers = series[series < lower_bound]

        total_anomalies = len(high_outliers) + len(low_outliers)

        return {
            "column": col,
            "total_records_checked": len(series),
            "lower_bound": round(lower_bound, 2),
            "upper_bound": round(upper_bound, 2),
            "high_anomalies_count": int(len(high_outliers)),
            "high_anomaly_samples": [round(float(x), 2) for x in high_outliers.head(5).tolist()],
            "low_anomalies_count": int(len(low_outliers)),
            "low_anomaly_samples": [round(float(x), 2) for x in low_outliers.head(5).tolist()],
            "total_anomalies": total_anomalies,
            "anomaly_rate_percent": round((total_anomalies / len(series)) * 100, 2),
        }

    # Internal helper utilities
    @staticmethod
    def _apply_filter(
        df: pd.DataFrame, col: str, op: str, val: Any
    ) -> pd.DataFrame:
        """Applies comparison filter to a DataFrame."""
        op_clean = str(op).strip().lower()
        if op_clean in ("==", "=", "eq"):
            if pd.api.types.is_numeric_dtype(df[col]):
                return df[df[col] == float(val)]
            return df[df[col].astype(str).str.lower() == str(val).lower()]
        elif op_clean in ("!=", "<>", "ne"):
            return df[df[col].astype(str).str.lower() != str(val).lower()]
        elif op_clean in (">", "gt"):
            return df[pd.to_numeric(df[col], errors="coerce") > float(val)]
        elif op_clean in (">=", "gte"):
            return df[pd.to_numeric(df[col], errors="coerce") >= float(val)]
        elif op_clean in ("<", "lt"):
            return df[pd.to_numeric(df[col], errors="coerce") < float(val)]
        elif op_clean in ("<=", "lte"):
            return df[pd.to_numeric(df[col], errors="coerce") <= float(val)]
        elif op_clean in ("contains", "like"):
            return df[df[col].astype(str).str.contains(str(val), case=False, na=False)]
        return df

    @staticmethod
    def _calc_sub_metric(sub_df: pd.DataFrame, col: str, agg: str) -> float:
        """Computes numeric metric on a subset."""
        if sub_df.empty:
            return 0.0
        s = pd.to_numeric(sub_df[col], errors="coerce").dropna()
        if s.empty:
            return 0.0
        agg_clean = agg.lower()
        if agg_clean == "sum":
            return float(s.sum())
        elif agg_clean in ("mean", "avg"):
            return float(s.mean())
        elif agg_clean == "median":
            return float(s.median())
        elif agg_clean == "min":
            return float(s.min())
        elif agg_clean == "max":
            return float(s.max())
        elif agg_clean == "count":
            return float(len(s))
        return float(s.sum())

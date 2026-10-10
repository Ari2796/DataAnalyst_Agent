"""Data profiling service: analyzes uploaded DataFrames for structure, statistics, and semantic roles."""

import re
from typing import Any, Dict, List, Tuple
import numpy as np
import pandas as pd
from app.schemas.dataset import (
    ColumnGeneralType,
    ColumnProfile,
    DatasetProfile,
    NumericStats,
    SemanticMapping,
    SemanticRole,
)

# Canonical semantic patterns and keyword aliases for e-commerce
SEMANTIC_PATTERNS: Dict[SemanticRole, List[str]] = {
    SemanticRole.REVENUE: [
        r"^sales[_\s]?amount$",
        r"^total[_\s]?amount$",
        r"^total[_\s]?sales$",
        r"^revenue$",
        r"^sales$",
        r"^net[_\s]?sales$",
        r"^gross[_\s]?sales$",
        r"^order[_\s]?total$",
        r"^amount$",
        r"^item[_\s]?total$",
    ],
    SemanticRole.UNIT_PRICE: [
        r"^unit[_\s]?price$",
        r"^item[_\s]?price$",
        r"^price$",
        r"^retail[_\s]?price$",
        r"^selling[_\s]?price$",
        r"^cost[_\s]?per[_\s]?unit$",
    ],
    SemanticRole.QUANTITY: [
        r"^quantity$",
        r"^qty$",
        r"^units[_\s]?sold$",
        r"^units$",
        r"^item[_\s]?count$",
        r"^volume$",
    ],
    SemanticRole.ORDER_ID: [
        r"^order[_\s]?id$",
        r"^transaction[_\s]?id$",
        r"^order[_\s]?number$",
        r"^order[_\s]?no$",
        r"^invoice[_\s]?id$",
        r"^invoice[_\s]?no$",
    ],
    SemanticRole.ORDER_DATE: [
        r"^order[_\s]?date$",
        r"^transaction[_\s]?date$",
        r"^purchase[_\s]?date$",
        r"^order[_\s]?timestamp$",
        r"^date$",
        r"^sale[_\s]?date$",
        r"^created[_\s]?at$",
        r"^invoice[_\s]?date$",
    ],
    SemanticRole.PRODUCT: [
        r"^product[_\s]?name$",
        r"^product[_\s]?title$",
        r"^product$",
        r"^item[_\s]?name$",
        r"^item$",
        r"^sku$",
        r"^product[_\s]?id$",
    ],
    SemanticRole.CATEGORY: [
        r"^category$",
        r"^product[_\s]?category$",
        r"^dept$",
        r"^department$",
        r"^sub[_\s]?category$",
        r"^product[_\s]?group$",
    ],
    SemanticRole.CUSTOMER_ID: [
        r"^customer[_\s]?id$",
        r"^user[_\s]?id$",
        r"^client[_\s]?id$",
        r"^customer[_\s]?name$",
        r"^buyer[_\s]?id$",
    ],
    SemanticRole.REGION: [
        r"^region$",
        r"^location$",
        r"^state$",
        r"^city$",
        r"^country$",
        r"^territory$",
        r"^zone$",
        r"^market$",
    ],
    SemanticRole.DISCOUNT: [
        r"^discount$",
        r"^discount[_\s]?rate$",
        r"^discount[_\s]?percent$",
        r"^rebate$",
    ],
    SemanticRole.PROFIT: [
        r"^profit$",
        r"^net[_\s]?profit$",
        r"^margin$",
        r"^operating[_\s]?profit$",
    ],
    SemanticRole.SHIPPING_COST: [
        r"^shipping[_\s]?cost$",
        r"^shipping[_\s]?fee$",
        r"^shipping$",
        r"^freight$",
    ],
    SemanticRole.RATING: [
        r"^rating$",
        r"^review[_\s]?score$",
        r"^stars$",
        r"^feedback[_\s]?score$",
    ],
}


class ProfilingService:
    """Profiles tabular datasets and identifies e-commerce patterns."""

    @staticmethod
    def classify_column_type(series: pd.Series) -> ColumnGeneralType:
        """Classifies pandas series into general type."""
        dtype_str = str(series.dtype).lower()

        if pd.api.types.is_numeric_dtype(series):
            # Check if boolean represented as 0/1 or bool
            if pd.api.types.is_bool_dtype(series):
                return ColumnGeneralType.BOOLEAN
            # If unique values are only {0, 1} or {True, False} with count 2
            non_null = series.dropna()
            if len(non_null) > 0 and set(non_null.unique()).issubset({0, 1}):
                return ColumnGeneralType.BOOLEAN
            return ColumnGeneralType.NUMERIC

        if pd.api.types.is_datetime64_any_dtype(series):
            return ColumnGeneralType.DATETIME

        # Check if text column can be parsed as dates
        non_null = series.dropna().astype(str).str.strip()
        if len(non_null) > 0:
            sample = non_null.head(20)
            # Look for common date patterns (YYYY-MM-DD, DD/MM/YYYY, etc.)
            date_pattern = re.compile(
                r"^(\d{4}[-/.]\d{1,2}[-/.]\d{1,2}|\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4})"
            )
            if sample.str.match(date_pattern).mean() > 0.7:
                try:
                    pd.to_datetime(sample, errors="raise")
                    return ColumnGeneralType.DATETIME
                except Exception:
                    pass

        # Check categorical vs free text
        unique_ratio = series.nunique() / max(len(series), 1)
        if unique_ratio < 0.2 or series.nunique() < 30:
            return ColumnGeneralType.CATEGORICAL

        return ColumnGeneralType.TEXT

    @classmethod
    def detect_semantic_role(
        cls, col_name: str, series: pd.Series, general_type: ColumnGeneralType
    ) -> Tuple[SemanticRole, float]:
        """Detects the most likely e-commerce business role using regex matching and data types.
        
        Returns:
            Tuple[detected_role, confidence_score]
        """
        norm_name = col_name.strip().lower()

        # Check exact regex matches against defined patterns
        for role, patterns in SEMANTIC_PATTERNS.items():
            for pat in patterns:
                if re.search(pat, norm_name):
                    # Verify type suitability
                    if role in (
                        SemanticRole.REVENUE,
                        SemanticRole.UNIT_PRICE,
                        SemanticRole.QUANTITY,
                        SemanticRole.DISCOUNT,
                        SemanticRole.PROFIT,
                        SemanticRole.SHIPPING_COST,
                        SemanticRole.RATING,
                    ):
                        confidence = 0.95 if general_type == ColumnGeneralType.NUMERIC else 0.6
                        return role, confidence

                    if role == SemanticRole.ORDER_DATE:
                        confidence = 0.95 if general_type == ColumnGeneralType.DATETIME else 0.7
                        return role, confidence

                    return role, 0.9

        # Secondary fuzzy checks for partial keywords
        if any(w in norm_name for w in ["revenue", "sales", "turnover"]) and general_type == ColumnGeneralType.NUMERIC:
            return SemanticRole.REVENUE, 0.8
        if any(w in norm_name for w in ["price", "cost"]) and general_type == ColumnGeneralType.NUMERIC:
            return SemanticRole.UNIT_PRICE, 0.75
        if any(w in norm_name for w in ["qty", "quant", "count"]) and general_type == ColumnGeneralType.NUMERIC:
            return SemanticRole.QUANTITY, 0.8
        if any(w in norm_name for w in ["date", "time", "day", "month", "year"]) and general_type in (
            ColumnGeneralType.DATETIME,
            ColumnGeneralType.CATEGORICAL,
            ColumnGeneralType.TEXT,
        ):
            return SemanticRole.ORDER_DATE, 0.7
        if any(w in norm_name for w in ["prod", "item", "title", "sku"]):
            return SemanticRole.PRODUCT, 0.75
        if any(w in norm_name for w in ["cat", "genre", "dept", "type"]):
            return SemanticRole.CATEGORY, 0.75
        if any(w in norm_name for w in ["region", "state", "city", "country", "area"]):
            return SemanticRole.REGION, 0.8
        if any(w in norm_name for w in ["cust", "client", "user"]):
            return SemanticRole.CUSTOMER_ID, 0.75
        if "order" in norm_name and any(w in norm_name for w in ["id", "no", "num", "code"]):
            return SemanticRole.ORDER_ID, 0.85

        return SemanticRole.OTHER, 0.0

    @classmethod
    def profile_dataset(
        cls, dataset_id: str, filename: str, file_size_bytes: int, df: pd.DataFrame
    ) -> DatasetProfile:
        """Computes comprehensive profile for an uploaded dataset."""
        row_count = int(len(df))
        col_count = int(len(df.columns))
        duplicate_rows = int(df.duplicated().sum())

        column_profiles: List[ColumnProfile] = []
        semantic_mappings: Dict[str, SemanticMapping] = {}

        for col in df.columns:
            series = df[col]
            missing_count = int(series.isna().sum())
            missing_percentage = round((missing_count / max(row_count, 1)) * 100, 2)
            unique_count = int(series.nunique(dropna=True))

            general_type = cls.classify_column_type(series)

            # Sample values (up to 5 non-null, json-safe)
            non_null_samples = series.dropna().head(5).tolist()
            clean_samples = []
            for s in non_null_samples:
                if pd.isna(s):
                    continue
                if isinstance(s, (np.integer, int)):
                    clean_samples.append(int(s))
                elif isinstance(s, (np.floating, float)):
                    clean_samples.append(round(float(s), 4))
                else:
                    clean_samples.append(str(s)[:60])

            # Numeric statistics if applicable
            stats: NumericStats | None = None
            if pd.api.types.is_numeric_dtype(series) and not series.dropna().empty:
                valid_num = series.dropna().astype(float)
                stats = NumericStats(
                    min=round(float(valid_num.min()), 4),
                    max=round(float(valid_num.max()), 4),
                    mean=round(float(valid_num.mean()), 4),
                    median=round(float(valid_num.median()), 4),
                    std=round(float(valid_num.std()), 4) if len(valid_num) > 1 else 0.0,
                    q25=round(float(valid_num.quantile(0.25)), 4),
                    q75=round(float(valid_num.quantile(0.75)), 4),
                )

            suggested_role, confidence = cls.detect_semantic_role(col, series, general_type)

            column_profiles.append(
                ColumnProfile(
                    name=col,
                    data_type=str(series.dtype),
                    general_type=general_type,
                    missing_count=missing_count,
                    missing_percentage=missing_percentage,
                    unique_count=unique_count,
                    sample_values=clean_samples,
                    suggested_role=suggested_role if suggested_role != SemanticRole.OTHER else None,
                    stats=stats,
                )
            )

            if suggested_role != SemanticRole.OTHER:
                # If a role is already mapped, keep the higher confidence one
                role_key = suggested_role.value
                if role_key not in semantic_mappings or confidence > semantic_mappings[role_key].confidence:
                    semantic_mappings[role_key] = SemanticMapping(
                        column_name=col,
                        mapped_role=suggested_role,
                        confidence=confidence,
                        is_confirmed=confidence >= 0.7,
                        notes=f"Detected with {int(confidence * 100)}% confidence based on column name and data type."
                    )

        suggested_questions = cls.generate_suggested_questions(semantic_mappings, column_profiles)

        from datetime import datetime, timezone
        profile = DatasetProfile(
            dataset_id=dataset_id,
            filename=filename,
            file_size_bytes=file_size_bytes,
            row_count=row_count,
            column_count=col_count,
            duplicate_rows=duplicate_rows,
            columns=column_profiles,
            semantic_mappings=semantic_mappings,
            suggested_questions=suggested_questions,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        return profile

    @staticmethod
    def generate_suggested_questions(
        mappings: Dict[str, SemanticMapping], columns: List[ColumnProfile]
    ) -> List[str]:
        """Generates dynamic tailored sample questions matching present e-commerce fields."""
        questions: List[str] = []
        has_rev = "revenue" in mappings
        has_cat = "category" in mappings
        has_prod = "product" in mappings
        has_date = "order_date" in mappings
        has_region = "region" in mappings
        has_qty = "quantity" in mappings

        if has_rev:
            questions.append("What is the total revenue?")
        if has_prod and has_rev:
            questions.append("Which product generated the highest sales?")
            questions.append("Show the top 10 products by revenue.")
        if has_cat and has_rev:
            questions.append("Create a bar chart showing revenue by category.")
            questions.append("Which categories contribute the most to total sales?")
        if has_date and has_rev:
            questions.append("Plot monthly revenue as a line chart.")
            questions.append("Show monthly sales trends.")
        if has_region and has_rev:
            questions.append("Compare sales between different regions.")
        if has_qty and has_rev:
            questions.append("Show the relationship between quantity sold and revenue.")
        if has_rev and ("unit_price" in mappings or "order_id" in mappings):
            questions.append("What is the average order value?")

        questions.append("Give me a business summary of this dataset.")
        questions.append("What are the main trends and anomalies in this dataset?")

        return questions[:8]

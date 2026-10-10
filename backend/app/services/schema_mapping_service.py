"""Semantic schema mapping service: resolves business concepts to actual DataFrame columns safely."""

from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
from app.schemas.dataset import DatasetProfile, SemanticRole


class SchemaMappingService:
    """Safely resolves business roles (e.g. 'revenue', 'category') to concrete columns."""

    @staticmethod
    def resolve_column(
        df: pd.DataFrame,
        identifier: str,
        confirmed_mappings: Optional[Dict[str, str]] = None,
        profile: Optional[DatasetProfile] = None,
    ) -> Tuple[Optional[str], Optional[str]]:
        """Resolves an identifier (which may be a role like 'revenue' or an actual column name)
        to a verified column in the DataFrame.
        
        Returns:
            Tuple[resolved_column_name, error_message]
        """
        if not identifier or not isinstance(identifier, str):
            return None, "Column identifier must be a non-empty string."

        clean_id = identifier.strip()

        # 1. Direct match with actual DataFrame columns (case-insensitive)
        for col in df.columns:
            if col.lower() == clean_id.lower():
                return col, None

        # 2. Check confirmed mappings from session (e.g., 'revenue' -> 'sales_amount')
        role_key = clean_id.lower()
        if confirmed_mappings and role_key in confirmed_mappings:
            target_col = confirmed_mappings[role_key]
            if target_col in df.columns:
                return target_col, None

        # 3. Check profile semantic mappings
        if profile and profile.semantic_mappings:
            if role_key in profile.semantic_mappings:
                target_col = profile.semantic_mappings[role_key].column_name
                if target_col in df.columns:
                    return target_col, None

        # 4. Fallback search among column profiles
        if profile:
            for col_prof in profile.columns:
                if col_prof.suggested_role and col_prof.suggested_role.value == role_key:
                    if col_prof.name in df.columns:
                        return col_prof.name, None

        available_cols = list(df.columns)
        return None, (
            f"Could not resolve '{identifier}' to an existing column. "
            f"Available dataset columns are: {', '.join(available_cols)}."
        )

    @staticmethod
    def get_role_column_map(
        df: pd.DataFrame,
        confirmed_mappings: Optional[Dict[str, str]] = None,
        profile: Optional[DatasetProfile] = None,
    ) -> Dict[str, str]:
        """Returns a snapshot dictionary of all currently active role -> column mappings."""
        role_map: Dict[str, str] = {}
        if profile:
            for role_str, mapping in profile.semantic_mappings.items():
                if mapping.column_name in df.columns:
                    role_map[role_str] = mapping.column_name

        if confirmed_mappings:
            for role_str, col_name in confirmed_mappings.items():
                if col_name in df.columns:
                    role_map[role_str] = col_name

        return role_map

    @classmethod
    def identify_ambiguities(
        cls, df: pd.DataFrame, profile: DatasetProfile
    ) -> List[Dict[str, Any]]:
        """Identifies roles where multiple candidate columns exist with similar plausibility."""
        from app.services.profiling_service import SEMANTIC_PATTERNS
        ambiguities = []

        for role, patterns in SEMANTIC_PATTERNS.items():
            candidates = []
            for col in df.columns:
                col_lower = col.lower()
                for pat in patterns:
                    import re
                    if re.search(pat, col_lower):
                        candidates.append(col)
                        break
            if len(candidates) > 1:
                ambiguities.append({
                    "role": role.value,
                    "candidates": candidates,
                    "active_selection": profile.semantic_mappings.get(role.value).column_name
                    if profile.semantic_mappings.get(role.value) else candidates[0]
                })

        return ambiguities

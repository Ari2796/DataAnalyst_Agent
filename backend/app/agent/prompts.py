"""Token-optimized system prompts for the AI Data Analyst Agent."""

from typing import Any, Dict, Optional
from app.schemas.dataset import DatasetProfile


def build_system_prompt(profile: Optional[DatasetProfile], recent_entities: Dict[str, Any]) -> str:
    """Builds a condensed, token-efficient system prompt with essential schema & rules."""
    if not profile:
        return (
            "You are an AI E-Commerce Data Analyst. No dataset is currently loaded. "
            "Advise the user to upload a CSV file."
        )

    # Ultra-compact column list: name (type, role)
    col_tokens = []
    for c in profile.columns:
        role = f":{c.suggested_role.value}" if c.suggested_role else ""
        col_tokens.append(f"{c.name}({c.general_type.value}{role})")
    cols_str = ", ".join(col_tokens)

    # Active mappings
    mappings_str = ", ".join(
        f"{role}->{m.column_name}" for role, m in profile.semantic_mappings.items()
    ) or "None"

    # Context entities for pronouns
    entity_str = ""
    if recent_entities:
        entity_str = f"Context: {recent_entities}. "

    return (
        f"You are an expert E-Commerce Data Analyst. "
        f"Dataset: {profile.filename} ({profile.row_count:,} rows). "
        f"Columns: {cols_str}. "
        f"Mappings: {mappings_str}. {entity_str}"
        f"RULES:\n"
        f"1. Never invent numbers. Always compute via tools (calculate_metric, group_and_aggregate, get_top_n, compare_groups, analyze_time_trend, generate_chart_data).\n"
        f"2. For charts requested, call generate_chart_data.\n"
        f"3. Distinguish row count from order count (unique order_id).\n"
        f"4. Keep explanations concise, professional, and directly answered in 2-4 sentences."
    )

"""Agent execution engine: manages OpenAI tool-calling loop, memory, and fallback routing."""

import json
import logging
from typing import Any, Dict, List, Optional
from openai import OpenAI
from app.config import settings
from app.agent.prompts import build_system_prompt
from app.agent.tools import ANALYSIS_TOOLS_SPEC, execute_tool
from app.schemas.agent import ChatResponse, DataTable, ToolCallRecord
from app.schemas.charts import ChartSpec
from app.services.llm_service import LLMService
from app.services.session_service import SessionData, session_service

logger = logging.getLogger(__name__)


class AgentRunner:
    """Executes natural language queries using bounded tool-calling loops."""

    @classmethod
    async def run(
        cls,
        session: SessionData,
        user_message: str,
        confirmed_mappings: Optional[Dict[str, str]] = None,
    ) -> ChatResponse:
        """Main agent entrypoint."""
        if confirmed_mappings:
            session_service.update_mappings(session.dataset_id, confirmed_mappings)

        # Record user message in session history
        session_service.add_message(session.dataset_id, "user", user_message)

        client = LLMService.get_client()

        if client is None:
            # Fallback deterministic analysis if LLM is not configured yet
            logger.info("LLM not configured in .env. Running deterministic rule-based analysis.")
            return cls._execute_deterministic_fallback(session, user_message)

        # Execute live LLM agent loop
        return await cls._execute_llm_loop(client, session, user_message)

    @classmethod
    async def _execute_llm_loop(
        cls,
        client: OpenAI,
        session: SessionData,
        user_message: str,
    ) -> ChatResponse:
        """Executes the OpenAI tool-calling loop with bounded iterations."""
        recent_history = session_service.get_history(session.dataset_id, limit=settings.max_history_turns)
        system_prompt = build_system_prompt(session.profile, session.recent_entities)

        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt}
        ]

        # Append recent history (excluding the very latest user message to avoid duplicate)
        for turn in recent_history[:-1]:
            if turn.role in ("user", "assistant"):
                messages.append({"role": turn.role, "content": turn.content})

        # Append current user prompt
        messages.append({"role": "user", "content": user_message})

        tool_call_records: List[ToolCallRecord] = []
        captured_chart_spec: Optional[ChartSpec] = None
        captured_data_table: Optional[DataTable] = None
        limitations: List[str] = []

        iteration = 0
        final_answer = ""

        try:
            while iteration < settings.max_tool_iterations:
                iteration += 1

                response = client.chat.completions.create(
                    model=settings.llm_model,
                    messages=messages,
                    tools=ANALYSIS_TOOLS_SPEC,
                    tool_choice="auto",
                    temperature=0.1,
                    max_tokens=settings.max_output_tokens,
                )

                choice = response.choices[0]
                assistant_msg = choice.message

                # If no tool calls requested, assistant gave final answer
                if not assistant_msg.tool_calls:
                    final_answer = assistant_msg.content or "No textual summary provided."
                    break

                # Convert assistant message with tool calls to dict for conversation history
                tool_calls_serialized = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in assistant_msg.tool_calls
                ]

                messages.append({
                    "role": "assistant",
                    "content": assistant_msg.content,
                    "tool_calls": tool_calls_serialized,
                })

                # Execute each tool call
                for tc in assistant_msg.tool_calls:
                    fn_name = tc.function.name
                    try:
                        args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                    except json.JSONDecodeError:
                        args = {}

                    tool_result, success = execute_tool(fn_name, args, session)

                    # Update recent context entities
                    cls._extract_entities_from_call(session, fn_name, args, tool_result)

                    # Capture chart or tabular output if generated (full dataset for UI)
                    if fn_name == "generate_chart_data" and success and "chart_type" in tool_result:
                        try:
                            captured_chart_spec = ChartSpec(**tool_result)
                        except Exception as e:
                            logger.warning("Failed to parse ChartSpec: %s", e)

                    if fn_name in ("group_and_aggregate", "get_top_n") and success and "results" in tool_result:
                        res_list = tool_result["results"]
                        if res_list and isinstance(res_list, list):
                            cols = list(res_list[0].keys())
                            captured_data_table = DataTable(
                                title=f"{tool_result.get('aggregation', '').capitalize()} {tool_result.get('metric_column', '')} by {tool_result.get('group_by', '')}",
                                columns=cols,
                                rows=res_list[:15],
                                total_count=len(res_list),
                            )

                    summary_msg = f"Completed {fn_name}" if success else f"Error in {fn_name}: {tool_result.get('error')}"
                    tool_call_records.append(
                        ToolCallRecord(
                            tool_name=fn_name,
                            arguments=args,
                            result_summary=summary_msg,
                            success=success,
                        )
                    )

                    # Feed compact result back to LLM to save tokens
                    compact_payload = cls._compact_tool_payload(fn_name, tool_result)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(compact_payload, ensure_ascii=False),
                    })

            if not final_answer:
                # If iteration limit reached, ask LLM for a final summary based on tool results gathered
                final_res = client.chat.completions.create(
                    model=settings.llm_model,
                    messages=messages + [{
                        "role": "user",
                        "content": "Please provide your final brief business conclusion based on the above tool results.",
                    }],
                    temperature=0.1,
                    max_tokens=settings.max_output_tokens,
                )
                final_answer = final_res.choices[0].message.content or "Analysis completed."

        except Exception as e:
            logger.error("Error during LLM execution: %s", str(e), exc_info=True)
            final_answer = (
                f"An error occurred while contacting the LLM provider ({str(e)}). "
                "Deterministic calculations were executed where possible."
            )
            limitations.append(f"LLM API Communication error: {str(e)}")

        # Store response in session history
        session_service.add_message(session.dataset_id, "assistant", final_answer)

        # Dynamic follow-up questions
        follow_ups = cls._generate_follow_up_suggestions(session, user_message)

        return ChatResponse(
            dataset_id=session.dataset_id,
            message=final_answer,
            data_table=captured_data_table,
            chart_spec=captured_chart_spec,
            tool_calls=tool_call_records,
            follow_up_suggestions=follow_ups,
            limitations=limitations if limitations else None,
        )

    @classmethod
    def _execute_deterministic_fallback(
        cls, session: SessionData, user_message: str
    ) -> ChatResponse:
        """Determines best tool to execute using keyword heuristics when no LLM key is configured."""
        q = user_message.lower().strip()
        role_map = session.confirmed_mappings
        rev_col = role_map.get("revenue", "revenue")
        cat_col = role_map.get("category", "category")
        prod_col = role_map.get("product", "product_name")
        reg_col = role_map.get("region", "region")
        date_col = role_map.get("order_date", "order_date")
        qty_col = role_map.get("quantity", "quantity")

        tool_calls: List[ToolCallRecord] = []
        captured_chart_spec: Optional[ChartSpec] = None
        captured_data_table: Optional[DataTable] = None
        limitations = [
            "LLM API Key is not configured in backend/.env. Running deterministic Python analytical engine in offline mode."
        ]

        answer = ""
        # 1. Total revenue
        if "total revenue" in q or "total sales" in q or "how much revenue" in q:
            res, succ = execute_tool("calculate_metric", {"metric_column": rev_col, "aggregation": "sum"}, session)
            tool_calls.append(ToolCallRecord(tool_name="calculate_metric", arguments={"metric_column": rev_col}, result_summary="Total revenue calculated", success=succ))
            val = res.get("value", 0)
            answer = f"### Total Revenue\nThe total revenue recorded in this dataset is **${val:,.2f}** across {res.get('rows_evaluated', 0):,} records."

        # 2. Highest sales product / Top products
        elif "highest" in q and ("product" in q or "item" in q) or "top" in q and "product" in q:
            n = 10 if "10" in q else 5
            res, succ = execute_tool("get_top_n", {"entity_column": prod_col, "metric_column": rev_col, "n": n}, session)
            tool_calls.append(ToolCallRecord(tool_name="get_top_n", arguments={"entity_column": prod_col, "n": n}, result_summary=f"Top {n} products computed", success=succ))
            top_items = res.get("results", [])
            if top_items:
                top_p = top_items[0]
                answer = f"### Top Products by Revenue\nThe product with the highest revenue is **{top_p.get(prod_col, 'Top Product')}** with **${top_p.get(rev_col, 0):,.2f}** in sales."
                captured_data_table = DataTable(
                    title=f"Top {n} Products by Revenue",
                    columns=[prod_col, rev_col],
                    rows=top_items,
                    total_count=len(top_items),
                )
                chart_res, _ = execute_tool("generate_chart_data", {"chart_type": "bar", "x_axis": prod_col, "y_axis": rev_col, "limit": n, "title": f"Top {n} Products by Revenue"}, session)
                if "chart_type" in chart_res:
                    captured_chart_spec = ChartSpec(**chart_res)

        # 3. Bar chart / Revenue by category
        elif "category" in q or "categories" in q:
            is_chart = "chart" in q or "plot" in q or "show" in q
            res, succ = execute_tool("group_and_aggregate", {"group_by": cat_col, "metric_column": rev_col, "aggregation": "sum"}, session)
            tool_calls.append(ToolCallRecord(tool_name="group_and_aggregate", arguments={"group_by": cat_col, "metric_column": rev_col}, result_summary="Revenue grouped by category", success=succ))
            items = res.get("results", [])
            answer = f"### Revenue by Category\nAnalyzed sales distribution across **{len(items)}** product categories."
            captured_data_table = DataTable(
                title="Revenue by Category",
                columns=[cat_col, rev_col],
                rows=items,
                total_count=len(items),
            )
            chart_type = "pie" if "pie" in q else "bar"
            chart_res, _ = execute_tool("generate_chart_data", {"chart_type": chart_type, "x_axis": cat_col, "y_axis": rev_col, "title": "Revenue Distribution by Category"}, session)
            if "chart_type" in chart_res:
                captured_chart_spec = ChartSpec(**chart_res)

        # 4. Monthly trend / Line chart
        elif "monthly" in q or "trend" in q or "time" in q:
            res, succ = execute_tool("analyze_time_trend", {"metric_column": rev_col, "date_column": date_col, "freq": "M"}, session)
            tool_calls.append(ToolCallRecord(tool_name="analyze_time_trend", arguments={"metric_column": rev_col}, result_summary="Monthly trend computed", success=succ))
            trends = res.get("trend", [])
            answer = f"### Monthly Revenue Trend\nComputed monthly trajectory across **{len(trends)}** time periods."
            chart_res, _ = execute_tool("generate_chart_data", {"chart_type": "line", "x_axis": date_col, "y_axis": rev_col, "title": "Monthly Revenue Trend"}, session)
            if "chart_type" in chart_res:
                captured_chart_spec = ChartSpec(**chart_res)

        # 5. Region comparison
        elif "region" in q or "regions" in q:
            res, succ = execute_tool("group_and_aggregate", {"group_by": reg_col, "metric_column": rev_col}, session)
            tool_calls.append(ToolCallRecord(tool_name="group_and_aggregate", arguments={"group_by": reg_col, "metric_column": rev_col}, result_summary="Regional revenue grouped", success=succ))
            items = res.get("results", [])
            answer = f"### Regional Sales Performance\nBreakdown of total revenue across **{len(items)}** geographic regions."
            captured_data_table = DataTable(
                title="Revenue by Region",
                columns=[reg_col, rev_col],
                rows=items,
                total_count=len(items),
            )
            chart_res, _ = execute_tool("generate_chart_data", {"chart_type": "bar", "x_axis": reg_col, "y_axis": rev_col, "title": "Revenue by Region"}, session)
            if "chart_type" in chart_res:
                captured_chart_spec = ChartSpec(**chart_res)

        # 6. Scatter / Quantity vs Revenue
        elif "quantity" in q and "revenue" in q:
            chart_res, _ = execute_tool("generate_chart_data", {"chart_type": "scatter", "x_axis": qty_col, "y_axis": rev_col, "title": "Quantity vs Revenue Correlation"}, session)
            tool_calls.append(ToolCallRecord(tool_name="generate_chart_data", arguments={"chart_type": "scatter"}, result_summary="Scatter plot prepared", success=True))
            if "chart_type" in chart_res:
                captured_chart_spec = ChartSpec(**chart_res)
            answer = "### Quantity vs. Revenue Analysis\nScatter distribution comparing units sold against total transaction revenue."

        # 7. Summary / Overview / Anomalies
        elif "anomal" in q or "outlier" in q:
            res, succ = execute_tool("detect_basic_anomalies", {"metric_column": rev_col}, session)
            tool_calls.append(ToolCallRecord(tool_name="detect_basic_anomalies", arguments={"metric_column": rev_col}, result_summary="Anomalies detected", success=succ))
            anom_count = res.get("total_anomalies", 0)
            answer = (
                f"### Statistical Anomaly Detection\n"
                f"Identified **{anom_count}** outliers ({res.get('anomaly_rate_percent', 0)}% of dataset) "
                f"outside the bounds of ${res.get('lower_bound', 0):,.2f} to ${res.get('upper_bound', 0):,.2f}."
            )

        # Default fallback: Dataset Summary
        else:
            res, succ = execute_tool("get_dataset_summary", {}, session)
            tool_calls.append(ToolCallRecord(tool_name="get_dataset_summary", arguments={}, result_summary="Dataset summary generated", success=succ))
            tot_rev = res.get("total_revenue")
            rev_txt = f"Total revenue is **${tot_rev:,.2f}**." if tot_rev is not None else ""
            orders_txt = f"Contains **{res.get('unique_orders'):,}** unique orders." if res.get('unique_orders') else ""
            answer = (
                f"### Dataset Business Summary\n"
                f"The dataset contains **{res.get('total_rows'):,}** records across **{res.get('total_columns')}** columns. "
                f"{orders_txt} {rev_txt}\n\n"
                "You can ask specific questions like:\n"
                "- *What is the total revenue?*\n"
                "- *Show the top 10 products by revenue*\n"
                "- *Create a bar chart showing revenue by category*\n"
                "- *Plot monthly revenue as a line chart*"
            )

        session_service.add_message(session.dataset_id, "assistant", answer)
        follow_ups = cls._generate_follow_up_suggestions(session, user_message)

        return ChatResponse(
            dataset_id=session.dataset_id,
            message=answer,
            data_table=captured_data_table,
            chart_spec=captured_chart_spec,
            tool_calls=tool_calls,
            follow_up_suggestions=follow_ups,
            limitations=limitations,
        )

    @staticmethod
    def _extract_entities_from_call(
        session: SessionData, tool_name: str, args: Dict[str, Any], result: Dict[str, Any]
    ) -> None:
        """Saves recently evaluated entities and parameters to session memory for pronoun resolution."""
        updates = {}
        if "group_by" in args:
            updates["last_group_by"] = args["group_by"]
        if "metric_column" in args:
            updates["last_metric"] = args["metric_column"]
        if "group_a" in args:
            updates["last_cohort"] = args["group_a"]
        if tool_name in ("get_top_n", "group_and_aggregate") and "results" in result:
            top_res = result["results"]
            if top_res and len(top_res) > 0:
                first_k, first_v = list(top_res[0].items())[0]
                updates["top_entity"] = f"{first_k}: {first_v}"

        if updates:
            session_service.update_recent_entities(session.dataset_id, updates)

    @staticmethod
    def _compact_tool_payload(tool_name: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Compresses tool results returned to the LLM to minimize input tokens."""
        if not isinstance(result, dict):
            return result

        compact = result.copy()

        # For chart generation, LLM only needs status, not the raw data array
        if tool_name == "generate_chart_data":
            return {
                "status": "chart_rendered_successfully",
                "chart_type": compact.get("chart_type"),
                "title": compact.get("title"),
                "records_plotted": len(compact.get("data", [])),
            }

        # Truncate tabular lists to 5 rows for LLM reasoning
        if "results" in compact and isinstance(compact["results"], list) and len(compact["results"]) > 5:
            total = len(compact["results"])
            compact["results"] = compact["results"][:5]
            compact["note"] = f"Top 5 of {total} records summarized."

        if "trend" in compact and isinstance(compact["trend"], list) and len(compact["trend"]) > 6:
            compact["trend"] = compact["trend"][:6]

        if "sample_values" in compact and isinstance(compact["sample_values"], list):
            compact["sample_values"] = compact["sample_values"][:3]

        return compact

    @staticmethod
    def _generate_follow_up_suggestions(
        session: SessionData, user_message: str
    ) -> List[str]:
        """Provides intuitive next questions based on current conversation context."""
        q = user_message.lower()
        if "revenue" in q and "category" not in q:
            return [
                "Create a bar chart showing revenue by category.",
                "Plot monthly revenue as a line chart.",
                "Which product generated the highest sales?",
            ]
        elif "category" in q:
            return [
                "Which category has the highest average order value?",
                "What about its monthly trend?",
                "Compare sales between different regions.",
            ]
        elif "product" in q:
            return [
                "Which products are underperforming?",
                "Show the relationship between quantity sold and revenue.",
                "What are the main trends and anomalies in this dataset?",
            ]
        return [
            "Show monthly sales trends.",
            "Compare sales between different regions.",
            "Give me a business summary of this dataset.",
        ]

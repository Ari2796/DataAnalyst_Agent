"""Tests for conversational agent loop, session memory, isolation, and LLM mocking."""

import json
from unittest.mock import MagicMock
import pandas as pd
import pytest
from app.agent.agent import AgentRunner
from app.config import settings
from app.services.llm_service import LLMService
from app.services.profiling_service import ProfilingService
from app.services.session_service import session_service


@pytest.fixture
def mock_session(sample_df: pd.DataFrame):
    """Creates an active session with sample dataset."""
    sess = session_service.create_session("sess-test-agent", "sample.csv", sample_df, 500)
    sess.profile = ProfilingService.profile_dataset("sess-test-agent", "sample.csv", 500, sample_df)
    session_service.update_profile("sess-test-agent", sess.profile)
    return sess


@pytest.mark.asyncio
async def test_deterministic_fallback_when_llm_unconfigured(mock_session, monkeypatch):
    """Verifies that offline fallback responds intelligently to user queries when no key is set."""
    monkeypatch.setattr(settings, "llm_api_key", "")
    LLMService.reset_client()
    
    resp = await AgentRunner.run(mock_session, "What is the total revenue?")
    assert resp.dataset_id == mock_session.dataset_id
    assert "Total Revenue" in resp.message
    assert len(resp.tool_calls) > 0
    assert resp.tool_calls[0].tool_name == "calculate_metric"


@pytest.mark.asyncio
async def test_session_isolation(sample_df: pd.DataFrame):
    """Verifies that two independent sessions maintain strict data and history isolation."""
    sess_a = session_service.create_session("session-a", "a.csv", sample_df.head(5), 100)
    sess_b = session_service.create_session("session-b", "b.csv", sample_df.tail(10), 200)

    session_service.add_message("session-a", "user", "Hello from user A")
    session_service.add_message("session-b", "user", "Hello from user B")

    hist_a = session_service.get_history("session-a")
    hist_b = session_service.get_history("session-b")

    assert len(hist_a) == 1
    assert hist_a[0].content == "Hello from user A"
    assert len(hist_b) == 1
    assert hist_b[0].content == "Hello from user B"
    assert len(sess_a.df) == 5
    assert len(sess_b.df) == 10


@pytest.mark.asyncio
async def test_agent_tool_calling_with_mocked_llm(mock_session, monkeypatch):
    """Verifies that the agent loop invokes tools and completes reasoning with mocked LLM."""
    monkeypatch.setattr(settings, "llm_api_key", "sk-mock-valid-key")

    mock_client = MagicMock()

    # Step 1: LLM proposes calling calculate_metric
    call_msg = MagicMock()
    call_msg.content = None
    mock_tool_call = MagicMock()
    mock_tool_call.id = "call_abc123"
    mock_tool_call.type = "function"
    mock_tool_call.function.name = "calculate_metric"
    mock_tool_call.function.arguments = json.dumps({
        "metric_column": "sales_amount",
        "aggregation": "sum"
    })
    call_msg.tool_calls = [mock_tool_call]

    first_choice = MagicMock()
    first_choice.message = call_msg
    first_response = MagicMock(choices=[first_choice])

    # Step 2: LLM receives result and provides final text response
    final_msg = MagicMock()
    final_msg.content = "Verified total sales amount is $6,234.50 across all e-commerce transactions."
    final_msg.tool_calls = None
    second_choice = MagicMock()
    second_choice.message = final_msg
    second_response = MagicMock(choices=[second_choice])

    # Mock completions.create to return first_response then second_response
    mock_client.chat.completions.create.side_effect = [first_response, second_response]
    monkeypatch.setattr(LLMService, "get_client", lambda: mock_client)

    resp = await AgentRunner.run(mock_session, "Calculate total sales please.")

    assert "6,234.50" in resp.message
    assert len(resp.tool_calls) == 1
    assert resp.tool_calls[0].tool_name == "calculate_metric"
    assert resp.tool_calls[0].success is True


@pytest.mark.asyncio
async def test_agent_iteration_limit(mock_session, monkeypatch):
    """Verifies that infinite tool loops are safely bounded by max_tool_iterations."""
    monkeypatch.setattr(settings, "llm_api_key", "sk-mock-valid-key")
    monkeypatch.setattr(settings, "max_tool_iterations", 2)

    mock_client = MagicMock()

    # A mock that keeps asking to call tools forever
    looping_msg = MagicMock()
    looping_msg.content = None
    tc = MagicMock()
    tc.id = "call_loop"
    tc.type = "function"
    tc.function.name = "get_dataset_summary"
    tc.function.arguments = "{}"
    looping_msg.tool_calls = [tc]

    choice = MagicMock(message=looping_msg)
    loop_response = MagicMock(choices=[choice])

    # Final response after limit reached
    final_msg = MagicMock(content="Reached limit, concluded summary.")
    final_response = MagicMock(choices=[MagicMock(message=final_msg)])

    mock_client.chat.completions.create.side_effect = [loop_response, loop_response, final_response]
    monkeypatch.setattr(LLMService, "get_client", lambda: mock_client)

    resp = await AgentRunner.run(mock_session, "Keep looping")
    assert resp.message == "Reached limit, concluded summary."
    # Max tool iterations was 2, so exactly 2 iterations executed
    assert len(resp.tool_calls) == 2


@pytest.mark.asyncio
async def test_graceful_handling_of_llm_api_error(mock_session, monkeypatch):
    """Verifies that LLM connection errors are caught and surfaced cleanly without crashing."""
    monkeypatch.setattr(settings, "llm_api_key", "sk-mock-valid-key")

    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = RuntimeError("OpenAI connection timeout")
    monkeypatch.setattr(LLMService, "get_client", lambda: mock_client)

    resp = await AgentRunner.run(mock_session, "Tell me sales")
    assert "error occurred while contacting the LLM provider" in resp.message
    assert resp.limitations is not None
    assert any("OpenAI connection timeout" in lim for lim in resp.limitations)

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from agent.graph import build_graph
from agent.models import AgentConfig, ApiTestCase, ApiTestResult

async def test_graph_compiles_and_runs():
    config = AgentConfig(
        base_url="http://localhost:8080",
        spec_url="http://localhost:8080/openapi.json",
        max_iterations=1,
        token_budget=10000,
    )

    initial_state = {
        "config": config,
        "spec": {},
        "test_cases": [],
        "results": [],
        "evaluations": [],
        "iteration": 0,
        "new_cases_this_iteration": 0,
        "token_usage": 0,
        "termination_reason": None,
        "requirements": None,
        "source_code": None,
    }

    # What each node returns
    mock_test_case = ApiTestCase(
        id="TC-001",
        endpoint="/tasks",
        method="GET",
        headers={},
        payload=None,
        expected_status=200,
        rationale="Happy path"
    )

    mock_test_result = ApiTestResult(
        test_case=mock_test_case,
        status_received=200,
        response_body={},
        passed=True,
        error=None,
    )

    async def mock_parser(state):
        return {**state, "spec": {"endpoints": [{"path": "/tasks", "method": "GET", "summary": "Get tasks", "parameters": [], "requestBody": {}, "responses": {}}], "base_url": "http://localhost:8080"}}

    async def mock_generator(state):
        return {**state, "test_cases": [mock_test_case], "new_cases_this_iteration": 1, "token_usage": state.get("token_usage", 0) + 100}

    async def mock_reflection(state):
        return {**state, "token_usage": state.get("token_usage", 0) + 50}

    async def mock_executor(state):
        return {**state, "results": [mock_test_result]}

    async def mock_evaluator(state):
        from agent.models import EvaluationResult
        return {**state, "evaluations": [
            EvaluationResult(
                test_case=mock_test_case,
                status_received=200,
                passed=True,
                bug_detected=False,
                verdict="Response correct",
                reasoning="Status 200 returned as expected",
            )
        ], "token_usage": state.get("token_usage", 0) + 100}

    with patch("agent.graph.parser_node", mock_parser), \
        patch("agent.graph.generator_node", mock_generator), \
        patch("agent.graph.executor_node", mock_executor), \
        patch("agent.graph.evaluator_node", mock_evaluator), \
        patch("agent.graph.reflection_node", mock_reflection):

        graph = build_graph()
        result = await graph.ainvoke(initial_state)

    assert len(result["test_cases"]) >= 1
    assert len(result["results"]) >= 1
    assert len(result["evaluations"]) >= 1
    assert result["iteration"] == 1
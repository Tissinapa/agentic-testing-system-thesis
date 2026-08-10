import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from agent.nodes.executor import executor_node
from agent.models import AgentConfig, ApiTestCase

async def test_executor_runs_all_test_cases():
    config = AgentConfig(
        base_url="http://localhost:8080",
        spec_url="http://localhost:8080/openapi.json",
    )
    test_cases = [
        ApiTestCase(
            id="TC-001",
            endpoint="/tasks",
            method="GET",
            headers={},
            payload=None,
            expected_status=200,
            rationale="Happy path get all tasks"
        ),
        ApiTestCase(
            id="TC-002",
            endpoint="/tasks",
            method="POST",
            headers={},
            payload={"title": "Test"},
            expected_status=201,
            rationale="Happy path create task"
        ),
    ]
    state = {
        "config": config,
        "spec": {},
        "test_cases": test_cases,
        "results": [],
        "evaluations": [],
        "iteration": 0,
        "new_cases_this_iteration": 2,
        "token_usage": 300,
        "termination_reason": None,
        "requirements": None,
        "source_code": None,
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b'[]'
    mock_response.json.return_value = {}

    mock_client = AsyncMock()
    mock_client.request.return_value = mock_response

    with patch("agent.nodes.executor.httpx.AsyncClient") as mock_class:
        mock_class.return_value.__aenter__.return_value = mock_client
        mock_class.return_value.__aexit__.return_value = AsyncMock()

        result = await executor_node(state)

    assert len(result["results"]) == 2
    assert result["results"][0].status_received == 200
    assert result["results"][0].passed == True   # expected 200, got 200
    assert result["results"][1].passed == False  # expected 201, got 200
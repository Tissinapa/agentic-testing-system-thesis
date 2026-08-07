import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from agent.nodes.generator import generator_node
from agent.models import AgentConfig

mock_llm_response = """[
    {
        "id": "TC-001",
        "endpoint": "/tasks",
        "method": "POST",
        "headers": {},
        "payload": {"title": "Test task", "priority": 1},
        "expected_status": 201,
        "rationale": "Happy path - valid task creation"
    },
    {
        "id": "TC-002",
        "endpoint": "/tasks",
        "method": "POST",
        "headers": {},
        "payload": {"priority": 1},
        "expected_status": 400,
        "rationale": "Missing required title field"
    }
]"""

async def test_generator_produces_test_cases():
    config = AgentConfig(
        base_url="http://localhost:8080",
        spec_url="http://localhost:8080/openapi.json",
    )
    state = {
        "config": config,
        "spec": {
            "endpoints": [
                {"path": "/tasks", "method": "POST", "summary": "Create task",
                 "parameters": [], "requestBody": {}, "responses": {}}
            ]
        },
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

    mock_response = MagicMock()
    mock_response.content = mock_llm_response
    mock_response.usage_metadata = {"input_tokens": 100, "output_tokens": 200}

    # Patch the whole class, not the instance method
    with patch("agent.nodes.generator.ChatAnthropic") as mock_class:
        mock_instance = MagicMock()
        mock_instance.ainvoke = AsyncMock(return_value=mock_response)
        mock_class.return_value = mock_instance

        result = await generator_node(state)

    assert len(result["test_cases"]) == 2
    assert result["new_cases_this_iteration"] == 2
    assert result["token_usage"] == 300
    assert result["test_cases"][0].endpoint == "/tasks"
    assert result["test_cases"][1].expected_status == 400
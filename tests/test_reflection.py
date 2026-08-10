import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from agent.nodes.reflection import reflection_node
from agent.models import AgentConfig, ApiTestCase

mock_llm_response = """{
    "coverage_gaps": ["DELETE /tasks/{id} has no test case"],
    "issues_found": ["No authentication boundary test"],
    "additional_test_cases": [
        {
            "id": "TC-NEW-001",
            "endpoint": "/tasks/1",
            "method": "DELETE",
            "headers": {},
            "payload": null,
            "expected_status": 204,
            "rationale": "Missing DELETE endpoint coverage"
        }
    ]
}"""

async def test_reflection_adds_missing_cases():
    config = AgentConfig(
        base_url="http://localhost:8080",
        spec_url="http://localhost:8080/openapi.json",
    )
    existing_case = ApiTestCase(
        id="TC-001",
        endpoint="/tasks",
        method="POST",
        headers={},
        payload={"title": "Test"},
        expected_status=201,
        rationale="Happy path"
    )
    state = {
        "config": config,
        "spec": {
            "endpoints": [
                {"path": "/tasks", "method": "POST", "summary": "Create task",
                 "parameters": [], "requestBody": {}, "responses": {}},
                {"path": "/tasks/{id}", "method": "DELETE", "summary": "Delete task",
                 "parameters": [], "requestBody": {}, "responses": {}}
            ]
        },
        "test_cases": [existing_case],
        "results": [],
        "evaluations": [],
        "iteration": 0,
        "new_cases_this_iteration": 1,
        "token_usage": 100,
        "termination_reason": None,
        "requirements": None,
        "source_code": None,
    }

    mock_response = MagicMock()
    mock_response.content = mock_llm_response
    mock_response.usage_metadata = {"input_tokens": 50, "output_tokens": 100}

    with patch("agent.nodes.reflection.ChatAnthropic") as mock_class:
        mock_instance = MagicMock()
        mock_instance.ainvoke = AsyncMock(return_value=mock_response)
        mock_class.return_value = mock_instance

        result = await reflection_node(state)

    # Should have original + 1 new case from reflection
    assert len(result["test_cases"]) == 2
    assert result["test_cases"][1].endpoint == "/tasks/1"
    assert result["test_cases"][1].method == "DELETE"
    assert result["token_usage"] == 250  # 100 existing + 50 + 100 new
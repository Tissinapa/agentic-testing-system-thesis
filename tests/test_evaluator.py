import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from agent.nodes.evaluator import evaluator_node
from agent.models import AgentConfig, ApiTestCase, ApiTestResult

mock_llm_response = """[
    {
        "test_case_id": "TC-001",
        "status_received": 200,
        "passed": false,
        "bug_detected": true,
        "verdict": "Missing validation on required field",
        "reasoning": "Sending null title returned 200 instead of 400. This is a validation bug."
    }
]"""

async def test_evaluator_detects_bugs():
    config = AgentConfig(
        base_url="http://localhost:8080",
        spec_url="http://localhost:8080/openapi.json",
    )
    test_case = ApiTestCase(
        id="TC-001",
        endpoint="/tasks",
        method="POST",
        headers={},
        payload={"title": None},
        expected_status=400,
        rationale="Null title should be rejected"
    )
    test_result = ApiTestResult(
        test_case=test_case,
        status_received=200,
        response_body={"id": 1, "title": None},
        passed=False,
        error=None,
    )
    state = {
        "config": config,
        "spec": {},
        "test_cases": [test_case],
        "results": [test_result],
        "evaluations": [],
        "iteration": 0,
        "new_cases_this_iteration": 1,
        "token_usage": 300,
        "termination_reason": None,
        "requirements": None,
        "source_code": None,
    }

    mock_response = MagicMock()
    mock_response.content = mock_llm_response
    mock_response.usage_metadata = {"input_tokens": 100, "output_tokens": 150}

    with patch("agent.nodes.evaluator.ChatAnthropic") as mock_class:
        mock_instance = MagicMock()
        mock_instance.ainvoke = AsyncMock(return_value=mock_response)
        mock_class.return_value = mock_instance

        result = await evaluator_node(state)

    assert len(result["evaluations"]) == 1
    assert result["evaluations"][0].bug_detected == True
    assert result["evaluations"][0].test_case.id == "TC-001"
    assert result["evaluations"][0].verdict == "Missing validation on required field"
    assert result["token_usage"] == 550  # 300 + 100 + 150
import json
import pytest
from pathlib import Path
from unittest.mock import patch
from agent.results import export_results
from agent.models import AgentConfig, ApiTestCase, ApiTestResult, EvaluationResult

def make_state():
    config = AgentConfig(
        base_url="http://localhost:8080",
        spec_url="http://localhost:8080/openapi.json",
        max_iterations=3,
        token_budget=10000,
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
    result = ApiTestResult(
        test_case=test_case,
        status_received=200,
        response_body={},
        passed=False,
        error=None,
    )
    evaluation = EvaluationResult(
        test_case=test_case,
        status_received=200,
        passed=False,
        bug_detected=True,
        verdict="Missing validation",
        reasoning="Null title accepted — seeded bug B1",
    )
    return {
        "config": config,
        "spec": {"endpoints": []},
        "test_cases": [test_case],
        "results": [result],
        "evaluations": [evaluation],
        "iteration": 2,
        "new_cases_this_iteration": 0,
        "token_usage": 1500,
        "termination_reason": "max_iterations",
        "requirements": None,
        "source_code": None,
    }

def test_export_produces_correct_structure(tmp_path):
    state = make_state()

    with patch("agent.results.Path") as mock_path:
        mock_dir = mock_path.return_value.__truediv__.return_value
        mock_dir.mkdir = lambda **kwargs: None
        mock_dir.__truediv__ = lambda self, other: tmp_path / other

        output = export_results(state, "java")

    assert output["meta"]["target"] == "java"
    assert output["meta"]["iterations"] == 2
    assert output["meta"]["token_usage"] == 1500
    assert output["summary"]["test_cases_generated"] == 1
    assert output["summary"]["bugs_detected"] == 1
    assert len(output["bugs"]) == 1
    assert output["bugs"][0]["verdict"] == "Missing validation"

def test_export_saves_file(tmp_path):
    state = make_state()

    with patch("agent.results.Path") as mock_path:
        results_dir = tmp_path / "results" / "agent"
        results_dir.mkdir(parents=True, exist_ok=True)
        mock_path.return_value.__truediv__.return_value.__truediv__.return_value = results_dir / "agent_java_test.json"
        mock_path.return_value.__truediv__.return_value.mkdir = lambda **kwargs: None

        export_results(state, "java")
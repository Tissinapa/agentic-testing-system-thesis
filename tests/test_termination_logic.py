import pytest
from agent.nodes.termination_logic import termination_logic_node
from agent.models import AgentConfig, ApiTestCase, ApiTestResult

def make_state(iteration=0, token_usage=0, new_cases=1, results=[], spec_endpoints=["/tasks"]):
    config = AgentConfig(
        base_url="http://localhost:8080",
        spec_url="http://localhost:8080/openapi.json",
        max_iterations=3,
        token_budget=10000,
    )
    return {
        "config": config,
        "spec": {"endpoints": [{"path": ep} for ep in spec_endpoints]},
        "test_cases": [],
        "results": results,
        "evaluations": [],
        "iteration": iteration,
        "new_cases_this_iteration": new_cases,
        "token_usage": token_usage,
        "termination_reason": None,
        "requirements": None,
        "source_code": None,
    }

def test_stops_at_max_iterations():
    state = make_state(iteration=3)
    assert termination_logic_node(state) == "done"

def test_stops_at_token_budget():
    state = make_state(token_usage=10000)
    assert termination_logic_node(state) == "done"

def test_stops_when_no_new_cases():
    state = make_state(iteration=1, new_cases=0)
    assert termination_logic_node(state) == "done"

def test_iterates_when_conditions_not_met():
    state = make_state(iteration=1, token_usage=500, new_cases=3)
    assert termination_logic_node(state) == "iterate"

def test_stops_when_all_endpoints_covered():
    test_case = ApiTestCase(
        id="TC-001",
        endpoint="/tasks",
        method="GET",
        headers={},
        payload=None,
        expected_status=200,
        rationale="Happy path"
    )
    result = ApiTestResult(
        test_case=test_case,
        status_received=200,
        response_body={},
        passed=True,
        error=None,
    )
    state = make_state(
        iteration=1,
        new_cases=2,
        results=[result],
        spec_endpoints=["/tasks"]
    )
    assert termination_logic_node(state) == "done"
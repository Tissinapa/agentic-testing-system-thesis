import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from agent.nodes.parser import parser_node
from agent.models import AgentConfig

mock_spec = {
    "paths": {
        "/tasks": {
            "get": {"summary": "Get all tasks", "responses": {"200": {}}},
            "post": {"summary": "Create task", "responses": {"201": {}}}
        }
    }
}

async def test_parser_extracts_endpoints():
    config = AgentConfig(
        base_url="http://localhost:8080",
        spec_url="http://localhost:8080/openapi.json",
    )
    state = {
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

    mock_response = Mock()
    mock_response.json.return_value = mock_spec
    mock_response.raise_for_status = Mock()

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response

    with patch("agent.nodes.parser.httpx.AsyncClient") as mock_class:
        mock_class.return_value.__aenter__.return_value = mock_client
        mock_class.return_value.__aexit__.return_value = AsyncMock()
        result = await parser_node(state)

    assert len(result["spec"]["endpoints"]) == 2
    assert result["spec"]["endpoints"][0]["path"] == "/tasks"
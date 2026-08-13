import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from agent.run import run, load_file
import argparse

def make_args(**kwargs):
    defaults = {
        "target": "python",
        "base_url": "http://localhost:8000",
        "spec_url": "http://localhost:8000/openapi.json",
        "mode": "black",
        "max_iterations": 1,
        "token_budget": 10000,
        "requirements": None,
        "source_code": None,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)

def test_load_file_returns_none_for_missing_file():
    result = load_file("nonexistent_file.txt")
    assert result is None

def test_load_file_returns_content(tmp_path):
    f = tmp_path / "requirements.md"
    f.write_text("# Requirements\n- Task title is required")
    result = load_file(str(f))
    assert result == "# Requirements\n- Task title is required"

async def test_run_invokes_graph():
    args = make_args()

    mock_final_state = {
        "config": MagicMock(),
        "spec": {},
        "test_cases": [MagicMock()],
        "results": [MagicMock()],
        "evaluations": [MagicMock(bug_detected=True)],
        "iteration": 1,
        "new_cases_this_iteration": 0,
        "token_usage": 500,
        "termination_reason": "max_iterations",
        "requirements": None,
        "source_code": None,
    }

    with patch("agent.run.build_graph") as mock_build, \
         patch("agent.run.export_results") as mock_export:

        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock(return_value=mock_final_state)
        mock_build.return_value = mock_graph
        mock_export.return_value = {}

        await run(args)

        mock_graph.ainvoke.assert_called_once()
        mock_export.assert_called_once_with(mock_final_state, "python")
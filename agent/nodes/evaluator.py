import json
from pathlib import Path
from langchain_anthropic import ChatAnthropic
from agent.models import AgentState, EvaluationResult, ApiTestResult

PROMPT_PATH = Path(__file__).parent.parent /"prompts" / "evaluation_prompt.txt"
BATCH_SIZE = 10

def _find_test_case(results, test_case_id):
        for r in results:
            if r.test_case.id == test_case_id:
                return r.test_case
        # Fallback — return first result if only one exists
        if len(results) == 1:
            return results[0].test_case
        return None

def _build_prompt(batch: list[ApiTestResult], requirements: str) -> str:
    template = PROMPT_PATH.read_text()
    return template.format(
        results=json.dumps([{
            "test_case": r.test_case.model_dump(),
            "status_received": r.status_received,
            "response_body": r.response_body,
            "passed": r.passed,
            "error": r.error,
        } for r in batch], indent=2),
        requirements=requirements,
    )     
def _extract_json(raw: str) -> str:
    raw = raw.strip()
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()
    start, end = raw.find("["), raw.rfind("]")
    return raw[start:end+1] if start != -1 and end != -1 else raw  

def _parse_evaluations(raw: str, results: list[ApiTestResult]) -> list[EvaluationResult]:
    evaluations = []
    try:
        data = json.loads(_extract_json(raw))
        for e in data:
            try:
                test_case = _find_test_case(results, e.get("test_case_id", ""))
                if test_case is None:
                    continue
                evaluations.append(EvaluationResult(
                    test_case=test_case,
                    status_received=e["status_received"],
                    passed=e["passed"],
                    bug_detected=e["bug_detected"],
                    verdict=e["verdict"],
                    reasoning=e["reasoning"],
                ))
            except Exception as ex:
                print(f"Warning: skipping evaluation: {ex}")
    except json.JSONDecodeError as e:
        print(f"Warning: evaluator batch JSON parsing failed: {e}")
    return evaluations

async def _evaluate_batch(
    llm, batch: list[ApiTestResult],
    results: list[ApiTestResult],
    requirements: str ) -> tuple[list[EvaluationResult], int]:
    response = await llm.ainvoke(_build_prompt(batch, requirements))
    tokens = (
        response.usage_metadata.get("input_tokens", 0) +
        response.usage_metadata.get("output_tokens", 0)
    )
    evaluations = _parse_evaluations(response.content, results)
    return evaluations, tokens

async def evaluator_node(state: AgentState) -> AgentState:
    if state["token_usage"] >= state["config"].token_budget:
        print(f"Token budget exhausted before evaluation ({state['token_usage']}/{state['config'].token_budget})")
        return {**state, "evaluations": []}

    llm = ChatAnthropic(model="claude-sonnet-4-6", max_tokens=4000)
    results = state["results"]
    requirements = state.get("requirements") or "No additional requirements."

    all_evaluations = []
    total_tokens = 0

    for i in range(0, len(results), BATCH_SIZE):
        batch = results[i:i+BATCH_SIZE]
        evals, tokens = await _evaluate_batch(llm, batch, results, requirements)
        all_evaluations.extend(evals)
        total_tokens += tokens

    return {
        **state,
        "evaluations": all_evaluations,
        "token_usage": state["token_usage"] + total_tokens,
    }  
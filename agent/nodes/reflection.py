import json
import re
from langchain_anthropic import ChatAnthropic
from agent.models import AgentState, ApiTestCase
from pathlib import Path

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "reflection_prompt.txt"

def _build_prompt(state: AgentState) -> str:
    template = PROMPT_PATH.read_text()
    requirements = state.get("requirements") or "No additional requirements."
    
    # Extract auth token
    
    auth_token = "NO_TOKEN_PROVIDED"
    patterns = [r'Token value:\s*(\S+)', r'token value:\s*(\S+)']
    for pattern in patterns:
        match = re.search(pattern, requirements, re.IGNORECASE)
        if match:
            token = match.group(1)
            if not token.startswith("<") and len(token) > 3:
                auth_token = token
                break

    failed_evaluations = [
        {
            "test_case": e.test_case.model_dump(),
            "status_received": e.status_received,
            "bug_detected": e.bug_detected,
            "verdict": e.verdict,
            "reasoning": e.reasoning,
        }
        for e in state["evaluations"]
        if e.bug_detected or not e.passed
    ]

    return template.format(
        endpoints=json.dumps(state["spec"]["endpoints"], indent=2),
        failed_evaluations=json.dumps(failed_evaluations, indent=2),
        requirements=requirements,
        auth_token=auth_token,
    )

# Extract json array from llm response
def _extract_json(raw: str) -> str:
    raw = raw.strip()
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()
    start, end = raw.find("{"), raw.rfind("}")
    return raw[start:end+1] if start != -1 and end != -1 else raw


def _parse_additional_cases(raw: str) -> list[ApiTestCase]:
    cases = []
    try:
        data = json.loads(_extract_json(raw))
        for tc in data.get("additional_test_cases", []):
            try:
                cases.append(ApiTestCase(**tc))
            except Exception as e:
                print(f"Warning: skipping reflection test case: {e}")
    except json.JSONDecodeError as e:
        print(f"Warning: reflection JSON parsing failed: {e}")
    return cases

def _count_tokens(response) -> int:
    return (
        response.usage_metadata.get("input_tokens", 0) +
        response.usage_metadata.get("output_tokens", 0)
    )

async def reflection_node(state: AgentState) -> AgentState:
    if state["token_usage"] >= state["config"].token_budget:
        print(f"Token budget exhausted before reflection ({state['token_usage']}/{state['config'].token_budget})")
        return state
    # Skip if no evaluations yet
    if not state.get("evaluations"):
        print("No evaluations to reflect on — skipping reflection")
        return state
    
    llm = ChatAnthropic(model="claude-sonnet-4-6", max_tokens=2000)
    response = await llm.ainvoke(_build_prompt(state))
    additional = _parse_additional_cases(response.content)

    print(f"Reflection added {len(additional)} follow-up test cases")
    
    return {
        **state,
        "test_cases": state["test_cases"] + additional,
        "new_cases_this_iteration": state["new_cases_this_iteration"] + len(additional),
        "token_usage": state["token_usage"] + _count_tokens(response),
    }
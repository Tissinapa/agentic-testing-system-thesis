import json
import uuid
import re
from langchain_anthropic import ChatAnthropic
from agent.models import AgentState, ApiTestCase
from pathlib import Path



PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "generation_prompt.txt"

def _build_prompt(state: AgentState) -> str:
    template = PROMPT_PATH.read_text()
    requirements = state.get("requirements")
    print(f"DEBUG in generator: requirements = '{str(requirements)[:100]}'")
    
    # Handle None safely
    requirements_text = requirements or "No additional requirements."
    
    auth_token = "NO_TOKEN_PROVIDED"
    if requirements:
        import re
        patterns = [
            r'Token value:\s*(\S+)',
            r'token value:\s*(\S+)',
            r'- Token value:\s*(\S+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, requirements, re.IGNORECASE)
            if match:
                token = match.group(1)
                if not token.startswith("<") and len(token) > 3:
                    auth_token = token
                    break

    print(f"DEBUG: extracted auth_token = '{auth_token}'")
    
    return template.format(
        endpoints=json.dumps(state["spec"]["endpoints"], indent=2),
        requirements=requirements_text,
        previous_cases=json.dumps(
            [tc.model_dump() for tc in state["test_cases"]], indent=2
        ),
        auth_token=auth_token,
    )

def _extract_json(raw: str) -> str:
    # Extract json array from llm response
    raw = raw.strip()
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()
    start, end = raw.find("["), raw.rfind("]")
    return raw[start:end+1] if start != -1 and end != -1 else raw

def _parse_test_cases(raw: str) -> list[ApiTestCase]:
    cases = []
    try:
        data = json.loads(_extract_json(raw))
        for tc in data:
            try:
                tc["id"] = f"TC-{str(uuid.uuid4())[:8].upper()}"
                cases.append(ApiTestCase(**tc))
            except Exception as e:
                print(f"Warning: skipping invalid test case: {e}")
    except json.JSONDecodeError as e:
        print(f"Warning: generator JSON parsing failed: {e}")
    return cases

def _count_tokens(response) -> int:
    return (
        response.usage_metadata.get("input_tokens", 0) +
        response.usage_metadata.get("output_tokens", 0)
    )
    
    
    
async def generator_node(state: AgentState) -> AgentState:
    if state["token_usage"] >= state["config"].token_budget:
        print(f"Token budget exhausted before generation ({state['token_usage']}/{state['config'].token_budget})")
        return {**state, "new_cases_this_iteration": 0}

    llm = ChatAnthropic(model="claude-sonnet-4-6", max_tokens=6000)
    response = await llm.ainvoke(_build_prompt(state))
    new_cases = _parse_test_cases(response.content)

    return {
        **state,
        "test_cases": state["test_cases"] + new_cases,
        "new_cases_this_iteration": len(new_cases),
        "token_usage": state["token_usage"] + _count_tokens(response),
    }
    
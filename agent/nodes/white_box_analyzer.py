import json
from langchain_anthropic import ChatAnthropic
from agent.models import AgentState, ApiTestCase, EvaluationResult
from pathlib import Path

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "white_box_prompt.txt"

def _build_prompt(state: AgentState) -> str:
    template = PROMPT_PATH.read_text()
    return template.format(
        source_code = state.get("source_code") or "",
        requirements = state.get("requirements") or "No requirements provided.",
    )
    
def _count_tokens(response) -> int:
    return (
        response.usage_metadata.get("input_tokens",0) +
        response.usage_metadata.get("output_tokens",0)
    )

def _extract_json(raw: str) -> str:
    raw = raw.strip()
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()
    
    # Try object first then array
    obj_start, obj_end = raw.find("{"), raw.rfind("}")
    arr_start, arr_end = raw.find("["), raw.rfind("]")
    
    if obj_start != -1 and obj_end != -1:
        if arr_start != -1 and arr_start < obj_start:
            return raw[arr_start:arr_end+1]
        return raw[obj_start:obj_end+1]
    elif arr_start != -1 and arr_end != -1:
        return raw[arr_start:arr_end+1]
    return raw

def _parse_findings(raw: str) -> list[EvaluationResult]:
    findings = []
    try:
        extracted = _extract_json(raw)
        data=json.loads(_extract_json(raw))
        # Handle both array and object responses
        if isinstance(data, list):
            findings_data = data
        elif isinstance(data, dict):
            findings_data = data.get("findings", [])
        else:
            print(f"Warning: unexpected JSON structure")
            return []
        for i , finding in enumerate(findings_data):
            try:
                tc = ApiTestCase(
                    id=f"WB-{str(i+1).zfill(3)}",
                    endpoint=finding.get("location", "source_code"),
                    method="GET",
                    headers={},
                    payload=None,
                    expected_status=200,
                    rationale=f"White-box: {finding.get('type', 'issue')}"
                )
                findings.append(EvaluationResult(
                    test_case=tc,
                    status_received=0,
                    passed=False,
                    bug_detected=True,
                    verdict=finding.get("title", "Issue found"),
                    reasoning=finding.get("description", ""),
                )) 
            except Exception as e:
                print(f"Warning: skipping findings: {e}")        
        
    except json.JSONDecodeError as e:
        print(f"Warning: white-box analysis JSON failed: {e}")
    
    return findings

async def white_box_analyzer_node(state: AgentState ) -> AgentState:
    if not state.get("source_code"):
        print("Warning: White-box mode requires source code")
        return state
    if state["token_usage"] >= state["config"].token_budget:
        print(f"Token budget exhausted before white-box analysis")
        return state
    
    llm = ChatAnthropic(model ="claude-sonnet-4-6", max_tokens = 4000)
    response = await llm.ainvoke(_build_prompt(state))
    findings = _parse_findings(response.content)
    
    print(f"White-box analysis found {len(findings)} issues")
    
    return {
        **state,
        "evaluations": state["evaluations"] + findings,
        "token_usage": state["token_usage"] + _count_tokens(response),
    }
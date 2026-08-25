import json
from pathlib import Path
from langchain_anthropic import ChatAnthropic
from agent.models import AgentState, EvaluationResult

PROMPT_PATH = Path(__file__).parent.parent /"prompts" / "evaluation_prompt.txt"


def find_test_case(results, test_case_id):
        for r in results:
            if r.test_case.id == test_case_id:
                return r.test_case
        # Fallback — return first result if only one exists
        if len(results) == 1:
            return results[0].test_case
        return None

async def evaluator_node(state: AgentState) -> AgentState:
    llm = ChatAnthropic(model= "claude-sonnet-4-6",max_tokens=6000)# Change this later
    
    results= state["results"]
    requirements = state.get("requirements") or "No additional requirements provided."
    
    prompt_template = PROMPT_PATH.read_text()
    
    all_evaluations = []
    batch_size = 10

    for i in range(0, len(results), batch_size):
        batch = results[i:i+batch_size]
        prompt = prompt_template.format(
            results=json.dumps([{
                "test_case": r.test_case.model_dump(),
                "status_received": r.status_received,
                "response_body": r.response_body,
                "passed": r.passed,
                "error": r.error,
            } for r in batch], indent=2),
            requirements=requirements,
        )
        response = await llm.ainvoke(prompt)
        raw = response.content.strip()

        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()

        start = raw.find("[")
        end = raw.rfind("]")
        if start != -1 and end != -1:
            raw = raw[start:end+1]

        try:
            batch_data = json.loads(raw)
        except json.JSONDecodeError as e:
            print(f"Warning: batch {i//batch_size} evaluation failed: {e}")
            continue

        for e in batch_data:
            try:
                test_case = find_test_case(results, e.get("test_case_id", ""))
                if test_case is None:
                    continue
                all_evaluations.append(EvaluationResult(
                    test_case=test_case,
                    status_received=e["status_received"],
                    passed=e["passed"],
                    bug_detected=e["bug_detected"],
                    verdict=e["verdict"],
                    reasoning=e["reasoning"],
                ))
            except Exception as ex:
                print(f"Warning: skipping evaluation: {ex}")
                continue
    
    return {
        **state,
        "evaluations": all_evaluations,
        "token_usage": state["token_usage"] + response.usage_metadata.get("input_tokens", 0) + response.usage_metadata.get("output_tokens", 0),
    }  
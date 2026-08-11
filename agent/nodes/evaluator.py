import json
from pathlib import Path
from langchain_anthropic import ChatAnthropic
from agent.models import AgentState, EvaluationResult

PROMPT_PATH = Path(__file__).parent.parent /"prompts" / "evaluation_prompt.txt"




async def evaluator_node(state: AgentState) -> AgentState:
    llm = ChatAnthropic(model= "claude-sonne-4-6",max_tokens=2000)# Change this later
    
    results= state["results"]
    requirements = state.get("requirements") or "No additional requirements provided."
    
    prompt_template = PROMPT_PATH.read_text()
    prompt = prompt_template.format(
        results = json.dumps([{
            "test_case": r.test_case.model_dump(),
            "status_received": r.status_received,
            "response_body": r.response_body,
            "passed": r.passed,
            "error": r.error,
        }for r in results], indent = 2),
        requirements = requirements
    )

    response = await llm.ainvoke(prompt)
    raw = response.content
    
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        raw = raw.rsplit("```", 1)[0]
        
    evaluations_data = json.loads(raw)
    evaluations = []
    
    def find_test_case(results, test_case_id):
        for r in results:
            if r.test_case.id == test_case_id:
                return r.test_case
        # Fallback — return first result if only one exists
        if len(results) == 1:
            return results[0].test_case
        return None
    
    for e in evaluations_data:
        test_case = find_test_case(results, e["test_case_id"])
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
    
    return {
        **state,
        "evaluations": evaluations,
        "token_usage": state["token_usage"] + response.usage_metadata.get("input_tokens", 0) + response.usage_metadata.get("output_tokens", 0),
    }  
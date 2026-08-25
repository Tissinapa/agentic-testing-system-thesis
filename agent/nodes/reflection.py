import json
from langchain_anthropic import ChatAnthropic
from agent.models import AgentState, ApiTestCase
from pathlib import Path

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "reflection_prompt.txt"

async def reflection_node(state: AgentState)-> AgentState:
    llm = ChatAnthropic(model="claude-sonnet-4-6",max_tokens=4000)
    
    endpoints = state["spec"]["endpoints"]
    test_cases = [tc.model_dump() for tc in state["test_cases"]]
                
    prompt_template = PROMPT_PATH.read_text()
    prompt = prompt_template.format(
        endpoints = json.dumps(endpoints, indent=2),
        test_cases = json.dumps(test_cases, indent=2),
    )
    
    response = await llm.ainvoke(prompt)
    raw = response.content.strip()
    
    # Extract JSON robustly
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()

    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1:
        raw = raw[start:end+1]

    try:
        reflection_data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"Warning: reflection JSON parsing failed: {e}")
        return {
            **state,
            "token_usage": state["token_usage"] + response.usage_metadata.get("input_tokens", 0) + response.usage_metadata.get("output_tokens", 0),
        }

    additional_cases = []
    for tc in reflection_data.get("additional_test_cases", []):
        try:
            additional_cases.append(ApiTestCase(**tc))
        except Exception as e:
            print(f"Warning: skipping invalid test case: {e}")
            continue
        
        
    return {
        **state,
        "test_cases": state["test_cases"] + additional_cases,
        "new_cases_this_iteration": state["new_cases_this_iteration"] + len(additional_cases),
        "token_usage": state["token_usage"] + response.usage_metadata.get("input_tokens", 0 )+ response.usage_metadata.get("output_tokens",0),
    }
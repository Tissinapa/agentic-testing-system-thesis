import json
import uuid
from langchain_anthropic import ChatAnthropic
from agent.models import AgentState, ApiTestCase
from pathlib import Path




PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "generation_prompt.txt"

def extract_json(raw: str) -> str:
    # Extract json array from llm response
    raw = raw.strip()
    
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```json" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()
    
    start = raw.find("[")
    end = raw.find("]")
    if start != -1 and end != -1:
        raw = raw[start:end+1]
    return raw

async def generator_node(state: AgentState) -> AgentState:
    llm = ChatAnthropic(model="claude-sonnet-4-6", max_tokens=8000) #Change tokens later
    
    endpoints = state["spec"]["endpoints"]
    requirements = state.get("requirements") or "No additional requirements provided."
    #source_code = state.get("source_code") or "No source code provided."
    previous_cases = [tc.model_dump() for tc in state["test_cases"]]
    
    prompt_template = PROMPT_PATH.read_text()
    prompt = prompt_template.format(
        endpoints=json.dumps(endpoints, indent=2),
        requirements=requirements,
        previous_cases=json.dumps(previous_cases, indent=2),
    )
    
    response = await llm.ainvoke(prompt)
    raw = response.content
    
    try:
        raw = extract_json(raw)
        test_cases_data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"Warning: JSON parsing failed: {e}")
        print(f"Raw response preview: {raw[:200]}")
        return {
            **state,
            "test_cases": state["test_cases"],
            "new_cases_this_iteration": 0,
            "token_usage": state["token_usage"] + response.usage_metadata.get("input_tokens", 0) + response.usage_metadata.get("output_tokens", 0),
        }

    new_cases = []
    for tc in test_cases_data:
        try:
            tc["id"] = f"TC-{str(uuid.uuid4())[:8].upper()}"
            new_cases.append(ApiTestCase(**tc))
        except Exception as e:
            print(f"Warning: skipping invalid test case: {e}")
            continue
    #New test case tracking during iteration
    new_count = len(new_cases)  
    
    return {
        **state,
        "test_cases": state["test_cases"] + new_cases,
        "new_cases_this_iteration": new_count,
        "token_usage": state["token_usage"]+ response.usage_metadata.get("input_tokens", 0 ) + response.usage_metadata.get("output_tokens", 0),
    }

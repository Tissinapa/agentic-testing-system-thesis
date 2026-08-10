import json
import uuid
from langchain_anthropic import ChatAnthropic
from agent.models import AgentState, ApiTestCase
from pathlib import Path




PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "generation_prompt.txt"

async def generator_node(state: AgentState) -> AgentState:
    llm = ChatAnthropic(model="claude-sonnet-4-6", max_tokens=4000) #Change tokens later
    
    endpoints = state["spec"]["endpoints"]
    requirements = state["requirements"] or "No additional requirements provided."
    previous_cases = [tc.model_dump() for tc in state["test_cases"]]
    
    prompt_template = PROMPT_PATH.read_text()
    prompt = prompt_template.format(
        endpoints=json.dumps(endpoints, indent=2),
        requirements=requirements,
        previous_cases=json.dumps(previous_cases, indent=2),
    )
    
    response = await llm.ainvoke(prompt)
    raw = response.content
    
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        raw = raw.rsplit("```", 1)[0]
    
    test_cases_data = json.loads(raw)
    
    new_cases = []
    for tc in test_cases_data:
        tc["id"] = f"TC-{str(uuid.uuid4())[:8].upper()}"
        new_cases.append(ApiTestCase(**tc))
        
    #New test case tracking during iteration
    new_count = len(new_cases)  
    
    return {
        **state,
        "test_cases": state["test_cases"] + new_cases,
        "new_cases_this_iteration": new_count,
        "token_usage": state["token_usage"]+ response.usage_metadata.get("input_tokens", 0 ) + response.usage_metadata.get("output_tokens", 0),
    }

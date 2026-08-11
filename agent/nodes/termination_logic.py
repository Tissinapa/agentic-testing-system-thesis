from agent.models import AgentState

def termination_logic_node(state: AgentState) -> AgentState:
    config = state["config"]
    
    
    # maximum iteration reached
    if state["iteration"] >= config.max_iterations:
        return "done"
    
    # Maximum token budget reached
    if state["token_usage"] >= config.token_budget:
            return "done"
        
    # "Quality stop" no new test cases found
    if state["iteration"] > 0 and state["new_cases_this_iteration"] == 0:
            return "done"
    
    # "Quality stop" all enpoints covered
    tested_endpoints = {r.test_case.endpoint for r in state["results"]}
    all_endpoints = {endpoints["path"] for endpoints in state["spec"].get("endpoints", [])}
    if all_endpoints and tested_endpoints >=all_endpoints:
        return "done"
    
    return "iterate"
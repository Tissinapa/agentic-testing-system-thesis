import httpx
from agent.models import AgentState

async def parser_node(state: AgentState) -> AgentState:
    
    # Skip spec fetching in white-box mode
    if state["config"].mode == "white":
        return {
            **state,
            "spec": {"endpoints": [], "base_url": state["config"].base_url}
        }
    spec_url = state['config'].spec_url

    async with httpx.AsyncClient() as client:
        response = await client.get(spec_url)
        response.raise_for_status()
        spec = response.json()

    endpoints = []
    for path, methods in spec.get("paths", {}).items():
        for method, details in methods.items():
            if method.upper() not in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                continue
            endpoints.append({
                "path": path,
                "method": method.upper(),
                "summary": details.get("summary", ""),
                "parameters": details.get("parameters", []),
                "requestBody": details.get("requestBody", {}),
                "responses": details.get("responses", {}),
            })

    return {
        **state,           # ← spread all existing state first
        "spec": {
            "raw": spec,
            "endpoints": endpoints,
            "base_url": state["config"].base_url,
        }
    }
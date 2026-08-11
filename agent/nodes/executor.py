import httpx
import asyncio
from agent.models import AgentState, ApiTestCase, ApiTestResult

async def execute_single(client: httpx.AsyncClient, tc: ApiTestCase, base_url: str)-> ApiTestResult:
    url = f"{base_url}{tc.endpoint}"
    
    try:
        response = await client.request(
            method=tc.method,
            url=url,
            headers=tc.headers,
            json=tc.payload
        )
        return ApiTestResult(
            test_case=tc,
            status_received=response.status_code,
            response_body=response.json() if response.content else None,
            passed=response.status_code ==tc.expected_status,
        )
    except Exception as e:
        return ApiTestResult(
            test_case=tc,
            status_received=0,
            response_body=None,
            passed=False,
            error=str(e),
        )
async def executor_node(state: AgentState) -> AgentState:
    base_url = state["config"].base_url
    test_cases = state["test_cases"]
    
    async with httpx.AsyncClient(timeout=10.0)as client:
        tasks =[execute_single(client, tc, base_url) for tc in test_cases]
        results = await asyncio.gather(*tasks)
    return{
        **state,
        "results": list(results),
    }    
from pydantic import BaseModel
from typing import Optional, Literal, Union
from typing_extensions import TypedDict



# For test case generation
class ApiTestCase(BaseModel):
    id: str         
    endpoint: str       # api endpoint
    method: Literal["GET","POST","PUT","DELETE","PATCH"]
    headers: dict = {}
    payload: Optional[dict] = None
    expected_status: int 
    rationale: str      # why this test was generated
    


#For test executor
class ApiTestResult(BaseModel):
    test_case: ApiTestCase
    status_received: int
    response_body: Optional[Union[dict,list]] = None
    passed: bool
    error: Optional[str] = None



#For test evaluation
class EvaluationResult(BaseModel):
    test_case: ApiTestCase
    status_received: int
    passed: bool
    bug_detected: bool
    verdict: str    #LLm short verdict
    reasoning: str  #LLM reasoning
        
        
# For Lang Graph config
class AgentConfig(BaseModel):
    base_url: str
    spec_url: str
    
    target: Literal["java","python"] = "python"
    mode: Literal["black","white"] = "black"
    max_iterations: int = 3    #This can be changed later
    token_budget: int = 10000   #Change this later
    requirements: Optional[str] = None
    source_code: Optional[str] = None
        
# For Lang Graph state
class AgentState(TypedDict):
    config: AgentConfig

    spec: dict
    test_cases: list[ApiTestCase]
    results: list[ApiTestResult]
    evaluations: list[EvaluationResult]
    iteration: int
    new_cases_this_iteration: int
    token_usage: int
    termination_reason: Optional[str]
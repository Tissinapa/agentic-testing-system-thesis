from pydantic import BaseModel
from typing import Optional, Literal
from typing_extensions import TypedDict



# For test case generation
class TestCase(BaseModel):
    id: str         
    endpoint: str       # api endpoint
    method: Literal["GET","POST","PUT","DELETE","PATCH"]
    headers: dict = {}
    payload: Optional[dict] = None
    expected_status: int
    rationale: str      # why this test was generated
    


#For test executor
class TestResult(BaseModel):
    test_case: TestCase
    status_received: int
    response_body: Optional[dict] = None
    passsed: bool
    error: Optional[str] = None



#For test evaluation
class EvaluationResult(BaseModel):
    test_case: TestCase
    status_received: int
    passed: bool
    bug_detected: bool
    verdict: str    #LLm short verdict
    reasoning: str  #LLM reasoning
        
        
# For Lang Graph config
class AgentConfig(BaseModel):
    
    
    
    
    max_iterations: int = 3    #This can be changed later
    token_budget: int = 22   #Change this later
        
# For Lang Graph state
class AgentState(TypedDict):
    config: AgentConfig

    spec: dict
    test_cases: list[TestCase]
    results: list[TestResult]
    evaluations: list[EvaluationResult]
    iteration: int
    new_cases_this_iteration: int
    token_usage: int
    termination_reason: Optional[str]
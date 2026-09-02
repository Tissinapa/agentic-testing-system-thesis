import json
from pathlib import Path
from datetime import datetime
from agent.models import AgentState

def export_results(state: AgentState, target: str) -> dict:
    bugs_detected = [e for e in state["evaluations"] if e.bug_detected]
    
    output = {
        "meta": {
            "target": target,
            "mode": state["config"].mode,
            "timestamp": datetime.now().isoformat(),
            "base_url": state["config"].base_url,
            "spec_url": state["config"].spec_url,
            "iterations": state["iteration"],
            "token_usage": state["token_usage"],
            "termination_reason": state.get("termination_reason"),
            
            
        },
        "summary":{
            "test_cases_generated": len(state["test_cases"]),
            "tests_executed": len(state["results"]),
            "bugs_detected": len(bugs_detected),
            "false_positives": len([e for e in state["evaluations"] if not e.bug_detected and not e.passed]),
            "endpoints_covered": len({r.test_case.endpoint for r in state["results"]}),
            
        },
        "test_cases": [tc.model_dump() for tc in state["test_cases"]],
        "results": [
            {
                "test_id": r.test_case.id,
                "endpoint": r.test_case.endpoint,
                "method": r.test_case.method,
                "status_received": r.status_received,
                "status_expected": r.test_case.expected_status,
                "passed": r.passed,
                "error": r.error,
                
            }
            for r in state["results"]
        ],
        "evaluations":[
            {
                "test_id": e.test_case.id,
                "endpoint":e.test_case.endpoint,
                "bug_detected": e.bug_detected,
                "verdict": e.verdict,
                "resoning": e.reasoning,
            }
            for e in state["evaluations"]
        ],
        "bugs": [
            {
                "test_id": e.test_case.id,
                "endpoint":e.test_case.endpoint,
                "method": e.test_case.method,
                "verdict": e.verdict,
                "resoning": e.reasoning,
            }
            for e in bugs_detected
        ],
    }
    results_dir = Path("results") / "agent"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename= results_dir / f"agent{target}_{timestamp}.json"
    
    with open(filename, "w") as f:
        json.dump(output, f, indent=2)
    print(f"Results saved to {filename}")
    return output
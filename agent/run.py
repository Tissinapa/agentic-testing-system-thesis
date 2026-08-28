import asyncio
import argparse
from dotenv import load_dotenv
from agent.models import AgentConfig, AgentState
from agent.graph import build_graph
from agent.results import export_results

load_dotenv()

def parse_args():
    parser = argparse.ArgumentParser(description="AI testing agent")
    parser.add_argument(
        "--target",
        choices=["java","python"],
        required=True,
        help="Target application language"
    )
    parser.add_argument(
        "--base-url",
        required=True,
        help="Base URL of the target application"    
    )
    parser.add_argument(
        "--spec-url",
        required=True,
        help="OpenAPI spec url"
    )
    parser.add_argument(
        "--mode",
        choices=["black", "white"],
        default="black",
        help="Testinmg mode: black-box or white-box (default: black)"
            
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=3,
        help="Maximum amount of agent loop iterations (default: 3)"
    )
    parser.add_argument(
        "--token-budget",
        type=int,
        default=10000,
        help="Maximum token budget (default: 10000)"
    )
    parser.add_argument(
        "--requirements",
        type=str,
        default=None,
        help="Path to requirements file"
            
    )
    parser.add_argument(
        "--source-code",
        type=str,
        default=None,
        help="Path to source code file for white-box mode"            
    )

    
    return parser.parse_args()

def load_file(path: str) -> str | None:
    if path is None:
        return None
    try:
        with open(path, "r") as f:
            return f.read()
    except FileNotFoundError:
        print(f"File not found: {path}")
        return None
    
async def run(args):
    requirements = load_file(args.requirements)
    source_code = load_file(args.source_code)
    #print(f"DEBUG: requirements loaded = '{str(requirements)[:100]}'")
    config = AgentConfig(
        base_url = args.base_url,
        spec_url= args.spec_url,
        target= args.target,
        mode= args.mode,
        max_iterations= args.max_iterations,
        token_budget= args.token_budget,
        requirements=args.requirements
    )
    initial_state: AgentState={
        "config": config,
        "spec": {},
        "test_cases": [],
        "results": [],
        "evaluations": [],
        "iteration":0,
        "new_cases_this_iteration": 0,
        "token_usage": 0,
        "termination_reason": None,
        "requirements": requirements,
        "source_code": source_code
    }
    
    print(f"Starting agent -> target: {args.target}, mode: {args.mode}")
    print(f"Base URL: {args.base_url}")
    print(f"Max iterations: {args.max_iterations}, token budget: {args.token_budget}")
    print("-"*50)
    
    graph = build_graph()
    final_state = await graph.ainvoke(initial_state)
    
    print("-"*50)
    print(f"Agent finished after {final_state['iteration']} iteration")
    print(f"Tokens used: {final_state['token_usage']}")
    print(f"Test cases generated: {len(final_state['test_cases'])}")
    print(f"Bugs detected: {len([ e for e in final_state['evaluations'] if e.bug_detected])}")
    
    output = export_results(final_state, args.target)
    return output

def main():
    args = parse_args()
    asyncio.run(run(args))
    
if __name__=="__main__":
    main()
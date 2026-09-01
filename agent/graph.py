from langgraph.graph import StateGraph, END
from agent.models import AgentState
from agent.nodes.parser import parser_node
from agent.nodes.generator import generator_node
from agent.nodes.reflection import reflection_node
from agent.nodes.executor import executor_node
from agent.nodes.evaluator import evaluator_node
from agent.nodes.termination_logic import termination_logic_node
from agent.nodes.white_box_analyzer import white_box_analyzer_node


########## Nodes run order#############
# BLACK
# parser -> generator -> executor -> evaluator -> reflection -> increment -> done

# WHITE
# parser -> white-box -> increment -> done

# HYPRID
# parser -> generator -> executor -> evaluator -> reflection -> white-box ->  increment -> done
######################################

def increment_iteration(state: AgentState) -> AgentState:
    return{
        **state,
        "iteration": state["iteration"] +1 ,
    }
    
def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)
    config_mode = None
    # all agent nodes
    graph.add_node("parser",parser_node)
    graph.add_node("generator",generator_node)
    graph.add_node("executor",executor_node)
    graph.add_node("evaluator",evaluator_node)
    graph.add_node("reflection", reflection_node)
    graph.add_node("white_box", white_box_analyzer_node)
    graph.add_node("increment", increment_iteration)
    
    graph.set_entry_point("parser")
    
    graph.add_conditional_edges(
        "parser",
        lambda state: state["config"].mode,
        {
            "black": "generator",
            "white": "white_box",
            "hybrid": "generator",
        }
    )
    # Black and hybrid flow
    graph.add_edge("generator", "executor")
    graph.add_edge("executor", "evaluator")
    graph.add_edge("evaluator", "reflection")

    # Hybrid adds white-box after reflection
    graph.add_conditional_edges(
        "reflection",
        lambda state: state["config"].mode,
        {
            "black": "increment",
            "hybrid": "white_box",
            "white": "increment",  # shouldn't reach here
        }
    )

    graph.add_edge("white_box", "increment")

    graph.add_conditional_edges(
        "increment",
        termination_logic_node,
        {
            "done": END,
            "iterate": "generator",
        }
    )

    return graph.compile()
from langgraph.graph import StateGraph, END
from agent.models import AgentState
from agent.nodes.parser import parser_node
from agent.nodes.generator import generator_node
from agent.nodes.reflection import reflection_node
from agent.nodes.executor import executor_node
from agent.nodes.evaluator import evaluator_node
from agent.nodes.termination_logic import termination_logic_node


def increment_iteration(state: AgentState) -> AgentState:
    return{
        **state,
        "iteration": state["iteration"] +1 ,
    }
    
def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)
    
    # all agent nodes
    graph.add_node("parser",parser_node)
    graph.add_node("generator",generator_node)
    graph.add_node("reflection", reflection_node)
    graph.add_node("executor",executor_node)
    graph.add_node("evaluation",evaluator_node)
    graph.add_node("increment", increment_iteration)
    
    graph.set_entry_point("parser")
    
    graph.add_edge("parser","generator")
    graph.add_edge("generator","reflection")
    graph.add_edge("reflection","executor")
    graph.add_edge("executor","evaluation")
    graph.add_edge("evaluation","increment")
    
    graph.add_conditional_edges(
        "increment", termination_logic_node, {
            "done":END,
            "iterate":"generator",
        }
    )
    return graph.compile()
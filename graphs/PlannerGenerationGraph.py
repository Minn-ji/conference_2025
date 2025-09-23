from typing_extensions import TypedDict, List
from langgraph.graph import StateGraph

class PlannerGenerationState(TypedDict):
    it: str | List 
    iss: List
    a: List
    state: List
    model: ChatOpenAI | AzureChatOpenAI | str

def _node(state: PlannerGenerationState) -> dict:

    result = other_function_output()
    return {
        "iss": result,
    }

# --- 5. Build and Compile the Subgraph ---
def create_generation_subgraph(input_payload: List[str]):
    workflow = StateGraph(PlannerGenerationState)
    하위_nodes = {
    "other": _node ,
    "nodes": generated_node,
    }
    # Always present
    workflow.add_node("other", _node)
    workflow.add_node("nodes", generated_node)

    workflow.set_entry_point("other")
    workflow.set_finish_point("finalize")

    for name in input_payload:
        node_name = f"{name}_node"
        node_fn = 하위_nodes[name]
        # Add node
        workflow.add_node(node_name, node_fn)

        # Wire: instantiation → metric node
        workflow.add_edge("instantiate_evaluator", node_name)

        # Wire: metric node → finalize
        workflow.add_edge(node_name, "finalize")

    return workflow.compile()
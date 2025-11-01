from typing import List, Dict, Literal, Union, Optional
from typing_extensions import TypedDict
from langgraph.graph import END, StateGraph
import asyncio

# --- EvaluationState Type ---
class PlannerState(TypedDict):
    retrieve_metrics: Optional[List[str]]
    generate_metrics: Optional[List[str]]
    evaluation_mode: Literal["retrieval_only", "generation_only", "full"]
    retriever_evaluation_result: Optional[Dict]
    generator_evaluation_result: Optional[Dict]

# --- Router Function ---
def route_evaluations(state: PlannerState) -> Literal["retrieval_evaluator", "generation_evaluator"]:
    mode = state["evaluation_mode"]
    if "retrieval_only" in mode:
        print("→ Route to Retrieval Evaluator ONLY")
        return "retrieval_evaluator"
    elif "generation_only" in mode:
        print("→ Route to Generation Evaluator ONLY")
        return "generation_evaluator"
    elif "full" in mode:
        print("→ Route to Retrieval THEN Generation")
        return "full"
    else:
        raise ValueError(f"Invalid evaluation_mode: {mode}")



# --- Router Node Definition ---
def router(state: PlannerState) -> Dict:
    return {}  # No update needed, just branching


# --- Create Main Graph ---
def eval_quiz_graph():
    workflow = StateGraph(PlannerState)

    # Nodes
    workflow.add_node("router", router)
    # Entry point
    workflow.set_entry_point("router")
    # Routing logic
    workflow.add_conditional_edges(
        "router",
        route_evaluations,
        {
            "retrieval_evaluator": "retrieval_evaluator",
            "generation_evaluator": "generation_evaluator",
            "full": "retrieval_evaluator",
        },
    )
    workflow.add_conditional_edges(
        "retrieval_evaluator",
        route_evaluations,
        {
            "retrieval_evaluator": END,
            "full" : "generation_evaluator",
        },
    )
    # Endpoints
    workflow.add_edge("generation_evaluator", END)


    return workflow.compile()
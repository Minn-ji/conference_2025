from typing import List, Dict, Literal
from typing_extensions import TypedDict
from langgraph.graph import START, END, StateGraph
from .PlannerGenerationGraph import PlannerGenerationState, create_generation_subgraph

class PlannerState(TypedDict):
    textt | str


def route_evaluations(state: PlannerState) -> Literal["create_planner", "check_answer"]:
    mode = state["evaluation_mode"]
    if "retrieval_only" in mode:
        return "retrieval_evaluator"
    elif "generation_only" in mode:
        return "generation_evaluator"
    elif "full" in mode:
        return "full"
    else:
        raise ValueError(f"Invalid evaluation_mode: {mode}")



async def create_planner(state: PlannerState) -> Dict:
    a_subgraph = create_generation_subgraph(state["ddd"])

    input: PlannerGenerationState = {
        "query":  state["dataset"]["Retrieval"]["query"],
    }
    results = await a_subgraph.ainvoke(input)
    results = results.get('final_results')
    return {"planner_result": results}


async def check_answer(state: PlannerState) -> Dict:
    b_subgrpah = create_quiz_subGraph(state["ee"])
    input: QuizState = {
            "query":  state["dataset"]["Retrieval"]["query"],
        }
    results = await b_subgrpah.ainvoke(input)
    results = results.get('final_results')
    return {"quiz_result": results}

# --- Router Node Definition ---
def router(state: PlannerState) -> Dict:
    return {}  # No update needed, just branching



def create_main_graph():
    workflow = StateGraph(PlannerState)

    # Nodes
    workflow.add_node("router", router)
    workflow.add_node("create_planner", create_planner)
    workflow.add_node("generation_evaluator", evaluate_generation)

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
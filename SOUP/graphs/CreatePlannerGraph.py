import numpy as np
from typing import List, Dict, Union, TypedDict, Literal, Optional
from langgraph.graph import StateGraph, END
from langchain_core.documents import Document
from metrics.Retrieval import RetrievalEvaluator
from time import sleep
from langchain_openai import AzureChatOpenAI, ChatOpenAI
import logging


    
METRICS_LIST = ["mrr", "map", "f1", "ndcg", "context_relevance","precision", "recall" ]

# --- Define the State for the Graph ---
class GeneratePlannerState(TypedDict):
    # --- INPUTS ---
    query: List[str]
    predicted_documents: List[List[Document]]
    ground_truth_documents: List[List[Document]]
    metrics_to_run: List[str]
    model: AzureChatOpenAI | ChatOpenAI | str
    k: int
    # --- INTERNAL STATE ---
    evaluator: Optional[RetrievalEvaluator]

    # --- OUTPUT ---
    mrr_score: Optional[float]
    map_score: Optional[float]
    ndcg_score: Optional[float]
    context_relevance_score: Optional[float]
    
    precision_micro: Optional[float]
    precision_macro: Optional[float]
    recall_micro: Optional[float]
    recall_macro: Optional[float]
    f1_micro: Optional[float]
    f1_macro: Optional[float]

    final_results: Dict[str, float]

# --- 3. Define Separate Nodes for Each Task ---

def instantiate_evaluator_node(state: GeneratePlannerState) -> dict:

    print("\n--- (1) Instantiating Evaluator ---")
    evaluator = RetrievalEvaluator(
        query=state["query"],
        ground_truth_documents=state["ground_truth_documents"],
        predicted_documents=state["predicted_documents"],
        model=state["model"],
    )
    sleep(2)
    return {
        "evaluator": evaluator,
    }


def recall_node(state: GeneratePlannerState) -> dict:
    """Node to calculate only the Recall@5 score."""
    print("--- (2g) Running Recall Node ---")
    evaluator = state["evaluator"]
    k = state["k"]    
    recall_micro, recall_macro = evaluator.recall(k=k)
    # logging.DEBUG(f" RECALL SCORE DEBUG: {recall_micro, recall_macro}")
    sleep(2)
    return {
        "recall_micro": recall_micro,
        "recall_macro": recall_macro
    }

def finalize_node(state: GeneratePlannerState) -> dict:
    """Optionally consolidate all scores into final_results."""
    print("--- (3) Finalizing Results ---")
    final_scores = {
        "recall_micro": state.get("recall_micro"),
        "recall_macro": state.get("recall_macro"),
    }
    # Remove any None entries
    final_scores = {k: v for k, v in final_scores.items() if v is not None}
    sleep(2)
    return {"final_results": final_scores}


def parallelize_metrics(state: GeneratePlannerState) -> str:
    
    metric = state["metrics_to_run"]
        
    if not state["metrics_to_run"]:
        print("→ All metrics computed. Go to finalize.")
        return "finalize"
    
    if metric not in METRICS_LIST:
        print("No evaluation metric selected\n Choose from the following metrics list \n{METRICS_LIST}")
    sleep(2)
    return metric


# --- 5. Build and Compile the graph ---
def create_planner_graph():
    workflow = StateGraph(GeneratePlannerState)
    METRIC_NODES = {
    "recall": recall_node
    }
    # Always present
    workflow.add_node("instantiate_evaluator", instantiate_evaluator_node)
    workflow.add_node("finalize", finalize_node)

    workflow.set_entry_point("instantiate_evaluator")
    workflow.set_finish_point("finalize")

    for metric in metrics_to_run:
        if metric not in METRIC_NODES:
            raise ValueError(f"Unknown metric '{metric}'. Must be one of {list(METRIC_NODES.keys())}")

        node_name = f"{metric}_node"
        node_fn = METRIC_NODES[metric]
        # Add node
        workflow.add_node(node_name, node_fn)

        # Wire: instantiation → metric node
        workflow.add_edge("instantiate_evaluator", node_name)

        # Wire: metric node → finalize
        workflow.add_edge(node_name, "finalize")

    return workflow.compile()










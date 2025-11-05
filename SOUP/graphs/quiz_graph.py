from typing import List, Dict, Literal, Union, Optional
from typing_extensions import TypedDict
from langgraph.graph import END, StateGraph
import asyncio
from graphs.states import PlannerState

# --- Router Node Definition ---
def router(state: PlannerState) -> Dict:
    return {}  # No update needed, just branching


# --- Create Main Graph ---
def generate_quiz_graph():
    pass
from fastapi import FastAPI
from RAG_Evaluation.api.v1.endpoints.evaluate_quiz import evaluator
from SOUP.api.v1.routers import api_router
from graphs.main_graph import create_main_graph, EvaluationState

app = FastAPI(
    title="SOUP API",
    description="An API to create Planner or evaluate Quizes built with LangGraph.",
)
app.include_router(api_router, prefix="/v1")


# --- API Endpoints ---

@app.get("/")
def read_root():
    return {"status": "ok"}


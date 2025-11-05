from fastapi import FastAPI
from api.v1.routers import api_router
import time
import uvicorn

app = FastAPI(
    title="SOUP API",
    description="An API to create Planner or evaluate Quizes built with LangGraph.",
)
app.include_router(api_router, prefix="/v1")


# --- API Endpoints ---

@app.get("/")
def read_root():
    time.sleep(30)
    return {"comment": "Hello, It's SOUP API!", "status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
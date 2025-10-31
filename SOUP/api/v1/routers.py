from fastapi import APIRouter
from api.v1.endpoints import planner, quiz

api_router = APIRouter()

api_router.include_router(planner.router, prefix="/planner", tags=["planner"])
api_router.include_router(quiz.router, prefix="/quiz", tags=["quiz"])
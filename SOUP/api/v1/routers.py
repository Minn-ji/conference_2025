from fastapi import APIRouter
from api.v1.endpoints import planner, quiz, ocr, grade, grade_original

api_router = APIRouter()

#api_router.include_router(planner.router, prefix="/planner", tags=["planner"])
#api_router.include_router(quiz.router, prefix="/quiz", tags=["quiz"])
api_router.include_router(ocr.router, prefix="/ocr", tags=["ocr"])  
api_router.include_router(grade.router, prefix="/grade", tags=["grade"])
#api_router.include_router(grade_original.router, prefix="/grade", tags=["grade"])
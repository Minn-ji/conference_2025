from typing import List
from schema import GetPlannerRequest
import json
from graphs import create_planner_graph
from fastapi import APIRouter
from core import get_user_info, get_recent_quiz_info, get_recent_planner
# import asyncio


router = APIRouter()

@router.post("/get-planner", status_code=202)
async def evaluator(request: GetPlannerRequest):
    ''' create new planner'''
    student_id = int(request.student_id)
    user_info = get_user_info(student_id)
    quiz_info = get_recent_quiz_info(student_id)
    planner = get_recent_planner(student_id, request.date)

    payload = {
        "grade": user_info["grade"],
        "recent_score": float(user_info.get("study_hours", 0)),  # 예: 최근 점수를 학습시간으로 임시대체
        "initial_level": 1,  # soup 등급을 숫자로 매핑해도 됨
        "recent_quiz_info": quiz_info,
        "recent_planner": planner
    }

    # return {
    #     "student_id": request.student_id,
    #     "date": request.date,
    #     "payload": payload
    # }
    graph_input = create_planner_input_payload(request)
    main_graph = create_planner_graph()
    response = await main_graph.ainvoke(input=graph_input)
    planner = response.get("planner")
    
    return planner


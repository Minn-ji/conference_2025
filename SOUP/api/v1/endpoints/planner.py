from typing import List
from fastapi import APIRouter
# import asyncio
from schema import GeneratePlannerRequest, create_planner_input_payload
from graphs import generate_planner_graph

router = APIRouter()

# http://127.0.0.1:8000/planner/generate
@router.post("/generate", status_code=200)
async def evaluator(request: GeneratePlannerRequest):
    ''' generate new planner'''
    print("generate new planner")
    graph_input = create_planner_input_payload(student_id=request.student_id, date=request.date)
    graph = generate_planner_graph()
    print(graph_input)
    response = await graph.ainvoke(input=graph_input)
    planner = response.get("generated_planner")
    
    return {"planner": planner}


import json
from fastapi import APIRouter, HTTPException

from graphs import create_eval_quiz_graph
from schema import GenerateQuizRequest, EvaluateQuizRequest, create_eval_quiz_input_payload

router = APIRouter()
# http://127.0.0.1:8000/quiz/generate
@router.post("/generate")
async def get_quiz(request: GenerateQuizRequest):
    '''create new quiz for daily planner'''
    today_planner = request.today_planner
    achieve_rate = 0
    for row in today_planner:
        achieve_rate += row["achieve"]
    achieve_rate = achieve_rate / len(today_planner)
    if achieve_rate < 20:
        return {"result": "No quiz"}
    return {"status": "OK"}


# http://127.0.0.1:8000/quiz/evaluate
@router.post("/evaluate", status_code=202)
async def evaluator(request: EvaluateQuizRequest):
    ''' evaluate quiz with llm'''
    quizs = request.quizzes
    graph_input = create_eval_quiz_input_payload(quizs)
    main_graph = create_eval_quiz_graph()
    response = await main_graph.ainvoke(input=graph_input)
    evaluate_result = response.get("result")

    return evaluate_result
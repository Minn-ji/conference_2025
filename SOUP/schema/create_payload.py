import inspect
import sys
import os
from typing import Dict, List, Any, Union
from fastapi import HTTPException
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER") # root

DB_NAME = os.getenv("DB_NAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT")

DB_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DB_URL, pool_pre_ping=True)


# def create_planner_input_payload(request: dict) -> dict:
def get_user_info(student_id: int) -> Dict[str, Any]:
    """users 테이블에서 학년, 레벨, 학습시간 등 가져오기"""
    query = text("""
        SELECT grade, study_hours, soup
        FROM users
        WHERE user_id = :uid
    """)
    with engine.connect() as conn:
        res = conn.execute(query, {"uid": student_id}).fetchone()
    if not res:
        raise HTTPException(status_code=404, detail=f"User {student_id} not found.")
    return dict(res._mapping)


def get_recent_quiz_info(student_id: int) -> List[Dict[str, Any]]:
    """question_sets + question_set_items에서 최근 퀴즈 데이터 구성"""
    query = text("""
        SELECT qs.question_set_id, qsi.question_id, qsi.is_correct, qsi.user_answer, qsi.descriptive_file_url
        FROM question_sets qs
        JOIN question_set_items qsi ON qs.question_set_id = qsi.question_set_id
        WHERE qs.user_id = :uid
        ORDER BY qs.finished_at DESC
        LIMIT 1
    """)
    with engine.connect() as conn:
        rows = conn.execute(query, {"uid": student_id}).fetchall()

    if not rows:
        return []

    quiz_id = rows[0]._mapping["question_set_id"]
    quiz_items = [
        {
            "question_num": i + 1,
            "question_type": "이해",  # TODO: questions 테이블에 해당 정보 없음
            "essay_type_score": {"score": 0.0, "text": ""}, # # TODO: questions 테이블에 해당 정보 없음
            "difficulty_level": 3, #TODO: questions 테이블에 해당 정보 없음
            "is_correct": bool(r._mapping["is_correct"]),
            "timeout": False #TODO: questions 테이블에 해당 정보 없음
        }
        for i, r in enumerate(rows)
    ]

    return [{
        "quiz_id": str(quiz_id),
        "quizes": quiz_items,
        "total_score": sum([1 for q in quiz_items if q["is_correct"]]) * 10
    }]

def get_korean_day(weekday_idx: int) -> str:
    days = ["월", "화", "수", "목", "금", "토", "일"]
    return days[weekday_idx % 7]

def get_recent_planner(student_id: int) -> Union[List, Dict[str, Any]]:
    """planners + planner_items에서 가장 최근 플래너 최대 3개 조회"""
    query = text("""
        SELECT p.planner_id, p.date, pi.content, pi.duration
        FROM planners p
        JOIN planner_items pi ON p.planner_id = pi.planner_id
        WHERE p.user_id = :uid
        ORDER BY p.date DESC
        LIMIT 3
    """)
    with engine.connect() as conn:
        rows = conn.execute(query, {"uid": student_id}).fetchall()

    if not rows:
        return []  # 명시적으로 '없음' 신호

    first = rows[0]._mapping
    contents = [{"text": r._mapping["content"], "time": r._mapping["duration"] or 0} for r in rows]

    return {
        "meta": {
            "date": str(first["date"].date()),
            "day_of_week": get_korean_day(first["date"].weekday()),
            "planned_time_min": sum(c["time"] for c in contents)
        },
        "content": contents,
        "content_total_min": sum(c["time"] for c in contents)
    }



# def create_eval_quiz_input_payload(request):
#     all_quizzes = request.quizzes
#     for quiz in all_quizzes:
#         question = quiz["question"]
#         answer = quiz["answer"]
#         user_answer = quiz["user_answer"]
        

#         quiz_payload = {
#             "question": ["query"],
#             "answer": ["predicted_documents"],
#             "user_answer": cleanseddata["ground_truth_documents"], # List[List of text]
#             "ans_by_level": "",

#         }
#     final_payload = {
#         "retrieve_metrics": config["retrieve_metrics"],
#         "dataset": {
#             "Retrieval": retrieval_dataset,
#         },
#             "evaluation_mode": config["evaluation_mode"],
#     }

#     return final_payload

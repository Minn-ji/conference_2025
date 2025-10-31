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

DB_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DB_URL, pool_pre_ping=True)


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


def get_recent_quiz_info(student_id: int) -> Dict[str, Any]:
    # 최근 quiz_id 조회
    quiz_id_query = text("""
        SELECT question_set_id
        FROM question_sets
        WHERE user_id = :uid
        ORDER BY finished_at DESC
        LIMIT 1
    """)

    with engine.connect() as conn:
        result = conn.execute(quiz_id_query, {"uid": student_id}).fetchone()

        if not result:
            # 최근 퀴즈 본 거 없음
            return {}

        quiz_id = result._mapping["question_set_id"]

        item_query = text("""
            SELECT is_correct, difficulty_level, essay_type_score, timeout, is_correnct
            FROM question_set_items
            WHERE question_set_id = :qid
            ORDER BY question_set_item_id
        """)

        items = conn.execute(item_query, {"qid": quiz_id}).fetchall()

    quiz_items = [
        {
            "question_num": idx + 1,
            "essay_type_score": r._mapping["essay_type_score"],
            "difficulty_level": r._mapping["difficulty_level"], 
            "is_correct": bool(r._mapping["is_correct"]),
            "timeout": bool(r._mapping["timeout"]), 
        }
        for idx, r in enumerate(items)
    ]

    return {
        "quiz_id": str(quiz_id),
        "quizes": quiz_items,
        "total_score": sum(1 for q in quiz_items if q["is_correct"]) * 10
    }

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
        return ["없음"] 

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
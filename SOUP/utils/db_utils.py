import os
from typing import Dict, List, Any, Union
from fastapi import HTTPException
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()
DB_URL = os.getenv("DB_URL")
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

    # previous_quiz_score: Optional[int]        # 이전 퀴즈 점수
    # score_trend: Optional[str]                # "상승/하락/유지" 등
    # accuracy_by_unit: Optional[Dict[str, float]]      # 단원별 정답률
    # accuracy_by_topic: Optional[Dict[str, float]]     # 유형별 정답률
    # accuracy_by_difficulty: Optional[Dict[str, float]]# 난이도별 정답률
    # time_efficiency: Literal["상승",

def _compute_accuracy_by(items, key):
    counts = defaultdict(lambda: {"correct": 0, "total": 0})
    for r in items:
        k = r[key]
        counts[k]["total"] += 1
        if r["is_correct"]:
            counts[k]["correct"] += 1

    return {
        k: v["correct"] / v["total"]
        for k, v in counts.items()
        if v["total"] > 0
    }

def get_recent_quiz_info(student_id: int) -> Dict[str, Any]:
    # 최근 quiz_id 조회
    quiz_id_query = text("""
        SELECT question_set_id
        FROM question_sets
        WHERE user_id = :uid
        ORDER BY finished_at DESC
        LIMIT 2
    """)

    with engine.connect() as conn:
        quiz_rows = conn.execute(quiz_id_query, {"uid": student_id}).fetchall()

        if not quiz_rows:
            # 최근 퀴즈 본 거 없음
            return {}

        quiz_id = quiz_rows[0]._mapping["question_set_id"]
        prev_quiz_id = quiz_rows[1]._mapping["question_set_id"] if len(quiz_rows) > 1 else None

        item_query = text("""
            SELECT 
                qsi.is_correct,
                qsi.timeout,
                qsi.essay_type_score,
                q.difficulty_level,
                q.subject_unit_id,
                q.question_type
            FROM question_set_items qsi
            JOIN questions q ON qsi.question_id = q.question_id
            WHERE qsi.question_set_id = :qid
        """)
        rows = conn.execute(item_query, {"qid": quiz_id}).fetchall()
        if prev_quiz_id: #이전 퀴즈
            prev_rows = conn.execute(item_query, {"qid": prev_quiz_id}).fetchall()
        else:
            prev_rows = []

    quiz_items = [
        {
            "question_num": idx + 1,
            "essay_type_score": r._mapping["essay_type_score"],
            "difficulty_level": r._mapping["difficulty_level"], 
            "is_correct": bool(r._mapping["is_correct"]),
            "timeout": bool(r._mapping["timeout"]), 
        }
        for idx, r in enumerate(rows)
    ]

    total_score = sum(1 for q in quiz_items if q["is_correct"]) * 10
    prev_score = (
        sum(1 for r in prev_rows if r._mapping["is_correct"]) * 10
        if prev_rows else None
    )
    if prev_score is None:
        score_trend = None
    elif total_score > prev_score:
        score_trend = "상승"
    elif total_score < prev_score:
        score_trend = "하락"
    else:
        score_trend = "유지"

    accuracy_by_unit = _compute_accuracy_by(
        [{**r._mapping, "is_correct": bool(r._mapping["is_correct"])} for r in rows],
        "subject_unit_id"
    )
    accuracy_by_topic = _compute_accuracy_by(
        [{**r._mapping, "is_correct": bool(r._mapping["is_correct"])} for r in rows],
        "topic"
    )
    accuracy_by_difficulty = _compute_accuracy_by(
        [{**r._mapping, "is_correct": bool(r._mapping["is_correct"])} for r in rows],
        "difficulty_level"
    )
    timeout_rate = sum(1 for q in quiz_items if q["timeout"]) / len(quiz_items)
    if prev_rows:
        prev_timeout_rate = sum(1 for r in prev_rows if r._mapping["timeout"]) / len(prev_rows)
        if timeout_rate < prev_timeout_rate:
            time_efficiency = "상승"
        elif timeout_rate > prev_timeout_rate:
            time_efficiency = "하락"
        else:
            time_efficiency = "유지"
    else:
        time_efficiency = None

    return {
        "quiz_id": str(quiz_id),
        "quizes": quiz_items,
        "total_score": sum(1 for q in quiz_items if q["is_correct"]) * 10,
        "previous_quiz_score": prev_score,
        "score_trend": score_trend,  # 상승/하락/유지
        "accuracy_by_unit": accuracy_by_unit,
        "accuracy_by_topic": accuracy_by_topic,
        "accuracy_by_difficulty": accuracy_by_difficulty,
        "time_efficiency": time_efficiency, # 상승/하락/유지
    }


def _get_korean_day(weekday_idx: int) -> str:
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
            "day_of_week": _get_korean_day(first["date"].weekday()),
            "planned_time_min": sum(c["time"] for c in contents)
        },
        "content": contents,
        "content_total_min": sum(c["time"] for c in contents)
    }
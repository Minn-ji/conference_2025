from typing import Dict, Optional
# from graphs.states import RecentQuizInfo
#: Optional[RecentQuizInfo]

'''
    "recent_quiz_info": {
        "quiz_id": "12",
        "quizes": [
            {"question_num": 1, "topic": "이해", essay_type_score": None, "difficulty_level": "2", "is_correct": True, "timeout": False},
            {"question_num": 2, "topic": "추론", "essay_type_score": None, "difficulty_level": "3", "is_correct": False, "timeout": False},
        ],
        "total_score": 60
    },
    '''
def get_avg_quiz_score(q) -> Optional[float]:
    if not q or not q.get("quizes"):
        return None
    return float(q.get("total_score")) if q.get("total_score") is not None else None

def extract_accuracy_by_topic(q) -> Optional[Dict[str, float]]:
    """
    recent_quiz_info["quizes"] 내 topic 필드를 기준으로 정답률 계산
    topic 별 correct / total
    """
    if not q or "quizes" not in q:
        return None

    topics = {}
    for row in q["quizes"]:
        topic = row.get("topic")
        is_correct = row.get("is_correct")

        if topic is None:
            continue

        if topic not in topics:
            topics[topic] = {"correct": 0, "total": 0}

        topics[topic]["total"] += 1
        if is_correct:
            topics[topic]["correct"] += 1

    # 정답률 계산
    result = {}
    for topic, stats in topics.items():
        if stats["total"] > 0:
            result[topic] = stats["correct"] / stats["total"]

    return result if result else None
def extract_accuracy_by_difficulty(q) -> Optional[Dict[str, float]]:
    """
    recent_quiz_info["quizes"] 기반으로 난이도별 정답률 계산
    difficulty_level 기준으로 correct / total
    """
    if not q or "quizes" not in q:
        return None

    difficulties = {}
    for row in q["quizes"]:
        level = row.get("difficulty_level")
        is_correct = row.get("is_correct")

        if level is None:
            continue

        if level not in difficulties:
            difficulties[level] = {"correct": 0, "total": 0}

        difficulties[level]["total"] += 1
        if is_correct:
            difficulties[level]["correct"] += 1

    # 정답률 계산
    result = {}
    for level, stats in difficulties.items():
        if stats["total"] > 0:
            result[level] = stats["correct"] / stats["total"]

    return result if result else None
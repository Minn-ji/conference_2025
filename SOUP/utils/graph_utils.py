from typing import Dict, Optional
# from graphs.states import RecentQuizInfo
#: Optional[RecentQuizInfo]
def get_avg_quiz_score(q) -> Optional[float]:
    if not q or not q.get("quizes"):
        return None
    # total_score는 10점 단위라고 했으니 quizes 기반 평균 점수 가정 필요시 조정
    # 여기서는 최근 퀴즈 1회 총점만 있으면 그대로 사용, 없으면 None
    return float(q.get("total_score")) if q.get("total_score") is not None else None

def extract_accuracy_by_topic(q) -> Optional[Dict[str, float]]:
    # 데이터가 없다 가정: 외부에서 전처리해 넣는 게 이상적. 없으면 None.
    return None

def extract_accuracy_by_difficulty(q) -> Optional[Dict[str, float]]:
    # 데이터가 없다 가정: 외부에서 전처리해 넣는 게 이상적. 없으면 None.
    return None

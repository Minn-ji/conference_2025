from graphs.states import PlannerState
from utils import safe, ask_llm, ensure_json, get_avg_quiz_score, extract_accuracy_by_topic, extract_accuracy_by_difficulty
from .prompts import student_check_prompt


def node_generate_quiz(state: PlannerState) -> PlannerState:
    """학생 레벨 테스트 생성"""
    # 학생이 선택한 대단원 정보 입력되고
    # 
    avg_score = get_avg_quiz_score(state.get("recent_quiz_info"))
    prompt = student_check_prompt.format(
        grade=safe(state.get("grade")),
        recent_score=safe(state.get("recent_score")),
        initial_level=safe(state.get("initial_level")),
        avg_score="없음" if avg_score is None else avg_score,
        accuracy_by_topic=safe(extract_accuracy_by_topic(state.get("recent_quiz_info"))),
        accuracy_by_difficulty=safe(extract_accuracy_by_difficulty(state.get("recent_quiz_info")))
    )
    out = ask_llm(prompt)
    out = ensure_json(out)
    print("quizzes", out)
    return {**state, "student_check_result": out}
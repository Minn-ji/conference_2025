from graphs.state import PlannerState
from utils import safe, ask_llm
from .prompts import recent_quiz_analyze_prompt


def node_recent_quiz_analyze(state: PlannerState) -> PlannerState:
    """최근 퀴즈 분석 텍스트 생성."""
    # 아래 값들은 외부에서 전처리해 state에 넣어두는 것을 권장
    prompt = recent_quiz_analyze_prompt.format(
        quiz_score=safe(state.get("recent_quiz_info", {}).get("total_score")),
        previous_quiz_score=safe(state.get("previous_quiz_score")),  # 있으면 사용
        score_trend=safe(state.get("score_trend")),                  # "상승/하락/유지" 등
        accuracy_by_unit=safe(state.get("accuracy_by_unit")),        # dict 기대
        accuracy_by_topic=safe(state.get("accuracy_by_topic")),      # dict 기대
        accuracy_by_difficulty=safe(state.get("accuracy_by_difficulty")),  # dict 기대
        time_efficiency=safe(state.get("time_efficiency"))           # 문자열
    )
    out = ask_llm(prompt)
    return {**state, "recent_quiz_analyze_result": out}
from graphs.states import PlannerState
from utils import safe, ask_llm
from .prompts import recent_quiz_analyze_prompt


def node_recent_quiz_analyze(state: PlannerState) -> PlannerState:
    """최근 퀴즈 분석 텍스트 생성."""


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
    print("Recent Quiz Analyze Result:", out)
    branch_flag = state.get("branch_flag")
    if branch_flag == "all":
        return {**state, "recent_quiz_analyze_result": out, "branch_flag": "recent_planner"}
    else:
        return {**state, "recent_quiz_analyze_result": out, "branch_flag": "generate_planner"}
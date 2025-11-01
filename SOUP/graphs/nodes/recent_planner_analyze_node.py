from graphs.state import PlannerState
from utils import safe, ask_llm
from .prompts import recent_planner_analyze_prompt

def node_recent_planner_analyze(state: PlannerState) -> PlannerState:
    """직전 플래너 분석 텍스트 생성."""
    rp = state.get("recent_planner")
    planned = rp["meta"]["planned_time_min"] if (rp and rp.get("meta")) else None
    # 실제 학습 시간은 별도 수집값이 없으므로 없으면 planned로 대체(0으로 두기보다 안전)
    actual = state.get("actual_time_min") if state.get("actual_time_min") is not None else planned
    plan_completion_rate = state.get("plan_completion_rate")  # 외부 계산값 권장

    prompt = recent_planner_analyze_prompt.format(
        plan_completion_rate=safe(plan_completion_rate),
        planned_time_min=safe(planned),
        actual_time_min=safe(actual),
        quiz_score=safe(state.get("recent_quiz_info", {}).get("total_score")),
        recent_quiz_analyze_result=safe(state.get("recent_quiz_analyze_result"))
    )
    out = ask_llm(prompt)
    return {**state, "recent_planner_analyze_result": out}

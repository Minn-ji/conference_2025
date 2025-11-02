from graphs.states import PlannerState
from utils import safe, ask_llm
from .prompts import recent_planner_analyze_prompt

# [입력]
# - 학년: {grade}  
# - 최근 학기 성적: {recent_grade}  
# - 하루 공부 가능 시간(분): {available_time_min}  
# - 학습 수준: {learning_level}
# - 현재 학습 중인 단원: {current_unit}  
# - 현재 학습 중인 단원 주변 단원들: {related_units}   # 예: ["소인수분해-(2)", "소인수분해-(3)", "최대공약수-(1)"]
# - 이전 플래너 달성 상태: {recent_planner_analyze_result}  
    # return {
    #     "grade": user_info["grade"],
    #     "available_time_min": user_info["study_hours"],
    #     "initial_level": user_info["soup"],
    #     "recent_quiz_info": quiz_info,
    #     "recent_planner": planner
    # }


    # class PlannerState(TypedDict):
    # grade: Optional[int | str]   # 1,2,3 or "1","2","3"
    # available_time_min: Optional[int]     # 하루 공부 가능 시간(분)
    # initial_level: Optional[Literal["A","B","C","D","E","F"]] # SOUP level
    # recent_quiz_info: Optional[RecentQuizInfo]
    # recent_planner: Optional[RecentPlanner]
    # recent_score: Optional[str]           # 최근 학기 성적(등급/점수 등 문자열)
    # current_unit: Optional[str]           # 현재 학습 중인 단원
    # related_units: Optional[List[str]]    # 주변 단원들

    # # 노드 결과가 누적될 필드
    # student_check_result: Optional[str]
    # recent_quiz_analyze_result: Optional[str]
    # recent_planner_analyze_result: Optional[str]
    # generated_planner: Optional[Dict[str, Any]]  # 생성된 플래너(JSON dict)

    # # 그래프 routing용 필드
    # has_quiz: bool 
    # has_planner: bool
    # branch_flag: Optional[Literal["recent_quiz", "recent_planner", "all", "generate_planner"]]

def node_recent_planner_analyze(state: PlannerState) -> PlannerState:
    """직전 플래너 분석 텍스트 생성."""
    rp = state.get("recent_planner")
    planned = rp["meta"]["planned_time_min"] if (rp and rp.get("meta")) else None
    # 실제 학습 시간은 별도 수집값이 없으므로 없으면 planned로 대체(0으로 두기보다 안전)
    actual = [plan["time"] for plan in rp["content"]] if (rp and rp.get("content")) else []
    actual = sum(actual) if actual else None
    plan_completion_rate = [plan["checked"] for plan in rp["content"]] if (rp and rp.get("content")) else []
    plan_completion_rate = (sum(plan_completion_rate)/len(plan_completion_rate))*100 if plan_completion_rate else None

    prompt = recent_planner_analyze_prompt.format(
        plan_completion_rate=safe(plan_completion_rate),
        planned_time_min=safe(planned),
        actual_time_min=safe(actual),
        quiz_score=safe(state.get("recent_quiz_info", {}).get("total_score")),
        recent_quiz_analyze_result=safe(state.get("recent_quiz_analyze_result"))
    )
    out = ask_llm(prompt)
    print("Recent Planner Analyze Result:", out)
    return {**state, "recent_planner_analyze_result": out}

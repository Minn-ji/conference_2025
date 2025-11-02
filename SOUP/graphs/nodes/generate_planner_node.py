import datetime
from graphs.states import PlannerState
from utils import safe, ask_llm, ensure_json
from .prompts import generate_planner_prompt


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

def node_generate_planner(state: PlannerState) -> PlannerState:
    """다음 학습 플래너 JSON 생성 + 검증 보정."""
    today = datetime.date.today()
    weekday = ["월","화","수","목","금","토","일"][today.weekday()]

    prompt = generate_planner_prompt.format(
        grade=safe(state.get("grade")),
        recent_score=safe(state.get("recent_score")),
        available_time_min=safe(state.get("available_time_min")),
        learning_level=safe(state.get("initial_level")),
        current_unit=safe(state.get("current_unit")),
        related_units=safe(state.get("related_units")),
        recent_planner_analyze_result=safe(state.get("recent_planner_analyze_result",""))
    ) + f"""
        # 추가 제약(시스템 보정):
        - meta.date는 "{today.strftime('%Y-%m-%d')}"로 설정하라.
        - meta.day_of_week는 "{weekday}"로 설정하라.
        - content_total_min은 반드시 {state.get('available_time_min')}과 정확히 일치해야 한다.
        """

    raw = ask_llm(prompt)
    try:
        plan = ensure_json(raw)
    except Exception:
        # JSON 파싱 실패 시, 최소 안전 기본값 반환
        plan = {
            "meta": {
                "date": today.strftime("%Y-%m-%d"),
                "day_of_week": weekday,
                "planned_time_min": state.get("available_time_min") or 0
            },
            "content": [],
            "content_total_min": state.get("available_time_min") or 0
        }

    # 시간 합 일치 보정
    target = int(state.get("available_time_min") or 0)
    if isinstance(plan, dict):
        # meta 보정
        plan.setdefault("meta", {})
        plan["meta"]["date"] = today.strftime("%Y-%m-%d")
        plan["meta"]["day_of_week"] = weekday
        plan["meta"]["planned_time_min"] = target

        # content 보정
        content = plan.get("content") or []
        # time이 숫자 아닌 항목 제거/0치환
        cleaned = []
        for c in content:
            if not isinstance(c, dict):
                continue
            t = c.get("time", 0)
            try:
                t = float(t)
            except Exception:
                t = 0.0
            cleaned.append({"text": str(c.get("text", ""))[:200], "time": t})
        plan["content"] = cleaned

        # 합계 조정
        s = int(round(sum(x.get("time", 0) for x in cleaned)))
        if s != target:
            diff = target - s
            if not cleaned:
                # 내용이 비어있으면 placeholder 하나 생성
                plan["content"] = [{"text": "핵심 개념 복습 및 유형 문제 풀이", "time": target}]
            else:
                # 마지막 항목에 보정치 더한다(음수면 깎음, 최소 0)
                last = plan["content"][-1]
                new_time = max(0, int(round(last["time"])) + diff)
                last["time"] = new_time

        # 최종 합계 재설정
        plan["content_total_min"] = int(round(sum(x["time"] for x in plan["content"])))
    print("Generated Planner:", plan)
    return {**state, "generated_planner": plan}

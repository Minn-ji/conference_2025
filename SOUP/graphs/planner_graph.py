from langgraph.graph import START, END, StateGraph
from graphs.states.planner_state import PlannerState
from graphs.nodes import (
    node_student_check,
    node_recent_quiz_analyze,
    node_recent_planner_analyze,
    node_generate_planner,
    node_data_check
)

def node_branch(state: PlannerState):
    has_quiz = bool(state["has_quiz"])
    has_planner = bool(state["has_planner"])

    if has_quiz and not has_planner:
        state["branch_flag"] = "recent_quiz"
        return "recent_quiz"   # 이름을 analyze로 하지 말고 라우팅 이름로 통일

    if has_planner and not has_quiz:
        state["branch_flag"] = "recent_planner"
        return "recent_planner"

    if has_quiz and has_planner:
        state["branch_flag"] = "all"
        return "all"

    # fallback 필요 (둘 다 없음)
    state["branch_flag"] = "no_history"
    return "no_history"


def branch_condition(state):
    if state['branch_flag'] == "recent_planner":
        return "recent_planner"
    
    elif state['branch_flag'] == "generate_planner":
        return "generate_planner"


def generate_planner_graph():
    graph = StateGraph(PlannerState)

    graph.add_node("data_check", node_data_check)
    graph.add_node("student_check", node_student_check)
    # graph.add_node("branch", node_branch)
    graph.add_node("recent_quiz_analyze", node_recent_quiz_analyze)
    graph.add_node("recent_planner_analyze", node_recent_planner_analyze)
    graph.add_node("generate_planner", node_generate_planner)

    # Flow
    graph.add_edge(START, "data_check")
    graph.add_edge("data_check", "student_check")
    # graph.add_edge("student_check", "branch")
    # Routing logic
    graph.add_conditional_edges(
        "student_check",
        node_branch,   # 조건 함수
        {
            "recent_quiz": "recent_quiz_analyze",
            "recent_planner": "recent_planner_analyze",
            "all": "recent_quiz_analyze",
            "no_history": "generate_planner"
        },
    )

    graph.add_conditional_edges(
        "recent_quiz_analyze",
        branch_condition,
        {
            "recent_planner": "recent_planner_analyze",
            "generate_planner": "generate_planner",
        }
    )   
    graph.add_edge("recent_planner_analyze", "generate_planner")
    graph.add_edge("generate_planner", END)

    return graph.compile()


example_state: PlannerState = {
    "grade": "1",
    "available_time_min": 90,   # 시간(시간 단위). 없으면 None 가능
    "initial_level": "B",
    "recent_score": "중상",
    "recent_quiz_info": {
        "quiz_id": "12",
        "quizes": [
            {"question_num": 1, "essay_type_score": None, "difficulty_level": "2", "is_correct": True, "timeout": False},
            {"question_num": 2, "essay_type_score": None, "difficulty_level": "3", "is_correct": False, "timeout": False},
        ],
        "total_score": 60
    },
    "recent_planner": {
        "meta": {"date": "2025-10-30", "day_of_week": "목", "planned_time_min": 90},
        "content": [{"text": "1. 소인수분해 - 소인수분해 : 복습", "time": 45}, {"text": "소인수 분해 - 소인수분해 : 유형 문제풀이", "time": 45}],
        "content_total_min": 90
    },
    # 분석/생성에 필요한 추가 입력
    "recent_grade": "B",
    "current_unit": "소인수분해 - 소인수분해",
    "related_units": ["자연수-(7) 소인수분해", "자연수-(9) 약수와 배수 응용"],
}

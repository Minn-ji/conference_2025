from langgraph.graph import START, END, StateGraph
from graphs.states.planner_state import PlannerState
from graphs.nodes.planner_nodes import (
    node_student_check,
    node_recent_quiz_analyze,
    node_recent_planner_analyze,
    node_generate_planner
)


# --- Create Main Graph ---
def generate_planner_graph():
    graph = StateGraph(PlannerState)
    graph.add_node("student_check", node_student_check)
    graph.add_node("recent_quiz_analyze", node_recent_quiz_analyze)
    graph.add_node("recent_planner_analyze", node_recent_planner_analyze)
    graph.add_node("generate_planner", node_generate_planner)

    # 순서: 학생수준 → 퀴즈분석 → 플래너분석 → 플래너생성
    graph.add_edge(START, "student_check")
    graph.add_edge("student_check", "recent_quiz_analyze")
    graph.add_edge("recent_quiz_analyze", "recent_planner_analyze")
    graph.add_edge("recent_planner_analyze", "generate_planner")
    graph.add_edge("generate_planner", END)

    return graph.compile()


example_state: PlannerState = {
    "grade": "1",
    "study_hours": 90.0/60.0,   # 시간(시간 단위). 없으면 None 가능
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
        "content": [{"text": "소인수분해 복습", "time": 45}, {"text": "유형 문제풀이", "time": 45}],
        "content_total_min": 90
    },
    # 분석/생성에 필요한 추가 입력
    "recent_grade": "B",
    "available_time_min": 90,
    "current_unit": "자연수-(8) 최대공약수와 최소공배수",
    "related_units": ["자연수-(7) 소인수분해", "자연수-(9) 약수와 배수 응용"],
}

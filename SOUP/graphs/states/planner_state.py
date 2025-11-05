from typing import List, Dict, Optional, Literal, TypedDict, Any


# Quiz item (각 문항 정보)
class QuizItem(TypedDict):
    question_num: int
    essay_type_score: Optional[float]
    difficulty_level: Optional[str]
    is_correct: bool
    timeout: bool
    # ----------

# 최근 퀴즈 정보
class RecentQuizInfo(TypedDict):
    quiz_id: str
    quizes: List[QuizItem]
    total_score: int
    previous_quiz_score: Optional[int]        # 이전 퀴즈 점수
    score_trend: Optional[str]                # "상승/하락/유지" 등
    accuracy_by_unit: Optional[Dict[str, float]]      # 단원별 정답률
    accuracy_by_topic: Optional[Dict[str, float]]     # 유형별 정답률
    accuracy_by_difficulty: Optional[Dict[str, float]]# 난이도별 정답률
    time_efficiency: Literal["상승","하락","유지"]  # 시간 효율 관련 문자열

# Planner item (각 계획 항목)
class PlannerItem(TypedDict):
    text: str
    time: float
    chechked: bool


# 최근 플래너 메타 정보
class PlannerMeta(TypedDict):
    date: str
    day_of_week: str
    planned_time_min: float


# 최근 플래너 정보
class RecentPlanner(TypedDict):
    meta: PlannerMeta
    content: List[PlannerItem]
    content_total_min: float


# 최종 PlannerState
class PlannerState(TypedDict):
    grade: Optional[int | str]   # 1,2,3 or "1","2","3"
    available_time_min: Optional[int]     # 하루 공부 가능 시간(분)
    initial_level: Optional[Literal["A","B","C","D","E","F"]] # 문제집에 따른 level
    recent_quiz_info: Optional[RecentQuizInfo]
    recent_planner: Optional[RecentPlanner]
    recent_score: Optional[str]           # 최근 학기 성적(등급/점수 등 문자열)
    current_unit: Optional[str]           # 현재 학습 중인 단원
    related_units: Optional[List[str]]    # 주변 단원들

    # 노드 결과가 누적될 필드
    student_check_result: Optional[str]
    recent_quiz_analyze_result: Optional[str]
    recent_planner_analyze_result: Optional[str]
    generated_planner: Optional[Dict[str, Any]]  # 생성된 플래너(JSON dict)

    # 그래프 routing용 필드
    has_quiz: bool 
    has_planner: bool
    branch_flag: Optional[Literal["recent_quiz", "recent_planner", "all", "generate_planner"]]
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Union


# class EssayTypeScore(BaseModel):
#     score: float = Field(..., description="서술형 점수 (0~1 사이 실수)")
#     text: str = Field(..., description="서술형 답변 요약 또는 내용")


# class QuizQuestion(BaseModel):
#     question_num: int = Field(..., description="문항 번호")
#     question_type: Literal["이해", "계산", "문제해결", "추론"] = Field(..., description="문항 유형")
#     essay_type_score: EssayTypeScore = Field(..., description="서술형 문항의 점수 및 텍스트")
#     difficulty_level: int = Field(..., description="문항 난이도 (1~5)")
#     is_correct: bool = Field(..., description="정답 여부")
#     timeout: bool = Field(..., description="시간 초과 여부")


# class QuizInfo(BaseModel):
#     quiz_id: str = Field(..., description="퀴즈 ID")
#     quizes: List[QuizQuestion] = Field(..., description="퀴즈에 포함된 문항 리스트")
#     total_score: int = Field(..., description="퀴즈 총점")


# class PlannerMeta(BaseModel):
#     date: str = Field(..., description="플래너 날짜 (YYYY-MM-DD)")
#     day_of_week: Literal["월", "화", "수", "목", "금", "토", "일"] = Field(..., description="요일")
#     planned_time_min: int = Field(..., description="계획된 총 공부 시간 (분 단위)")


# class PlannerContent(BaseModel):
#     text: str = Field(..., description="공부 계획 문장")
#     time: int = Field(..., description="해당 계획의 공부 시간 (분 단위)")


# class Planner(BaseModel):
#     meta: PlannerMeta = Field(..., description="플래너 메타데이터")
#     content: List[PlannerContent] = Field(..., description="하루 공부 계획 목록")
#     content_total_min: int = Field(..., description="총 계획된 공부 시간 (분 단위)")


class GeneratePlannerRequest(BaseModel):
    student_id: str = Field(..., description="학생 ID")
    date: str = Field(..., description="플래너 기준 날짜 (YYYY-MM-DD)")

# --------------

class EssayRequest(BaseModel):
    question: str = Field(..., description="서술형 문항 텍스트")
    answer: Union[int, str] = Field(..., description="정답 (객관식은 int, 서술형은 str)")
    user_answer: str = Field(..., description="사용자 답변 텍스트")


class EvaluateQuizQuestion(BaseModel):
    question_num: int = Field(..., description="문항 번호")
    question: str = Field(..., description="문항 텍스트")
    question_type: Literal["이해", "계산", "문제해결", "추론"] = Field(..., description="문항 유형")
    essay_type_score: Optional[float | None] = Field(
        None, description="서술형 점수 (자동 채점된 경우 float, 없으면 null)"
    )
    difficulty_level: int = Field(..., description="문항 난이도 (1~3)")
    answer: Union[int, str] = Field(..., description="정답 (객관식은 int, 서술형은 str)")
    user_answer: str = Field(..., description="사용자의 답변 텍스트")
    time: int = Field(..., description="해당 문항 풀이 시간 (초 단위)")
    evaluate_essay_type: bool = Field(
        ..., description="서술형 문항 채점 수행 여부 (True면 LLM 평가 수행)"
    )

# EvaluateQuizRequest
class EvaluateQuizRequest(BaseModel):
    quiz_id: str = Field(..., description="퀴즈 ID")
    quizes: List[EvaluateQuizQuestion] = Field(..., description="평가 대상 퀴즈 문항 리스트")

# --------------

# GetQuizRequest
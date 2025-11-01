from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Union


class GeneratePlannerRequest(BaseModel):
    student_id: str = Field(..., description="학생 ID")
    date: str = Field(..., description="플래너 기준 날짜 (YYYY-MM-DD)")

# --------------
# 내부에서 날릴 것
# class EssayRequest(BaseModel):
#     question: str = Field(..., description="서술형 문항 텍스트")
#     answer: Union[int, str] = Field(..., description="정답 (객관식은 int, 서술형은 str)")
#     user_answer: str = Field(..., description="사용자 답변 텍스트")


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

class GenerateQuizRequest(BaseModel):
    quis_id: str = Field(..., description="퀴즈 ID")
# api/v1/endpoints/grade.py
import asyncio
import json, re
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, HTTPException
from schema.grade_schema import GradeRequest, GradeResponse, settings
from utils.grade_utils import call_exaone_async

router = APIRouter()

# ─────────────── Prompt helpers ───────────────
def prompt_step1(problem_text: str, student_ocr: str) -> str:
    return f"""
너는 수학 서술형 풀이에서 '계산/대입/수치' 부분만 점검하는 보조 모듈이다.
아래 문제와 학생 풀이를 보고, 계산적으로 이상한 부분만 적어라.
없으면 "계산상 큰 문제는 없음" 이라고 써라.

[문제]
{problem_text}

[학생 풀이]
{student_ocr}

[계산 점검]
""".strip()

def prompt_step2(problem_text: str, student_ocr: str) -> str:
    return f"""
너는 수학 서술형 풀이에서 '논리적 비약'만 찾는 모듈이다.
중간 결론이 근거 없이 나온 경우, 앞줄과 안 맞는 경우만 적어라.
없으면 "논리 비약은 보이지 않음" 이라고 써라.

[문제]
{problem_text}

[학생 풀이]
{student_ocr}

[논리 점검]
""".strip()

def prompt_step3(problem_text: str, student_ocr: str, logic_text: str, rubric: Optional[str]) -> str:
    rubric_text = rubric or ""
    return f"""
너는 '풀이가 이 문제 의도/단원에 맞는지'만 판단하는 모듈이다.
앞 단계 논리 점검 결과도 함께 준다.

다음 3줄만 꼭 포함해서 써라:
- 판단: (알맞음 / 문제 의도와 다름)
- 이유: ...
- 이 문제에서 기대되는 개념: ...

[문제]
{problem_text}

[학생 풀이]
{student_ocr}

[이전 단계 논리 점검]
{logic_text}

[rubric 정보]
{rubric_text}

[적합성 판단]
""".strip()

def prompt_step4(problem_text: str, student_ocr: str, fit_text: str) -> str:
    return f"""
너는 '문제에서 요구한 값을 실제로 학생이 적었는지'만 확인하는 모듈이다.
예: "A와 B를 구하라"면 A와 B가 실제로 적혀 있어야 한다.

다음 3줄 형식으로 써라:
- 요구한 값 작성 여부: (모두 작성 / 일부 누락 / 작성 안 함)
- 누락된 항목: ...
- 메모: ...

[문제]
{problem_text}

[학생 풀이]
{student_ocr}

[이전 단계 적합성 판단]
{fit_text}

[요구값 점검]
""".strip()

def prompt_step5(problem_text: str, student_ocr: str, answer_key: str) -> str:
    return f"""
너는 '최종 정답이 모범답안과 같은지'만 보는 모듈이다.
A,B처럼 여러 값을 구하는 문제면 각각 맞았는지 쓰고,
형식만 다른 경우는 '형식만 다르고 값은 같음'이라고 써라.

다음 3줄 형식으로 써라:
- 정답 일치: (일치 / 일부 일치 / 불일치)
- 맞은 부분: ...
- 틀린 부분: ...

[문제]
{problem_text}

[학생 풀이]
{student_ocr}

[모범답안]
{answer_key}

[정답 점검]
""".strip()

def prompt_final(
    problem_text: str, student_ocr: str, answer_key: str, rubric: Optional[str],
    step1_txt: str, step2_txt: str, step3_txt: str, step4_txt: str, step5_txt: str,
    max_score: int
) -> str:
    rubric_text = rubric or ""
    return f"""
너는 수학 서술형 자동채점기의 '최종 합산기'이다.
아래 5개의 분석 결과를 종합해서 최종 채점 JSON **한 덩어리만** 출력하라.

[출력 규칙 - 매우 중요]
- 반드시 JSON만 출력한다. JSON 외의 문장은 절대 쓰지 않는다.
- 키 이름은 아래와 완전히 같아야 한다.
- 출력은 <JSON> 태그 안에만 쓴다. 태그 밖에는 아무것도 쓰지 않는다.

출력 예시(JSON 스키마):
{{
  "score": 0,
  "max_score": {max_score},
  "criteria": {{
    "relevance": 0,
    "validity": 0,
    "accuracy": 0,
    "completeness": 0,
    "presentation": 0
  }},
  "mistakes": [],
  "feedback": ""
}}

[채점 가이드]
1. step1(계산)에서 명백한 계산/대입 오류가 있으면 score는 2점을 넘기지 마라.
2. step2(논리)에서 명백한 비약이 있으면 score는 3점을 넘기지 마라.
3. step3(적합성)에서 "문제 의도와 다름"이면 relevance=0, score는 4점을 넘기지 마라.
4. step4(요구값)에서 일부 누락이면 completeness=0.
5. step5(정답)에서 일부만 맞으면 accuracy=0.

[문제]
{problem_text}

[학생 풀이]
{student_ocr}

[모범답안]
{answer_key}

[rubric/단원 정보]
{rubric_text}

[step1: 계산 점검 결과]
{step1_txt}

[step2: 논리 점검 결과]
{step2_txt}

[step3: 문제-풀이 적합성 결과]
{step3_txt}

[step4: 요구값 작성 여부]
{step4_txt}

[step5: 정답 일치 여부]
{step5_txt}

아래 태그 안에 JSON만 작성하라.
<JSON>
{{""".strip()  # '{' 프리픽스 깔기 (모델이 JSON 본문만 생성하도록 유도)

# ─────────────── JSON 추출 유틸 ───────────────
def _balanced_json_from(text: str) -> Optional[str]:
    if not text:
        return None
    i = text.find('{')
    if i == -1:
        return None
    depth = 0
    for j, ch in enumerate(text[i:], start=i):
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return text[i:j+1]
    return None

def extract_json_from_text_strict(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    t = text.strip()

    m = re.search(r"<JSON>(.*)</JSON>", t, flags=re.DOTALL | re.IGNORECASE)
    if m:
        block = m.group(1).strip()
        candidate = _balanced_json_from(block)
        if candidate:
            try:
                return json.loads(candidate)
            except Exception:
                pass

    candidate = _balanced_json_from(t)
    if candidate:
        try:
            return json.loads(candidate)
        except Exception:
            return None
    return None

def _schema_guard(data: Optional[Dict[str, Any]], max_score: int) -> Dict[str, Any]:
    if data is None:
        data = {
            "score": 0,
            "max_score": max_score,
            "criteria": {
                "relevance": 0, "validity": 0, "accuracy": 0,
                "completeness": 0, "presentation": 0
            },
            "mistakes": ["FINAL_PARSE_FAIL"],
            "feedback": "채점 결과를 파싱하지 못했습니다."
        }
    # 누락 키 보정
    def _get(d, k, default):
        return d[k] if isinstance(d, dict) and k in d else default
    data = {
        "score": _get(data, "score", 0),
        "max_score": _get(data, "max_score", max_score),
        "criteria": {
            "relevance": _get(_get(data, "criteria", {}), "relevance", 0),
            "validity": _get(_get(data, "criteria", {}), "validity", 0),
            "accuracy": _get(_get(data, "criteria", {}), "accuracy", 0),
            "completeness": _get(_get(data, "criteria", {}), "completeness", 0),
            "presentation": _get(_get(data, "criteria", {}), "presentation", 0),
        },
        "mistakes": _get(data, "mistakes", []),
        "feedback": _get(data, "feedback", "")
    }
    return data

# ─────────────── API: 비동기 채점 ───────────────
@router.post("/score", response_model=GradeResponse, summary="서술형 자동채점 (EXAONE, 병렬)")
async def grade_score(req: GradeRequest) -> GradeResponse:
    """
    step1~5를 비동기 병렬로 실행 → 마지막에 final 합산 1회 호출.
    """
    # 1) step1/2/5는 서로 독립 → 먼저 병렬
    s1_task = asyncio.create_task(
        call_exaone_async(settings.REMOTE_BASE, settings.REMOTE_API_KEY, prompt_step1(req.problem_text, req.student_ocr),
                          max_new_tokens=180, temperature=0.0, timeout_s=settings.REMOTE_TIMEOUT_S)
    )

    s2_task = asyncio.create_task(
        call_exaone_async(settings.REMOTE_BASE, settings.REMOTE_API_KEY, prompt_step2(req.problem_text, req.student_ocr),
                          max_new_tokens=180, temperature=0.0, timeout_s=settings.REMOTE_TIMEOUT_S)
    )

    s5_task = asyncio.create_task(
        call_exaone_async(settings.REMOTE_BASE, settings.REMOTE_API_KEY, prompt_step5(req.problem_text, req.student_ocr, req.answer_key),
                          max_new_tokens=180, temperature=0.0, timeout_s=settings.REMOTE_TIMEOUT_S)
    )

    s1, s2, s5 = await asyncio.gather(s1_task, s2_task, s5_task)

    # 2) step3는 step2 결과 의존 → 이후 호출
    s3 = await call_exaone_async(
        settings.REMOTE_BASE, settings.REMOTE_API_KEY,
        prompt_step3(req.problem_text, req.student_ocr, s2, req.rubric),
        max_new_tokens=200, temperature=0.0, timeout_s=settings.REMOTE_TIMEOUT_S
    )

    # 3) step4는 step3 결과 의존 → 이후 호출
    s4 = await call_exaone_async(
        settings.REMOTE_BASE, settings.REMOTE_API_KEY,
        prompt_step4(req.problem_text, req.student_ocr, s3),
        max_new_tokens=160, temperature=0.0, timeout_s=settings.REMOTE_TIMEOUT_S
    )


    # 4) final JSON 합성 (프리픽스 '{'로 유도)
    final_prompt = prompt_final(
        req.problem_text, req.student_ocr, req.answer_key, req.rubric,
        s1, s2, s3, s4, s5, req.max_score
    )
    raw = await call_exaone_async(
        settings.REMOTE_BASE, settings.REMOTE_API_KEY, final_prompt,
        max_new_tokens=220, temperature=0.0, timeout_s=settings.REMOTE_TIMEOUT_S
    )
    # 모델이 '{' 이후 본문만 생성했을 수 있으므로 보정
    raw_fixed = "{" + raw + "\n</JSON>"
    data = extract_json_from_text_strict(raw_fixed)

    # 5) 1회 재시도 (파싱 실패 시)
    if data is None:
        retry = f"""아래 태그 안에 JSON만 작성하라. 키는 예시와 동일해야 한다.
예시:
{{
  "score": 0,
  "max_score": {req.max_score},
  "criteria": {{
    "relevance": 0,
    "validity": 0,
    "accuracy": 0,
    "completeness": 0,
    "presentation": 0
  }},
  "mistakes": [],
  "feedback": ""
}}
<JSON>
{{"""
        raw2 = await call_exaone_async(
            settings.REMOTE_BASE, settings.REMOTE_API_KEY, retry,
            max_new_tokens=160, temperature=0.0, timeout_s=settings.REMOTE_TIMEOUT_S
        )
        data = extract_json_from_text_strict("{" + raw2 + "\n</JSON>")

    result = _schema_guard(data, req.max_score)
    return GradeResponse(result=result)

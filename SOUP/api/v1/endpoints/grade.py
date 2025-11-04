# api/v1/endpoints/grade.py
import asyncio
import json, re
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, HTTPException
from schema.grade_schema import GradeRequest, GradeResponse, settings
from utils.grade_utils import call_exaone_async
import re

def _extract_tag_block(text: str, tag: str) -> str:
    if not text:
        return ""
    m = re.search(rf"<{tag}>(.*?)</{tag}>", text, flags=re.DOTALL|re.IGNORECASE)
    return (m.group(1).strip() if m else "").strip()


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


def prompt_step234(problem_text: str, student_ocr: str, rubric: str | None) -> str:
    """
    범용형 step234: 논리(F2)·적합성(F3)·결과 작성 여부(F4)를 한 번에 산출.
    - REQVAL은 '작성 여부'만 판정(정오 판정은 step5에서 수행)
    - 새로운 계산/추정 금지, 주어진 텍스트 근거만 사용
    - 출력은 <LOGIC>/<FIT>/<REQVAL> 태그 내부에만 작성
    """
    rubric_text = rubric or ""
    return f"""
너는 수학 서술형 풀이를 평가하는 보조 모듈이다.
오직 [문제]/[학생 풀이]/[루브릭]의 텍스트만 근거로 판단하고, 새로운 계산이나 추정은 금지한다.

1) <LOGIC> — 논리 점검
- 근거 없는 결론, 앞뒤 모순, 비약만 지적하라.
- 없으면 정확히 "논리 비약은 보이지 않음"이라고 쓰라.

2) <FIT> — 문제 의도·단원 적합성
- 풀이가 문제의 학습 목표(루브릭 단원)와 맞는 접근인지 평가하라.
- 아래 3줄 형식을 그대로 쓰라.
  - 판단: (알맞음 / 문제 의도와 다름)
  - 이유: (텍스트에서 근거 구절을 짧게 인용)
  - 이 문제에서 기대되는 개념: (예: 인수분해, 삼각비, 극한, 확률의 곱셈정리, 닮음 등)

3) <REQVAL> — 문제에서 요구한 결과의 "명시적 작성 여부"만 판정
- 학생 풀이에 최종 결과(값/좌표/식/부등식/그래프 해석/결론 문장 등)가 **명시적으로 표현**되어 있으면 "작성"으로 본다.
- 맞고/틀림은 여기서 판단하지 않는다(정오 판정은 step5에서).
- "명시적"의 예:
  - 변수=값 표기(예: x=2, y=3)
  - 좌표·벡터·집합 등 표기(예: (2,3), ⟨1,−1⟩, A={{1,2}})
  - 완결된 수식/부등식/결론 문장(예: 최솟값은 3, 넓이는 6cm², 확률은 7/12)
- "불완전"의 예(작성으로 보지 않음):
  - 계산/변형만 있고 최종 결론이 없음(예: (x−2)(x−3)=0 만 있음)
  - 수치·기호 없이 암시만 함(예: “길이가 같다”)
- 아래 3줄 형식을 그대로 쓰라.
  - 요구한 값 작성 여부: (모두 작성 / 일부 누락 / 작성 안 함)
  - 누락된 항목: (없으면 "없음"; 여러 개면 쉼표 구분)
  - 메모: (필요시 1줄)

[출력 규칙]
- 아래 세 태그에만 결과를 작성하고, 태그 밖에는 아무것도 쓰지 마라.
- 각 태그는 간결히 한두 줄로 작성하라.

[문제]
{problem_text}

[학생 풀이]
{student_ocr}

[rubric/단원 정보]
{rubric_text}

<LOGIC>
</LOGIC>
<FIT>
</FIT>
<REQVAL>
</REQVAL>
""".strip()


def prompt_step5(problem_text: str, student_ocr: str, answer_key: str) -> str:
    """
    step5: 정답 비교 전용 (프롬프트만으로 엄격화)
    - 학생이 '실제로 적은 최종값' vs 모범답안을 교집합/차집합으로 비교
    - 절대 '수정하라/바꾸라' 같은 제안 금지, 판단/목록만 출력
    - 4줄 고정 키만 출력 (한글 키 정확히 유지)
    """
    return f"""
너는 '정답 비교 전용' 모듈이다. 새로운 계산·추론 금지.
오직 [학생 풀이]에 실제로 적힌 최종 결과(값/좌표/식/부등식/문장) 목록과 [모범답안] 목록을 비교하라.

[비교 절차]
1) 학생이 '최종 답으로 적은 항목들'을 모두 뽑는다.
2) 모범답안 항목들과 1:1로 비교한다.
3) 아래 4개 목록을 만든다.
   - 맞은 부분: 정답 ∩ 학생답
   - 틀린 부분: 학생답 − 정답
   - 누락된 정답: 정답 − 학생답
   - 최종 판정(정답 일치): 교집합 기준으로 [일치/일부 일치/불일치]

[출력 형식 — 반드시 아래 4줄 '그대로'만 출력. 다른 문장/설명/조언 금지]
- 정답 일치: (일치 / 일부 일치 / 불일치)
- 맞은 부분: [항목1, 항목2] 또는 "없음"
- 틀린 부분: [항목1, 항목2] 또는 "없음"
- 누락된 정답: [항목1, 항목2] 또는 "없음"

[금지]
- "수정/바꾸라/권장/제안" 등 조언 문구 금지
- 재계산/추정 금지
- 4줄 외 출력 금지

[문제]
{problem_text}

[학생 풀이]
{student_ocr}

[모범답안]
{answer_key}

[정답 비교 결과 — 4줄만 출력]
""".strip()


def prompt_final(
    problem_text: str,
    student_ocr: str,
    answer_key: str,
    rubric: str | None,
    step1_txt: str,
    step234_txt: str,  # ← 합본 하나
    step5_txt: str,
    max_score: int,
) -> str:
    rubric_text = rubric or ""
    return f"""
너는 수학 서술형 자동채점기의 '최종 합산기'이다.
오직 아래 제공된 텍스트(step1, step234, step5)와 [문제/학생/정답/루브릭]만 근거로 판단하며, 새로운 계산/추정은 금지한다.

[일관성 규칙 — 반드시 준수]
- accuracy는 step5 결과에 정합적으로 설정:
  - '정답 일치: 일치'면 accuracy = 최고
  - '일부 일치' 또는 '불일치'면 accuracy = 0
- completeness는 step234의 REQVAL에 정합적으로:
  - '요구한 값 작성 여부: 일부 누락/작성 안 함' → completeness = 0
- relevance는 step234의 FIT에 정합적으로:
  - '판단: 문제 의도와 다름' → relevance = 0, 최종 score ≤ {4 if max_score >= 5 else max_score-1}
- validity(계산/논리)는 step1(계산 오류)와 step234(LOGIC)에 정합적으로:
  - step1에 명백한 계산/대입 오류 → 최종 score ≤ 2
  - step234에서 논리 비약이 있으면 → 최종 score ≤ 3
- presentation은 간결·명확성 기준으로 설정.
- 최종 score는 위 caps 적용 후 {max_score} 범위에서 합리적으로 배정.

[출력 규칙 - 매우 중요]
- 반드시 JSON만 출력한다. 다른 문장 금지.
- 키는 아래 예시와 동일해야 한다.
- 출력은 <JSON> 태그 안에만 쓴다(태그 밖 출력 금지).

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

[step234: 논리·적합성·작성 여부 결과]
{step234_txt}

[step5: 정답 비교 결과]
{step5_txt}

<JSON>
{{""".strip()




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

@router.post("/score", response_model=GradeResponse, summary="서술형 자동채점 (EXAONE, 병렬)")
async def grade_score(req: GradeRequest) -> GradeResponse:
    # 1) step1/step5/step234 병렬
    s1_task = asyncio.create_task(
        call_exaone_async(
            settings.REMOTE_BASE, settings.REMOTE_API_KEY,
            prompt_step1(req.problem_text, req.student_ocr),
            max_new_tokens=160, temperature=0.0, timeout_s=settings.REMOTE_TIMEOUT_S
        )
    )
    s5_task = asyncio.create_task(
        call_exaone_async(
            settings.REMOTE_BASE, settings.REMOTE_API_KEY,
            prompt_step5(req.problem_text, req.student_ocr, req.answer_key),
            max_new_tokens=160, temperature=0.0, timeout_s=settings.REMOTE_TIMEOUT_S
        )
    )
    s234_task = asyncio.create_task(
        call_exaone_async(
            settings.REMOTE_BASE, settings.REMOTE_API_KEY,
            prompt_step234(req.problem_text, req.student_ocr, req.rubric),
            max_new_tokens=220, temperature=0.0, timeout_s=settings.REMOTE_TIMEOUT_S
        )
    )

    s1, s5, s234_raw = await asyncio.gather(s1_task, s5_task, s234_task)

    # 3) 최종 프롬프트 1회
    final_prompt = prompt_final(
        req.problem_text, req.student_ocr, req.answer_key, req.rubric,
        s1, s234_raw, s5, req.max_score
    )
    raw = await call_exaone_async(
        settings.REMOTE_BASE, settings.REMOTE_API_KEY, final_prompt,
        max_new_tokens=220, temperature=0.0, timeout_s=settings.REMOTE_TIMEOUT_S
    )
    raw_fixed = "{" + raw + "\n</JSON>"
    data = extract_json_from_text_strict(raw_fixed)

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

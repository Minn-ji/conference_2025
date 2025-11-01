
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from typing import Dict, Any
import json

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def ask_llm(prompt: str) -> str:
    """system 없이 단일 user 프롬프트로 호출."""
    resp = llm.invoke([HumanMessage(content=prompt)])
    return resp.content.strip()

def ensure_json(s: str) -> Dict[str, Any]:
    """LLM 결과가 JSON 문자열이어야 하는 노드에서 파싱."""
    s = s.strip()
    # 코드블록 제거 방지용 최소 처리
    if s.startswith("```"):
        s = s.strip("`")
        # ```json ... ``` 케이스
        if s.lower().startswith("json"):
            s = s[4:].strip()
    return json.loads(s)

def safe(val, default="없음"):
    return default if val is None else val
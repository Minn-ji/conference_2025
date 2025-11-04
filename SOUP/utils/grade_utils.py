# utils/grade_utils.py
import asyncio
import httpx
from fastapi import HTTPException
from urllib.parse import urljoin

_SEMA = asyncio.Semaphore(16)  # 동시 요청 제한

def _u(base: str, path: str) -> str:
    return urljoin(base.rstrip('/')+'/', path.lstrip('/'))

async def call_exaone_async(
    base: str,
    api_key: str,
    prompt: str,
    *,
    max_new_tokens: int = 180,
    temperature: float = 0.0,
    top_p: float | None = None,
    do_sample: bool = False,
    stop: list[str] | None = None,
    timeout_s: int = 30,
) -> str:
    """Vast 서버의 /exaone/generate를 호출 (세마포어로 동시성 제어)"""
    url = _u(base, "/exaone/generate")
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "prompt": prompt,
        "max_new_tokens": max_new_tokens,
        "temperature": temperature,
        "do_sample": do_sample,
    }
    if top_p is not None:
        payload["top_p"] = top_p
    if stop is not None:
        payload["stop"] = stop

    timeout = httpx.Timeout(timeout_s) if isinstance(timeout_s, (int, float)) else timeout_s

    async with _SEMA:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
    if resp.status_code != 200:
        # 어디로 쐈는지, 무엇이 왔는지 바로 보이게
        raise HTTPException(status_code=resp.status_code, detail=f"[{resp.status_code}] POST {url} -> {resp.text}")

    data = resp.json()
    return (data.get("text") or "").strip()

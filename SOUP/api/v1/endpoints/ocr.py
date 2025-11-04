from typing import Optional, List, Dict, Any
from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from schema.ocr_schema import settings, OCRResponse
from utils.ocr_utils import imagefile_to_b64_png, call_kanana_generate

# 기본 프롬프트는 utils로 빼도 되지만, 유지보수 편의상 여기 간단 정의
SYSTEM_PROMPT_DEFAULT = (
    "You are an OCR transcription assistant for handwritten math solutions.\n"
    "Your ONLY task is to transcribe exactly what is written in the image.\n"
    "Do NOT fix, correct, or interpret any errors in the math expressions.\n"
    "If the handwriting looks ambiguous, choose the most visually likely symbol rather than logically correct one.\n"
    "Korean explanation sentences must stay in Korean.\n"
    "All math expressions must be written in LaTeX and wrapped with $ ... $.\n"
    "Keep the same line breaks and spacing as in the original handwriting.\n"
    "Do NOT modify numbers or letters even if they seem mathematically wrong (e.g. write 2 even if it should be 8)."
)
USER_PROMPT_DEFAULT = (
    "다음 이미지는 손으로 쓴 수학 서술형 풀이입니다. "
    "위 규칙에 따라 그대로 옮겨 적으세요."
)

router = APIRouter()

@router.post("/transcribe", response_model=OCRResponse, summary="손글씨 수학 풀이 OCR 변환")
def ocr_transcribe(
    image_url: Optional[str] = Form(None),
    system_prompt: str = Form(SYSTEM_PROMPT_DEFAULT),
    user_prompt: str = Form(USER_PROMPT_DEFAULT),
    max_new_tokens: int = Form(512),
    temperature: float = Form(0.0),
    top_p: float = Form(1.0),
    do_sample: bool = Form(False),
    file: Optional[UploadFile] = File(None),
):
    """
    로컬 → Vast.ai Kanana 서버 중계 OCR
    - file (multipart) 또는 image_url 중 하나 필수
    """
    if not file and not image_url:
        raise HTTPException(status_code=400, detail="file 또는 image_url 중 하나는 필요합니다.")

    image_b64 = imagefile_to_b64_png(file) if file else None

    conv: List[Dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": "<image>"},
        {"role": "user",   "content": user_prompt},
    ]

    payload = {
        "image_url": image_url,
        "image_b64": image_b64,
        "conv": conv,
        "max_new_tokens": max_new_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "do_sample": do_sample,
    }

    data = call_kanana_generate(
        remote_base=settings.REMOTE_BASE,
        api_key=settings.REMOTE_API_KEY,
        payload=payload,
        timeout_s=settings.REMOTE_TIMEOUT_S,
    )
    return OCRResponse(text=data.get("text", ""), tokens=int(data.get("tokens", 0)))

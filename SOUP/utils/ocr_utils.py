import io
import base64
import requests
from PIL import Image
from fastapi import UploadFile, HTTPException

def imagefile_to_b64_png(img_file: UploadFile) -> str:
    """
    업로드된 이미지를 PNG로 변환 후 base64 인코딩합니다.
    Kanana API에 전달 가능한 형태: data:image/png;base64,<...>
    """
    data = img_file.file.read()
    image = Image.open(io.BytesIO(data)).convert("RGB")

    # 과도한 해상도 방지 (긴 변 2048px 권장)
    max_side = max(image.size)
    if max_side > 2048:
        scale = 2048 / max_side
        new_w = int(image.size[0] * scale)
        new_h = int(image.size[1] * scale)
        image = image.resize((new_w, new_h))

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64}"

def call_kanana_generate(remote_base: str, api_key: str, payload: dict, timeout_s: int = 120) -> dict:
    """
    Vast.ai 서버의 /kanana/generate API로 요청을 전송하고 결과(JSON)를 반환.
    """
    url = f"{remote_base}/kanana/generate"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=timeout_s)
        if r.status_code != 200:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        return r.json()
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="원격 Kanana 서버 응답 시간 초과")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"중계 실패: {e}")

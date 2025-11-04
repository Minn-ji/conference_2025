import os
from pydantic import BaseModel, Field
from typing import List, Optional

class Settings(BaseModel):
    """
    환경 설정 (스키마로 관리)
    - REMOTE_BASE: Vast.ai 서버의 Kanana API 베이스 URL
    - REMOTE_API_KEY: 서버의 API 키 (Authorization: Bearer <KEY>)
    - REMOTE_TIMEOUT_S: 요청 타임아웃(초)
    """
    REMOTE_BASE: str = Field(default=os.getenv("REMOTE_BASE", "http://208.181.135.123:61950"))
    REMOTE_API_KEY: str = Field(default=os.getenv("REMOTE_API_KEY", "Soup"))
    REMOTE_TIMEOUT_S: int = Field(default=int(os.getenv("REMOTE_TIMEOUT_S", "120")))

settings = Settings()

class ConversationTurn(BaseModel):
    role: str
    content: str

class OCRRequest(BaseModel):
    image_url: Optional[str] = None
    image_b64: Optional[str] = None
    conv: List[ConversationTurn]
    max_new_tokens: int = Field(default=512)
    temperature: float = Field(default=0.0)
    top_p: float = Field(default=1.0)
    do_sample: bool = Field(default=False)

class OCRResponse(BaseModel):
    text: str = Field(..., description="OCR 결과 텍스트")
    tokens: int = Field(..., description="생성된 토큰 수")

"""主機板標示 OCR 提示(僅供參考,不參與判定)。

流程:Ollama 視覺模型讀出照片上的型號字串 → 程式做「正規化精確比對」→
     綠燈(一致)/黃燈(不一致,請主管細看)。
角色定位:模型只負責「讀」,比對是確定性的程式邏輯,最終判斷永遠是主管的勾選。
Ollama 連不到或逾時 → 回 None,前端顯示「無法辨識」,人工流程不受影響。
"""

import base64
import logging
import re

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

PROMPT = (
    "Read the model number / marking text printed on the circuit board in this photo. "
    "Reply with ONLY the exact printed text, nothing else."
)


def normalize(text: str) -> str:
    """比對前正規化:轉大寫、去掉所有非英數字元(空白/連字號印刷差異不影響比對)。"""
    return re.sub(r"[^A-Z0-9]", "", text.upper())


def read_marking(image_bytes: bytes) -> str | None:
    """呼叫 Ollama 視覺模型讀取標示字串;失敗回 None(提示功能靜默降級)。"""
    try:
        response = httpx.post(
            f"{settings.ollama_url}/api/chat",
            json={
                "model": settings.ollama_model,
                "messages": [
                    {
                        "role": "user",
                        "content": PROMPT,
                        "images": [base64.b64encode(image_bytes).decode()],
                    }
                ],
                "stream": False,
            },
            timeout=settings.ocr_timeout_seconds,
        )
        response.raise_for_status()
        text = response.json()["message"]["content"].strip()
        return text or None
    except Exception as exc:  # noqa: BLE001 — 提示功能:任何失敗都不該影響主流程
        logger.warning("OCR 提示不可用(%s)", exc)
        return None


def compare_marking(expected: str, ocr_text: str) -> bool:
    """正規化後比對:預期字串需完整出現在辨識結果中(模型可能多讀到其他字)。"""
    if not expected or not ocr_text:
        return False
    return normalize(expected) in normalize(ocr_text)

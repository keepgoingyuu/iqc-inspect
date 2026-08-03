"""AI 助手:回答檢驗流程與當前檢驗單數據的問題。

- 上下文注入:帶 sheet_id 時,把該單的狀態/型號/判定/異常摘要放進 system prompt,
  模型能直接回答「這張單有哪些異常」「為什麼判不合格」。
- 只做問答輔助,不能操作系統、不參與判定。
- Ollama 離線 → 回 available=false,前端顯示提示,不影響主流程。
"""

import json
import logging
import re

import httpx
from fastapi import APIRouter, Depends
from opencc import OpenCC
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.service import get_current_user
from app.config import settings
from app.database import get_db
from app.models import InspectionSheet, User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/assistant", tags=["assistant"])

# 保險絲:模型偶爾飄簡體,回覆一律過「簡→台灣正體(含慣用詞)」;繁體過轉換無害
_s2twp = OpenCC("s2twp")

SYSTEM_PROMPT = """你是 IQC 進貨抽檢系統的 AI 助手,一律使用台灣正體中文(繁體)簡潔回答,禁止簡體字。
系統流程:建檢驗單(一櫃)→ 加型號(1~3個,選產品自動帶標準)→ 錄入積分球數據(PDF匯入)
→ 拍主機板標示照 → 綜合判定(超標自動高亮)→ 不合格強制二次拆檢 → 送審
→ 主管比對標示、簽核 → 匯出 Excel。判定由規則引擎完成,你不參與判定,只解讀說明。
回答要短、直接、用數據佐證;不知道就說不知道。
一律用純文字回答:不要使用任何 Markdown 語法(不要 **粗體**、# 標題、`程式碼`),
條列直接用「1. 2. 3.」或「-」開頭即可。"""


class ChatMessage(BaseModel):
    role: str  # user | assistant
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    sheet_id: int | None = None


def _sheet_context(db: Session, sheet_id: int) -> str:
    sheet = db.get(InspectionSheet, sheet_id)
    if sheet is None:
        return ""
    summary = {
        "檢驗單": sheet.id,
        "櫃號": sheet.container_no,
        "狀態": sheet.status,
        "QC日期": sheet.qc_date,
        "型號": [
            {
                "產品": mi.product_name,
                "判定": mi.result,
                "預期主機板標示": mi.expected_marking,
                "標示已確認": mi.marking_confirmed,
                "異常項目": (mi.judgement or {}).get("highlights", []),
                "樣品數據": [
                    {"第幾件": s.seq, "已確認": s.confirmed, **s.photometric}
                    for s in mi.samples
                ],
                "勾選與手動值": mi.item_values,
                "標稱參數": mi.params,
            }
            for mi in sheet.model_inspections
        ],
    }
    return "\n\n目前使用者正在看的檢驗單數據如下(JSON):\n" + json.dumps(
        summary, ensure_ascii=False
    )


def _strip_markdown(text: str) -> str:
    """保險絲:模型沒聽話時,把常見 Markdown 符號剝成純文字。"""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)  # **粗體**
    text = re.sub(r"(?<!\w)\*(?!\s)(.+?)(?<!\s)\*(?!\w)", r"\1", text)  # *斜體*
    text = re.sub(r"`([^`]+)`", r"\1", text)  # `行內碼`
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)  # # 標題
    return text


@router.post("/chat")
def chat(
    body: ChatRequest,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    system = SYSTEM_PROMPT
    if body.sheet_id:
        system += _sheet_context(db, body.sheet_id)

    messages = [{"role": "system", "content": system}] + [
        {"role": m.role, "content": m.content} for m in body.messages[-10:]
    ]
    try:
        response = httpx.post(
            f"{settings.ollama_url}/api/chat",
            json={
                "model": settings.ollama_model,
                "messages": messages,
                "stream": False,
                "think": False,
            },
            timeout=settings.ocr_timeout_seconds * 2,
        )
        response.raise_for_status()
        reply = _strip_markdown(response.json()["message"]["content"].strip())
        return {"available": True, "reply": _s2twp.convert(reply)}
    except Exception as exc:  # noqa: BLE001 — 輔助功能:失敗不影響主流程
        logger.warning("AI 助手不可用(%s)", exc)
        return {"available": False, "reply": ""}

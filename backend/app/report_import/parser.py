"""積分球 PDF 報告解析(Volnic FMS-6000「电光源测试报告」)。

策略:pdfplumber 抽文字層,以「標籤 + 單位」的正則定位數值。
已知風險:此類儀器 PDF 的中文標籤可能因字型編碼呈亂碼,
故每個欄位都同時提供「單位/英文縮寫」的備援 pattern(CCT、PF、Ra、lm、V、A、W),
不單獨依賴中文關鍵字。

尚未以真實 PDF 樣本驗證 — 拿到樣本後需跑 tests/test_parser.py 校正 pattern。
"""

import re
from io import BytesIO
from typing import Any

import pdfplumber

NUM = r"([0-9]+(?:\.[0-9]+)?)"

# 每欄位依序嘗試多個 pattern,先中後備援
FIELD_PATTERNS: dict[str, list[str]] = {
    "luminous_flux": [
        rf"光通量\s*\(?lm\)?\s*{NUM}",
        rf"\(lm\)\s*{NUM}",
    ],
    "efficacy": [
        rf"发光效率\s*\(?lm/w\)?\s*{NUM}",
        rf"發光效率\s*\(?lm/w\)?\s*{NUM}",
        rf"\(lm/w\)\s*{NUM}",
    ],
    "optical_power_mw": [
        rf"光功率\s*\(?mW\)?\s*{NUM}",
        rf"\(mW\)\s*{NUM}",
    ],
    "cct": [
        rf"相关色温\s*CCT\s*{NUM}",
        rf"相關色溫\s*CCT\s*{NUM}",
        rf"CCT\s*{NUM}\s*K?",
    ],
    "voltage": [
        rf"电压\s*U\s*{NUM}\s*V",
        rf"電壓\s*U\s*{NUM}\s*V",
        rf"\bU\s*{NUM}\s*V\b",
    ],
    "current": [
        rf"电流\s*I\s*{NUM}\s*A",
        rf"電流\s*I\s*{NUM}\s*A",
        rf"\bI\s*{NUM}\s*A\b",
    ],
    "power_w": [
        rf"功率\s*P\s*{NUM}\s*W",
        rf"\bP\s*{NUM}\s*W\b",
    ],
    "pf": [
        rf"PF\s*{NUM}",
    ],
    "cri": [
        rf"显色指数\s*CRI\s*Ra\s*=?\s*{NUM}",
        rf"顯色指數\s*CRI\s*Ra\s*=?\s*{NUM}",
        rf"Ra\s*=?\s*{NUM}",
    ],
}


class ParseError(Exception):
    pass


def extract_text(pdf_bytes: bytes) -> str:
    try:
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception as exc:
        raise ParseError(f"PDF 無法開啟:{exc}") from exc


def parse_report(pdf_bytes: bytes) -> dict[str, Any]:
    """回傳 {values: {key: float}, missing: [key], has_text_layer: bool}。

    文字層不存在(圖片型 PDF)時 has_text_layer=False,
    呼叫端應提示改走人工輸入(或未來的 OCR 備援)。
    """
    text = extract_text(pdf_bytes)
    if not text.strip():
        return {"values": {}, "missing": list(FIELD_PATTERNS), "has_text_layer": False}

    normalized = re.sub(r"[ \t]+", " ", text)
    values: dict[str, float] = {}
    missing: list[str] = []
    for key, patterns in FIELD_PATTERNS.items():
        for pattern in patterns:
            match = re.search(pattern, normalized)
            if match:
                values[key] = float(match.group(1))
                break
        else:
            missing.append(key)

    return {"values": values, "missing": missing, "has_text_layer": True}

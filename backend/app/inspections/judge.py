"""判定引擎:實測值 vs 檢驗標準 → 逐項 verdict + 異常高亮清單。

規則型別(spec item 的 rule.type):
- range:   min ≤ 值 ≤ max;或以 nominal ± tol_pct% 推算範圍
- min:     值 ≥ min
- max:     值 ≤ max
- check:   勾選必須為 "OK"
"""

from typing import Any

from app.models import ModelInspection


def _resolve_range(rule: dict) -> tuple[float | None, float | None]:
    lo, hi = rule.get("min"), rule.get("max")
    nominal = rule.get("nominal")
    tol_pct = rule.get("tol_pct")
    if nominal is not None and tol_pct is not None:
        lo = nominal * (1 - tol_pct / 100)
        hi = nominal * (1 + tol_pct / 100)
    # 下限≥90%/上限≤110% 這類百分比規則
    lo_pct, hi_pct = rule.get("min_pct"), rule.get("max_pct")
    if nominal is not None and lo_pct is not None:
        lo = nominal * lo_pct / 100
    if nominal is not None and hi_pct is not None:
        hi = nominal * hi_pct / 100
    return lo, hi


def evaluate_item(rule: dict, value: Any) -> dict:
    """回傳 {verdict: pass|fail|missing, reason}。"""
    if value is None or value == "":
        return {"verdict": "missing", "reason": "未填寫"}

    rtype = rule.get("type", "check")

    if rtype == "check":
        ok = str(value).strip().upper() == "OK"
        return {"verdict": "pass" if ok else "fail", "reason": "" if ok else "勾選為 NG"}

    try:
        num = float(value)
    except (TypeError, ValueError):
        return {"verdict": "fail", "reason": f"非數值:{value!r}"}

    if rtype == "range":
        lo, hi = _resolve_range(rule)
        if lo is not None and num < lo:
            return {"verdict": "fail", "reason": f"{num} 低於下限 {lo:g}"}
        if hi is not None and num > hi:
            return {"verdict": "fail", "reason": f"{num} 高於上限 {hi:g}"}
        return {"verdict": "pass", "reason": ""}
    if rtype == "min":
        lo = rule.get("min")
        if lo is not None and num < lo:
            return {"verdict": "fail", "reason": f"{num} 低於門檻 {lo:g}"}
        return {"verdict": "pass", "reason": ""}
    if rtype == "max":
        hi = rule.get("max")
        if hi is not None and num > hi:
            return {"verdict": "fail", "reason": f"{num} 高於門檻 {hi:g}"}
        return {"verdict": "pass", "reason": ""}

    return {"verdict": "fail", "reason": f"未知規則型別:{rtype}"}


def judge_model(mi: ModelInspection) -> dict:
    """對一個型號做綜合判定,寫入 mi.result / mi.judgement 並回傳明細。

    值的來源:
    - source_type=pdf 的項目 → 逐樣品取 photometric[key](每顆燈獨立判定)
    - 其他 → mi.item_values[key]
    """
    items: list[dict] = mi.spec.items or []
    detail: dict[str, Any] = {"items": {}, "highlights": []}
    any_fail = False
    any_missing = False

    for item in items:
        key = item["key"]
        rule = item.get("rule", {"type": "check"})
        source = item.get("source_type", "manual")

        if source == "auto":
            continue  # 標準值本身,不判定

        if source == "pdf":
            per_sample = {}
            for sample in sorted(mi.samples, key=lambda s: s.seq):
                result = evaluate_item(rule, sample.photometric.get(key))
                per_sample[str(sample.seq)] = result
                if result["verdict"] == "fail":
                    any_fail = True
                    detail["highlights"].append(
                        {"item": key, "sample": sample.seq, "reason": result["reason"]}
                    )
                elif result["verdict"] == "missing":
                    any_missing = True
            if not mi.samples:
                any_missing = True
                per_sample["1"] = {"verdict": "missing", "reason": "尚無樣品數據"}
            detail["items"][key] = per_sample
        else:
            result = evaluate_item(rule, mi.item_values.get(key))
            detail["items"][key] = result
            if result["verdict"] == "fail":
                any_fail = True
                detail["highlights"].append({"item": key, "reason": result["reason"]})
            elif result["verdict"] == "missing":
                any_missing = True

    if any_fail:
        mi.result = "fail"
    elif any_missing:
        mi.result = "pending"
    else:
        mi.result = "pass"

    detail["result"] = mi.result
    mi.judgement = detail
    return detail

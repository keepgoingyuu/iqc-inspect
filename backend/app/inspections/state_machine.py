"""檢驗單狀態機:防呆規則在此強制執行,不依賴前端 UI。

draft → data_entered → judged → (不合格) second_inspection → pending_review
                              → (合格) ────────────────────→ pending_review
pending_review → approved → archived
               → rejected → defect_ticket → archived
"""

from app.models import InspectionSheet

TRANSITIONS: dict[str, set[str]] = {
    "draft": {"data_entered"},
    "data_entered": {"judged"},
    "judged": {"second_inspection", "pending_review"},
    "second_inspection": {"judged", "pending_review"},
    "pending_review": {"approved", "rejected"},
    "approved": {"archived"},
    "rejected": {"defect_ticket"},
    "defect_ticket": {"archived"},
    "archived": set(),
}

# 這些狀態之後檢驗內容不可再修改(只能作廢重開)
LOCKED_STATUSES = {"approved", "rejected", "defect_ticket", "archived"}


class TransitionError(Exception):
    pass


def ensure_editable(sheet: InspectionSheet) -> None:
    if sheet.status in LOCKED_STATUSES:
        raise TransitionError(f"檢驗單已於「{sheet.status}」鎖定,不可修改;請作廢後重開")


def transition(sheet: InspectionSheet, to_status: str) -> None:
    """驗證並執行狀態轉移;違規時丟出 TransitionError。"""
    allowed = TRANSITIONS.get(sheet.status, set())
    if to_status not in allowed:
        raise TransitionError(f"不允許從「{sheet.status}」轉移到「{to_status}」")

    if to_status == "pending_review":
        _ensure_second_inspection_done(sheet)

    if to_status == "judged":
        for mi in sheet.model_inspections:
            if mi.result == "pending":
                raise TransitionError(f"型號「{mi.product_name}」尚未判定")

    sheet.status = to_status


def _ensure_second_inspection_done(sheet: InspectionSheet) -> None:
    """核心防呆:任一型號判定不合格,必須有第 2 件樣品(已確認數據)才能送審。"""
    for mi in sheet.model_inspections:
        if mi.result == "fail":
            confirmed_seqs = {s.seq for s in mi.samples if s.confirmed}
            if len(confirmed_seqs) < 2:
                raise TransitionError(
                    f"型號「{mi.product_name}」判定不合格,"
                    "必須完成第二件二次拆檢(數據已確認)才能進入審核"
                )

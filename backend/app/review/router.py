from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import audit
from app.auth.service import require_supervisor
from app.database import get_db
from app.inspections.schemas import SheetOut
from app.inspections.state_machine import TransitionError, transition
from app.models import AuditLog, InspectionSheet, ModelInspection, User

router = APIRouter(prefix="/api/review", tags=["review"])


class ReviewRequest(BaseModel):
    comment: str = ""


class AuditOut(BaseModel):
    id: int
    actor_id: int
    action: str
    detail: dict
    created_at: str

    model_config = {"from_attributes": True}


def _get_sheet(db: Session, sheet_id: int) -> InspectionSheet:
    sheet = db.get(InspectionSheet, sheet_id)
    if sheet is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "檢驗單不存在")
    return sheet


class MarkingConfirmRequest(BaseModel):
    confirmed: bool


@router.post("/models/{model_id}/confirm-marking")
def confirm_marking(
    model_id: int,
    body: MarkingConfirmRequest,
    db: Session = Depends(get_db),
    supervisor: User = Depends(require_supervisor),
) -> dict:
    """主管逐型號確認「主機板標示與認證一致」— 全數確認後簽核才會放行。"""
    mi = db.get(ModelInspection, model_id)
    if mi is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "型號檢驗不存在")
    if mi.sheet.status != "pending_review":
        raise HTTPException(status.HTTP_409_CONFLICT, "只有待審核狀態可確認標示")
    mi.marking_confirmed = body.confirmed
    mi.marking_confirmed_by = supervisor.id if body.confirmed else None
    audit.record(
        db, mi.sheet_id, supervisor.id, "confirm_marking",
        {"model_id": model_id, "product": mi.product_name, "confirmed": body.confirmed},
    )
    db.commit()
    return {"model_id": model_id, "marking_confirmed": mi.marking_confirmed}


@router.post("/sheets/{sheet_id}/approve", response_model=SheetOut)
def approve(
    sheet_id: int,
    body: ReviewRequest,
    db: Session = Depends(get_db),
    supervisor: User = Depends(require_supervisor),
) -> InspectionSheet:
    sheet = _get_sheet(db, sheet_id)
    try:
        transition(sheet, "approved")
    except TransitionError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    audit.record(db, sheet.id, supervisor.id, "approve", {"comment": body.comment})
    db.commit()
    return sheet


@router.post("/sheets/{sheet_id}/reject", response_model=SheetOut)
def reject(
    sheet_id: int,
    body: ReviewRequest,
    db: Session = Depends(get_db),
    supervisor: User = Depends(require_supervisor),
) -> InspectionSheet:
    sheet = _get_sheet(db, sheet_id)
    try:
        transition(sheet, "rejected")
        transition(sheet, "defect_ticket")  # 退件即開立異常單
    except TransitionError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    audit.record(db, sheet.id, supervisor.id, "reject", {"comment": body.comment})
    db.commit()
    return sheet


@router.get("/sheets/{sheet_id}/audit")
def audit_trail(
    sheet_id: int,
    db: Session = Depends(get_db),
    _supervisor: User = Depends(require_supervisor),
) -> list[dict]:
    _get_sheet(db, sheet_id)
    logs = db.scalars(
        select(AuditLog).where(AuditLog.sheet_id == sheet_id).order_by(AuditLog.id)
    )
    return [
        {
            "id": log.id,
            "actor_id": log.actor_id,
            "action": log.action,
            "detail": log.detail,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]

from sqlalchemy.orm import Session

from app.models import AuditLog


def record(
    db: Session, sheet_id: int, actor_id: int, action: str, detail: dict | None = None
) -> None:
    db.add(AuditLog(sheet_id=sheet_id, actor_id=actor_id, action=action, detail=detail or {}))

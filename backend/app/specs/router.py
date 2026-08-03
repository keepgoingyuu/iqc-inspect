from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.service import get_current_user, require_supervisor
from app.database import get_db
from app.models import SpecTemplate, User

router = APIRouter(prefix="/api/specs", tags=["specs"])


class SpecItemIn(BaseModel):
    key: str
    label: str
    source_type: str  # auto | pdf | manual | check
    rule: dict = {}
    standard_text: str = ""  # 表上「檢驗規範」欄顯示文字


class SpecCreate(BaseModel):
    name: str
    product_category: str
    items: list[SpecItemIn]


class SpecOut(BaseModel):
    id: int
    name: str
    product_category: str
    version: int
    items: list

    model_config = {"from_attributes": True}


@router.get("", response_model=list[SpecOut])
def list_specs(
    db: Session = Depends(get_db), _user: User = Depends(get_current_user)
) -> list[SpecTemplate]:
    return list(db.scalars(select(SpecTemplate).order_by(SpecTemplate.name, SpecTemplate.version)))


@router.get("/{spec_id}", response_model=SpecOut)
def get_spec(
    spec_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)
) -> SpecTemplate:
    spec = db.get(SpecTemplate, spec_id)
    if spec is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "檢驗標準不存在")
    return spec


@router.post("", response_model=SpecOut)
def create_spec(
    body: SpecCreate,
    db: Session = Depends(get_db),
    _supervisor: User = Depends(require_supervisor),
) -> SpecTemplate:
    """建立標準:同名自動遞增版本(標準版本化 — 舊單仍指向舊版,判定可重現)。"""
    valid_sources = {"auto", "pdf", "manual", "check"}
    for item in body.items:
        if item.source_type not in valid_sources:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                f"項目「{item.key}」的 source_type 需為 {valid_sources}",
            )
    latest = db.scalar(
        select(func.max(SpecTemplate.version)).where(SpecTemplate.name == body.name)
    )
    spec = SpecTemplate(
        name=body.name,
        product_category=body.product_category,
        version=(latest or 0) + 1,
        items=[item.model_dump() for item in body.items],
    )
    db.add(spec)
    db.commit()
    return spec

import secrets

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import audit
from app.auth.service import get_current_user
from app.config import settings
from app.database import get_db
from app.inspections import schemas
from app.inspections.judge import judge_model
from app.inspections.state_machine import TransitionError, ensure_editable, transition
from app.models import InspectionSheet, ModelInspection, Product, Sample, SpecTemplate, User
from app.report_import.parser import ParseError, parse_report

router = APIRouter(prefix="/api", tags=["inspections"])

MAX_MODELS_PER_SHEET = 3


def _get_sheet(db: Session, sheet_id: int) -> InspectionSheet:
    sheet = db.get(InspectionSheet, sheet_id)
    if sheet is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "檢驗單不存在")
    return sheet


def _get_model(db: Session, model_id: int) -> ModelInspection:
    mi = db.get(ModelInspection, model_id)
    if mi is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "型號檢驗不存在")
    return mi


def _get_sample(db: Session, sample_id: int) -> Sample:
    sample = db.get(Sample, sample_id)
    if sample is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "樣品不存在")
    return sample


def _editable_or_409(sheet: InspectionSheet) -> None:
    try:
        ensure_editable(sheet)
    except TransitionError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc


@router.post("/sheets", response_model=schemas.SheetOut)
def create_sheet(
    body: schemas.SheetCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> InspectionSheet:
    sheet = InspectionSheet(**body.model_dump(), created_by=user.id)
    db.add(sheet)
    db.flush()
    audit.record(db, sheet.id, user.id, "create_sheet", body.model_dump())
    db.commit()
    return sheet


@router.get("/sheets", response_model=list[schemas.SheetListItem])
def list_sheets(
    db: Session = Depends(get_db), _user: User = Depends(get_current_user)
) -> list[InspectionSheet]:
    return list(db.scalars(select(InspectionSheet).order_by(InspectionSheet.id.desc())))


@router.get("/sheets/{sheet_id}", response_model=schemas.SheetOut)
def get_sheet(
    sheet_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)
) -> InspectionSheet:
    return _get_sheet(db, sheet_id)


@router.post("/sheets/{sheet_id}/models", response_model=schemas.ModelOut)
def add_model(
    sheet_id: int,
    body: schemas.ModelCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ModelInspection:
    """選「產品」加入檢驗單:類別現行標準 + 參數 + 預期標示自動帶出並快照。"""
    sheet = _get_sheet(db, sheet_id)
    _editable_or_409(sheet)
    if len(sheet.model_inspections) >= MAX_MODELS_PER_SHEET:
        raise HTTPException(status.HTTP_409_CONFLICT, "一張檢驗單最多三個型號")

    product = db.get(Product, body.product_id)
    if product is None or not product.active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "產品不存在或已停用")

    # 取該類別「現行最新版」標準;快照後即使發新版,這張單仍指向舊版
    spec = db.scalar(
        select(SpecTemplate)
        .where(SpecTemplate.product_category == product.category)
        .order_by(SpecTemplate.version.desc())
        .limit(1)
    )
    if spec is None:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"類別「{product.category}」沒有檢驗標準",
        )

    mi = ModelInspection(
        sheet_id=sheet.id,
        spec_template_id=spec.id,
        product_id=product.id,
        product_name=product.name,
        batch_code=body.batch_code,
        params=dict(product.params),
        expected_marking=product.expected_marking,
    )
    db.add(mi)
    db.flush()
    audit.record(
        db, sheet.id, user.id, "add_model",
        {"model_id": mi.id, "product_id": product.id, "spec_version": spec.version},
    )
    db.commit()
    return mi


@router.patch("/models/{model_id}/values", response_model=schemas.ModelOut)
def update_item_values(
    model_id: int,
    body: schemas.ItemValuesUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ModelInspection:
    mi = _get_model(db, model_id)
    _editable_or_409(mi.sheet)
    mi.item_values = {**mi.item_values, **body.item_values}
    audit.record(db, mi.sheet_id, user.id, "update_values", {"model_id": mi.id})
    db.commit()
    return mi


@router.post("/models/{model_id}/samples", response_model=schemas.SampleOut)
def add_sample(
    model_id: int,
    body: schemas.SampleCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Sample:
    mi = _get_model(db, model_id)
    _editable_or_409(mi.sheet)
    if any(s.seq == body.seq for s in mi.samples):
        raise HTTPException(status.HTTP_409_CONFLICT, f"第 {body.seq} 件樣品已存在")
    sample = Sample(model_inspection_id=mi.id, seq=body.seq)
    db.add(sample)
    db.flush()
    audit.record(db, mi.sheet_id, user.id, "add_sample", {"sample_id": sample.id, "seq": body.seq})
    db.commit()
    return sample


@router.post("/samples/{sample_id}/pdf", response_model=schemas.ParseResult)
async def upload_pdf(
    sample_id: int,
    file: UploadFile,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    sample = _get_sample(db, sample_id)
    _editable_or_409(sample.model_inspection.sheet)
    pdf_bytes = await file.read()
    try:
        result = parse_report(pdf_bytes)
    except ParseError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc

    filename = f"report_{sample_id}_{secrets.token_hex(4)}.pdf"
    (settings.resolved_upload_dir / filename).write_bytes(pdf_bytes)

    # 解析值填入但 confirmed=False:等人工確認畫面按下確認才算數
    sample.photometric = {**sample.photometric, **result["values"]}
    sample.source = "pdf"
    sample.pdf_filename = filename
    sample.confirmed = False
    audit.record(
        db,
        sample.model_inspection.sheet_id,
        user.id,
        "upload_pdf",
        {"sample_id": sample_id, "parsed": result["values"], "missing": result["missing"]},
    )
    db.commit()
    return result


@router.patch("/samples/{sample_id}", response_model=schemas.SampleOut)
def update_sample(
    sample_id: int,
    body: schemas.SampleUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Sample:
    sample = _get_sample(db, sample_id)
    _editable_or_409(sample.model_inspection.sheet)
    if body.photometric is not None:
        sample.photometric = {**sample.photometric, **body.photometric}
    if body.confirmed is not None:
        sample.confirmed = body.confirmed
    audit.record(
        db,
        sample.model_inspection.sheet_id,
        user.id,
        "update_sample",
        {"sample_id": sample_id, "confirmed": sample.confirmed},
    )
    db.commit()
    return sample


@router.post("/sheets/{sheet_id}/judge", response_model=schemas.SheetOut)
def judge_sheet(
    sheet_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> InspectionSheet:
    """執行綜合判定:逐型號跑判定引擎並推進狀態到 judged。"""
    sheet = _get_sheet(db, sheet_id)
    _editable_or_409(sheet)
    if not sheet.model_inspections:
        raise HTTPException(status.HTTP_409_CONFLICT, "尚未加入任何型號")

    for mi in sheet.model_inspections:
        judge_model(mi)

    try:
        if sheet.status == "draft":
            transition(sheet, "data_entered")
        if sheet.status in ("data_entered", "second_inspection"):
            transition(sheet, "judged")
    except TransitionError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc

    audit.record(
        db, sheet.id, user.id, "judge",
        {mi.product_name: mi.result for mi in sheet.model_inspections},
    )
    db.commit()
    return sheet


@router.post("/sheets/{sheet_id}/transition", response_model=schemas.SheetOut)
def transition_sheet(
    sheet_id: int,
    body: schemas.TransitionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> InspectionSheet:
    """一般狀態轉移(送審、啟動二次拆檢、歸檔)。簽核/退件走 review API。"""
    if body.to_status in ("approved", "rejected"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "簽核/退件請使用審核 API(需主管權限)")
    sheet = _get_sheet(db, sheet_id)
    try:
        transition(sheet, body.to_status)
    except TransitionError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    audit.record(db, sheet.id, user.id, "transition", {"to": body.to_status})
    db.commit()
    return sheet

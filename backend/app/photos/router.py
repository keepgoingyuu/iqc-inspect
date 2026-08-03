import secrets
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app import audit
from app.auth.service import get_current_user
from app.config import settings
from app.database import get_db
from app.inspections.schemas import PhotoOut
from app.inspections.state_machine import TransitionError, ensure_editable
from app.models import Photo, Sample, User
from app.ocr import compare_marking, read_marking
from app.photos.service import compress_image

router = APIRouter(prefix="/api", tags=["photos"])

ALLOWED_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".heic"}


@router.post("/samples/{sample_id}/photos", response_model=PhotoOut)
async def upload_photo(
    sample_id: int,
    file: UploadFile,
    kind: str = "part",
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Photo:
    sample = db.get(Sample, sample_id)
    if sample is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "樣品不存在")
    try:
        ensure_editable(sample.model_inspection.sheet)
    except TransitionError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    if kind not in ("part", "marking"):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "kind 需為 part 或 marking")

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"不支援的圖片格式:{suffix}")

    # 手機原圖自動壓縮(約 5MB → 0.3MB);無法辨識的格式原樣保留
    data, new_suffix = compress_image(await file.read())
    filename = f"photo_{sample_id}_{secrets.token_hex(4)}{new_suffix or suffix}"
    (settings.resolved_upload_dir / filename).write_bytes(data)

    photo = Photo(sample_id=sample_id, kind=kind, filename=filename)
    db.add(photo)
    db.flush()
    audit.record(
        db,
        sample.model_inspection.sheet_id,
        user.id,
        "upload_photo",
        {"sample_id": sample_id, "photo_id": photo.id, "kind": kind},
    )
    db.commit()
    return photo


@router.post("/photos/{photo_id}/ocr")
def run_ocr(
    photo_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """OCR 提示:模型讀標示照字串 → 程式比對預期標示 → 綠/黃燈(不參與判定)。"""
    photo = db.get(Photo, photo_id)
    if photo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "照片不存在")
    if photo.kind != "marking":
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "只有主機板標示照可辨識")
    mi = photo.sample.model_inspection
    if not mi.expected_marking:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "此型號未設定預期標示字串")

    path = settings.resolved_upload_dir / photo.filename
    if not path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "照片檔案不存在(可能已被保存政策清除)")

    text = read_marking(path.read_bytes())
    if text is None:
        return {"available": False, "ocr_text": "", "match": None}

    match = compare_marking(mi.expected_marking, text)
    photo.ocr_text = text[:300]
    photo.ocr_match = match
    audit.record(
        db, mi.sheet_id, user.id, "ocr_hint",
        {"photo_id": photo_id, "ocr_text": text[:300], "match": match},
    )
    db.commit()
    return {"available": True, "ocr_text": text, "match": match}


@router.get("/files/{filename}")
def get_file(filename: str, _user: User = Depends(get_current_user)) -> FileResponse:
    # 阻擋路徑跳脫:只允許純檔名
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "非法檔名")
    path = settings.resolved_upload_dir / filename
    if not path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "檔案不存在")
    return FileResponse(path)

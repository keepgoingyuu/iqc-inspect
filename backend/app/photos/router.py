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
    if kind not in ("part", "certified"):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "kind 需為 part 或 certified")

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


@router.get("/files/{filename}")
def get_file(filename: str, _user: User = Depends(get_current_user)) -> FileResponse:
    # 阻擋路徑跳脫:只允許純檔名
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "非法檔名")
    path = settings.resolved_upload_dir / filename
    if not path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "檔案不存在")
    return FileResponse(path)

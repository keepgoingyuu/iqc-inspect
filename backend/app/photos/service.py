"""照片壓縮與到期清除。

- 壓縮:手機原圖(3~10MB)→ 長邊 2000px JPEG(約 0.2~0.4MB),
  證據清晰度足夠,儲存成本降 10~20 倍。
- 清除:滿保存期限(預設 24h,.env PHOTO_RETENTION_HOURS)且檢驗單「已歸檔」
  才刪除 — 避免主管隔天審核時照片已消失。
"""

import logging
from datetime import UTC, datetime, timedelta
from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import InspectionSheet, ModelInspection, Photo, Sample

logger = logging.getLogger(__name__)

MAX_DIMENSION = 2000
JPEG_QUALITY = 82


def compress_image(data: bytes) -> tuple[bytes, str]:
    """壓縮圖片,回傳 (bytes, 副檔名)。無法辨識的格式原樣保留。"""
    try:
        img = Image.open(BytesIO(data))
    except UnidentifiedImageError:
        return data, ""
    img = ImageOps.exif_transpose(img)  # 依 EXIF 轉正(手機直拍必要)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    img.thumbnail((MAX_DIMENSION, MAX_DIMENSION))
    buffer = BytesIO()
    img.save(buffer, "JPEG", quality=JPEG_QUALITY, optimize=True)
    return buffer.getvalue(), ".jpg"


def purge_expired_photos(db: Session) -> int:
    """刪除「滿保存期限且檢驗單已歸檔」的照片(檔案+紀錄),回傳刪除數。"""
    cutoff = datetime.now(UTC) - timedelta(hours=settings.photo_retention_hours)
    expired = db.scalars(
        select(Photo)
        .join(Sample, Photo.sample_id == Sample.id)
        .join(ModelInspection, Sample.model_inspection_id == ModelInspection.id)
        .join(InspectionSheet, ModelInspection.sheet_id == InspectionSheet.id)
        .where(Photo.uploaded_at < cutoff, InspectionSheet.status == "archived")
    ).all()

    for photo in expired:
        path = settings.resolved_upload_dir / photo.filename
        path.unlink(missing_ok=True)
        db.delete(photo)
    if expired:
        db.commit()
        logger.info(
            "已清除 %d 張到期照片(歸檔滿 %dh)", len(expired), settings.photo_retention_hours
        )
    return len(expired)

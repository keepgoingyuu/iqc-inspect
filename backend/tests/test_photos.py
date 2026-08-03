from datetime import UTC, datetime, timedelta
from io import BytesIO

from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import InspectionSheet, ModelInspection, Photo, Sample, SpecTemplate, User
from app.photos.service import compress_image, purge_expired_photos


def make_photo_bytes(width: int, height: int) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (width, height), "red").save(buffer, "PNG")
    return buffer.getvalue()


def test_compress_resizes_and_converts():
    original = make_photo_bytes(4000, 3000)
    compressed, suffix = compress_image(original)
    assert suffix == ".jpg"
    img = Image.open(BytesIO(compressed))
    assert max(img.size) <= 2000
    assert len(compressed) < len(original)


def test_compress_keeps_unknown_format():
    data, suffix = compress_image(b"not-an-image")
    assert data == b"not-an-image"
    assert suffix == ""


def make_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def seed_photo(db, status: str, hours_old: int) -> Photo:
    user = db.query(User).first()
    if user is None:
        user = User(
            username=f"u{status}{hours_old}", password_hash="x", display_name="t", role="inspector"
        )
        spec = SpecTemplate(name=f"s{status}{hours_old}", product_category="t", version=1, items=[])
        db.add_all([user, spec])
        db.flush()
    spec = db.query(SpecTemplate).first()
    sheet = InspectionSheet(container_no="C", status=status, created_by=user.id)
    db.add(sheet)
    db.flush()
    mi = ModelInspection(sheet_id=sheet.id, spec_template_id=spec.id, product_name="P")
    db.add(mi)
    db.flush()
    sample = Sample(model_inspection_id=mi.id, seq=1)
    db.add(sample)
    db.flush()
    photo = Photo(
        sample_id=sample.id,
        filename=f"gone_{status}_{hours_old}.jpg",
        uploaded_at=datetime.now(UTC) - timedelta(hours=hours_old),
    )
    db.add(photo)
    db.commit()
    return photo


def test_purge_only_archived_and_expired():
    db = make_db()
    seed_photo(db, "archived", hours_old=48)        # 該刪
    keep_active = seed_photo(db, "pending_review", hours_old=48)  # 未歸檔 → 保留
    keep_fresh = seed_photo(db, "archived", hours_old=1)          # 未滿期 → 保留

    deleted = purge_expired_photos(db)

    assert deleted == 1
    remaining = {p.filename for p in db.query(Photo).all()}
    assert remaining == {keep_active.filename, keep_fresh.filename}

from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    password_hash: Mapped[str] = mapped_column(String(200))
    display_name: Mapped[str] = mapped_column(String(50))
    role: Mapped[str] = mapped_column(String(20))  # inspector | supervisor
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class SpecTemplate(Base):
    """檢驗標準模板(版本化):同 name 發新 version,舊檢驗單仍指向舊版。

    items 結構(list[dict]),每項:
      key, label, source_type(auto|pdf|manual|check),
      rule(dict): {type: range|min|check, min, max, nominal, tol_pct, ...}
    """

    __tablename__ = "spec_templates"
    __table_args__ = (UniqueConstraint("name", "version"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))  # 例:吸頂燈-LED防潮灯15W
    product_category: Mapped[str] = mapped_column(String(50))  # 例:吸頂燈
    version: Mapped[int] = mapped_column(Integer, default=1)
    items: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class InspectionSheet(Base):
    __tablename__ = "inspection_sheets"

    id: Mapped[int] = mapped_column(primary_key=True)
    container_no: Mapped[str] = mapped_column(String(50))  # 櫃號
    seal_no: Mapped[str] = mapped_column(String(50), default="")  # 封籤號
    unstuffing_date: Mapped[str] = mapped_column(String(20), default="")  # 拆櫃日期
    qc_date: Mapped[str] = mapped_column(String(20), default="")
    status: Mapped[str] = mapped_column(String(30), default="draft")
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    model_inspections: Mapped[list["ModelInspection"]] = relationship(
        back_populates="sheet", cascade="all, delete-orphan"
    )


class ModelInspection(Base):
    """檢驗單上的一個產品型號(一張單 1~3 個並排)。"""

    __tablename__ = "model_inspections"

    id: Mapped[int] = mapped_column(primary_key=True)
    sheet_id: Mapped[int] = mapped_column(ForeignKey("inspection_sheets.id"))
    spec_template_id: Mapped[int] = mapped_column(ForeignKey("spec_templates.id"))
    product_name: Mapped[str] = mapped_column(String(200))
    batch_code: Mapped[str] = mapped_column(String(100), default="")
    # 型號層級的量測/勾選值:{item_key: value};value 為數值或 "OK"/"NG"
    item_values: Mapped[dict] = mapped_column(JSON, default=dict)
    # pending | pass | fail;由判定引擎寫入
    result: Mapped[str] = mapped_column(String(10), default="pending")
    # 判定明細(每項 verdict 與異常高亮),由判定引擎寫入
    judgement: Mapped[dict] = mapped_column(JSON, default=dict)

    sheet: Mapped[InspectionSheet] = relationship(back_populates="model_inspections")
    spec: Mapped[SpecTemplate] = relationship()
    samples: Mapped[list["Sample"]] = relationship(
        back_populates="model_inspection", cascade="all, delete-orphan"
    )


class Sample(Base):
    """實際拆檢的一顆燈。第 2 件 = 二次拆檢(不同顆燈、獨立數據)。"""

    __tablename__ = "samples"
    __table_args__ = (UniqueConstraint("model_inspection_id", "seq"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    model_inspection_id: Mapped[int] = mapped_column(ForeignKey("model_inspections.id"))
    seq: Mapped[int] = mapped_column(Integer, default=1)
    # 積分球數據:{luminous_flux, cct, power_w, efficacy, pf, cri, ...}
    photometric: Mapped[dict] = mapped_column(JSON, default=dict)
    source: Mapped[str] = mapped_column(String(10), default="manual")  # pdf | manual
    pdf_filename: Mapped[str] = mapped_column(String(300), default="")
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)  # 人工確認過解析值
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    model_inspection: Mapped[ModelInspection] = relationship(back_populates="samples")
    photos: Mapped[list["Photo"]] = relationship(
        back_populates="sample", cascade="all, delete-orphan"
    )


class Photo(Base):
    __tablename__ = "photos"

    id: Mapped[int] = mapped_column(primary_key=True)
    sample_id: Mapped[int] = mapped_column(ForeignKey("samples.id"))
    kind: Mapped[str] = mapped_column(String(20), default="part")  # part | certified
    filename: Mapped[str] = mapped_column(String(300))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    sample: Mapped[Sample] = relationship(back_populates="photos")


class AuditLog(Base):
    """Append-only 稽核軌跡:只新增,永不修改或刪除。"""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    sheet_id: Mapped[int] = mapped_column(ForeignKey("inspection_sheets.id"))
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(50))
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

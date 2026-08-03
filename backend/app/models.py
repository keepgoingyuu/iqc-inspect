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


class Product(Base):
    """產品主檔:型號的固有屬性。

    params:標稱參數 {nominal_power: 15, flux_min: 1350, ...},
           套入類別標準的公式算出該型號的合格範圍。
    expected_marking:主機板上應印的型號標示字串(審核比對的基準)。
    認證照片(選填,不一定有)掛 ProductPhoto。
    """

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    category: Mapped[str] = mapped_column(String(50))  # 對應 SpecTemplate.product_category
    params: Mapped[dict] = mapped_column(JSON, default=dict)
    expected_marking: Mapped[str] = mapped_column(String(200), default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    cert_photos: Mapped[list["ProductPhoto"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )


class ProductPhoto(Base):
    __tablename__ = "product_photos"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    filename: Mapped[str] = mapped_column(String(300))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    product: Mapped[Product] = relationship(back_populates="cert_photos")


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
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"), nullable=True)
    product_name: Mapped[str] = mapped_column(String(200))
    batch_code: Mapped[str] = mapped_column(String(100), default="")
    # 建立當下的產品參數/預期標示「快照」:產品主檔日後改了,舊單判定依據不變
    params: Mapped[dict] = mapped_column(JSON, default=dict)
    expected_marking: Mapped[str] = mapped_column(String(200), default="")
    # 主管審核關卡:確認主機板標示與認證一致(未全數確認,後端不放行簽核)
    marking_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    marking_confirmed_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
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
    # part=零件照 | marking=主機板標示照(送審必備) | certified=舊資料相容
    kind: Mapped[str] = mapped_column(String(20), default="part")
    filename: Mapped[str] = mapped_column(String(300))
    # OCR 提示(僅供參考,不參與判定):模型讀到的字串與比對結果
    ocr_text: Mapped[str] = mapped_column(String(300), default="")
    ocr_match: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
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

"""初始資料:預設帳號 + 吸頂燈檢驗標準模板(依紙本表單歸納)。

執行:uv run python -m app.seed
"""

from sqlalchemy import select

from app.auth.service import hash_password
from app.database import Base, SessionLocal, engine
from app.models import SpecTemplate, User

CEILING_LAMP_ITEMS = [
    # ── 自動帶入(標準值,不判定)──
    {"key": "nominal_power", "label": "標稱功率(W)", "source_type": "auto",
     "standard_text": "15", "rule": {}},
    {"key": "cct_spec", "label": "色溫規格(K)", "source_type": "auto",
     "standard_text": "6500K±500/4000K±500/3000K±300", "rule": {}},
    # ── 積分球 PDF 匯入(每樣品判定)──
    {"key": "cct", "label": "色溫實測(K)", "source_type": "pdf",
     "standard_text": "4000±500",
     "rule": {"type": "range", "nominal": 4000, "min": 3500, "max": 4500}},
    {"key": "power_w", "label": "功率實測(W)", "source_type": "pdf",
     "standard_text": "下限≥90%/上限≤110%",
     "rule": {"type": "range", "nominal": 15, "min_pct": 90, "max_pct": 110}},
    {"key": "luminous_flux", "label": "光通量(lm)", "source_type": "pdf",
     "standard_text": "1350~1500", "rule": {"type": "range", "min": 1350, "max": 1500}},
    {"key": "efficacy", "label": "光效(lm/W)", "source_type": "pdf",
     "standard_text": "90~100", "rule": {"type": "range", "min": 90, "max": 100}},
    {"key": "pf", "label": "PF 值", "source_type": "pdf",
     "standard_text": "≥0.4", "rule": {"type": "min", "min": 0.4}},
    {"key": "cri", "label": "顯色指數 CRI(Ra)", "source_type": "pdf",
     "standard_text": "≥80", "rule": {"type": "min", "min": 80}},
    # ── 手動數值 ──
    {"key": "net_weight", "label": "淨重實稱(g)", "source_type": "manual",
     "standard_text": "258±5%", "rule": {"type": "range", "nominal": 258, "tol_pct": 5}},
    {"key": "box_weight", "label": "外箱實秤(kg)", "source_type": "manual",
     "standard_text": "6.1±5%", "rule": {"type": "range", "nominal": 6.1, "tol_pct": 5}},
    {"key": "noise_db", "label": "實測噪音-環境音(dB)", "source_type": "manual",
     "standard_text": "<17", "rule": {"type": "max", "max": 17}},
    {"key": "ship_qty", "label": "出貨數量", "source_type": "manual",
     "standard_text": "", "rule": {"type": "min", "min": 0}},
    # ── OK/NG 勾選 ──
    {"key": "bom_check", "label": "實物+首件/BOM表", "source_type": "check",
     "standard_text": "核對", "rule": {"type": "check"}},
    {"key": "visual", "label": "目視外觀", "source_type": "check",
     "standard_text": "無瑕疵/異物/雜質", "rule": {"type": "check"}},
    {"key": "artwork_check", "label": "簽核稿件核對(彩盒/箱)", "source_type": "check",
     "standard_text": "核對", "rule": {"type": "check"}},
    {"key": "qr_code", "label": "掃描 QR CODE", "source_type": "check",
     "standard_text": "可讀取", "rule": {"type": "check"}},
    {"key": "switch_5x", "label": "開關 5 次", "source_type": "check",
     "standard_text": "93V/253V", "rule": {"type": "check"}},
    {"key": "dual_switch_5x", "label": "雙切開關 5 次", "source_type": "check",
     "standard_text": "93V/253V", "rule": {"type": "check"}},
    {"key": "aging", "label": "點測/老化(各半小時)", "source_type": "check",
     "standard_text": "不亮<1%", "rule": {"type": "check"}},
    {"key": "wall_switch_cct", "label": "壁切白光切換 5 秒內", "source_type": "check",
     "standard_text": "白光→自然光→黃光→小夜燈→白光", "rule": {"type": "check"}},
]


def seed() -> None:
    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        if db.scalar(select(User).where(User.username == "admin")) is None:
            db.add(User(username="admin", password_hash=hash_password("admin123"),
                        display_name="系統管理員", role="supervisor"))
            db.add(User(username="qc01", password_hash=hash_password("qc123"),
                        display_name="檢驗員01", role="inspector"))
            print("已建立帳號:admin/admin123(主管)、qc01/qc123(檢驗員)— 請儘速改密碼")
        existing_spec = db.scalar(
            select(SpecTemplate).where(SpecTemplate.name == "吸頂燈-LED防潮灯15W")
        )
        if existing_spec is None:
            db.add(SpecTemplate(name="吸頂燈-LED防潮灯15W", product_category="吸頂燈",
                                version=1, items=CEILING_LAMP_ITEMS))
            print("已建立檢驗標準:吸頂燈-LED防潮灯15W v1")
        db.commit()
        print("Seed 完成")
    finally:
        db.close()


if __name__ == "__main__":
    seed()

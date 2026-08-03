"""初始資料:預設帳號 + 吸頂燈類別標準(兩層設計)+ 示範產品主檔。

兩層設計:
- 類別標準(spec_templates):檢驗項目 + 公式,數字用參數引用(param/param_min/param_max)
- 產品主檔(products):各型號的標稱參數 + 預期主機板標示字串

執行:uv run python -m app.seed
"""

from sqlalchemy import select

from app.auth.service import hash_password
from app.database import Base, SessionLocal, engine
from app.models import Product, SpecTemplate, User

# ── 吸頂燈「類別標準」:公式引用參數,不寫死數字 ──
CEILING_LAMP_ITEMS = [
    # 自動帶入(標準值顯示,不判定)
    {"key": "nominal_power", "label": "標稱功率(W)", "source_type": "auto",
     "standard_text": "依產品主檔", "rule": {}},
    # 積分球 PDF 匯入(每樣品判定)
    {"key": "cct", "label": "色溫實測(K)", "source_type": "pdf",
     "standard_text": "標稱±500K",
     "rule": {"type": "range", "param_min": "cct_min", "param_max": "cct_max"}},
    {"key": "power_w", "label": "功率實測(W)", "source_type": "pdf",
     "standard_text": "下限≥90%/上限≤110%",
     "rule": {"type": "range", "param": "nominal_power", "min_pct": 90, "max_pct": 110}},
    {"key": "luminous_flux", "label": "光通量(lm)", "source_type": "pdf",
     "standard_text": "依產品主檔範圍",
     "rule": {"type": "range", "param_min": "flux_min", "param_max": "flux_max"}},
    {"key": "efficacy", "label": "光效(lm/W)", "source_type": "pdf",
     "standard_text": "依產品主檔範圍",
     "rule": {"type": "range", "param_min": "efficacy_min", "param_max": "efficacy_max"}},
    {"key": "pf", "label": "PF 值", "source_type": "pdf",
     "standard_text": "≥0.4", "rule": {"type": "min", "min": 0.4}},
    {"key": "cri", "label": "顯色指數 CRI(Ra)", "source_type": "pdf",
     "standard_text": "≥80", "rule": {"type": "min", "min": 80}},
    # 手動數值
    {"key": "net_weight", "label": "淨重實稱(g)", "source_type": "manual",
     "standard_text": "標稱±5%",
     "rule": {"type": "range", "param": "net_weight_nominal", "tol_pct": 5}},
    {"key": "box_weight", "label": "外箱實秤(kg)", "source_type": "manual",
     "standard_text": "標稱±5%",
     "rule": {"type": "range", "param": "box_weight_nominal", "tol_pct": 5}},
    {"key": "noise_db", "label": "實測噪音-環境音(dB)", "source_type": "manual",
     "standard_text": "<17", "rule": {"type": "max", "max": 17}},
    {"key": "ship_qty", "label": "出貨數量", "source_type": "manual",
     "standard_text": "", "rule": {"type": "min", "min": 0}},
    # OK/NG 勾選
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

# ── 示範產品主檔(依紙本表單的兩個型號)──
DEMO_PRODUCTS = [
    {
        "name": "LED 防潮灯 15W 曜弧黑 三色温 亮博士",
        "category": "吸頂燈",
        "expected_marking": "5205-G4-0150-3VC0101",
        "params": {
            "nominal_power": 15, "cct_nominal": 4000, "cct_min": 3500, "cct_max": 4500,
            "flux_min": 1350, "flux_max": 1500, "efficacy_min": 90, "efficacy_max": 100,
            "net_weight_nominal": 258, "box_weight_nominal": 6.1,
        },
    },
    {
        "name": "LED 防潮灯 15W 曜弧白 三色温 亮博士",
        "category": "吸頂燈",
        "expected_marking": "5205-B4-0150-3VC0101",
        "params": {
            "nominal_power": 15, "cct_nominal": 4000, "cct_min": 3500, "cct_max": 4500,
            "flux_min": 1350, "flux_max": 1500, "efficacy_min": 90, "efficacy_max": 100,
            "net_weight_nominal": 258, "box_weight_nominal": 6.1,
        },
    },
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
        if db.scalar(select(SpecTemplate).where(SpecTemplate.product_category == "吸頂燈")) is None:
            db.add(SpecTemplate(name="吸頂燈檢驗標準", product_category="吸頂燈",
                                version=1, items=CEILING_LAMP_ITEMS))
            print("已建立類別標準:吸頂燈 v1(參數化公式)")
        for spec in DEMO_PRODUCTS:
            if db.scalar(select(Product).where(Product.name == spec["name"])) is None:
                db.add(Product(**spec))
                print(f"已建立產品:{spec['name']}(標示 {spec['expected_marking']})")
        db.commit()
        print("Seed 完成")
    finally:
        db.close()


if __name__ == "__main__":
    seed()

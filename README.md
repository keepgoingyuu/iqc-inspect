# iqc-inspect — 進貨抽檢檢驗系統

LED 燈具進貨/出貨抽檢流程數位化:積分球 PDF 自動解析、自動判定與異常高亮、二次拆檢防呆、審核簽核、Excel 報表匯出。

需求與架構設計見 [docs/requirements.md](docs/requirements.md)。

## 環境需求

- [uv](https://docs.astral.sh/uv/)(Python 3.13)
- Node.js + pnpm

## 初次設定

```bash
cp .env.example .env        # 填入 SECRET_KEY(openssl rand -hex 32)

# 後端
cd backend
uv sync
uv run python -m app.seed   # 建立預設帳號與吸頂燈檢驗標準

# 前端
cd ../frontend
pnpm install
```

預設帳號(seed 建立,請儘速改密碼):`admin/admin123`(主管)、`qc01/qc123`(檢驗員)。

## 開發

```bash
# 後端(埠 8000)
cd backend && uv run uvicorn app.main:app --reload

# 前端(埠 5173,/api 自動轉發到 8000)
cd frontend && pnpm dev
```

後端 API 變更後,重新產生前端型別安全 client(需後端運行中):

```bash
cd frontend && pnpm generate-client
```

## 正式部署(內網單一服務)

```bash
cd frontend && pnpm build      # 產出 dist/,後端自動掛載
cd ../backend && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

內網任何電腦/平板瀏覽器開 `http://<主機IP>:8000` 即可使用(平板可直接呼叫相機拍照上傳)。

## 測試與品質

```bash
cd backend
uv run pytest        # 狀態機防呆、判定引擎、API
uv run ruff check app tests
```

## 專案結構

```
backend/app/
  ├── models.py            # 檢驗單 → 型號 ×1~3 → 樣品 ×N 資料層級
  ├── inspections/
  │   ├── state_machine.py # 狀態機:防呆規則後端強制(核心)
  │   ├── judge.py         # 判定引擎:實測 vs 標準 → 高亮異常
  │   └── router.py
  ├── report_import/parser.py  # 積分球 PDF 文字層解析(Volnic FMS-6000)
  ├── specs/               # 檢驗標準(版本化,新增產品不改程式)
  ├── review/              # 審核簽核 + append-only 稽核軌跡
  ├── export/              # Excel 匯出(openpyxl)
  ├── photos/              # 照片上傳
  └── auth/                # 登入 + 角色(檢驗員/主管)
frontend/src/
  ├── client/              # hey-api 自動產生,勿手改
  └── views/               # 登入、檢驗單列表、檢驗單詳情
```

## 待辦(見 docs/requirements.md §10)

- 取得真實 Volnic PDF 樣本驗證解析 pattern(目前依報告照片撰寫,未經實測)
- 公司 Excel 模板套版
- 第二期:OCR 備援、AI 輔助照片比對、統計儀表板

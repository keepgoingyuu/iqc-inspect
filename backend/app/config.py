from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# 專案根目錄(.env 所在):backend/app/config.py → 上兩層
ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT_DIR / ".env", extra="ignore")

    database_url: str = "sqlite:///./data/iqc.db"
    upload_dir: str = "./data/uploads"
    secret_key: str = "dev-only-insecure-key"
    port: int = 8000
    # 照片保存時數:滿時數「且檢驗單已歸檔」才清除(避免審核前照片消失)
    photo_retention_hours: int = 24
    # OCR 提示(Ollama):demo 與正式部署都是與系統同機,localhost 即可
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "gemma4:e4b"
    ocr_timeout_seconds: int = 60

    @property
    def resolved_database_url(self) -> str:
        # 相對路徑的 SQLite 一律以專案根目錄為基準,避免受啟動位置影響
        prefix = "sqlite:///./"
        if self.database_url.startswith(prefix):
            db_path = ROOT_DIR / self.database_url[len(prefix) :]
            db_path.parent.mkdir(parents=True, exist_ok=True)
            return f"sqlite:///{db_path}"
        return self.database_url

    @property
    def resolved_upload_dir(self) -> Path:
        path = Path(self.upload_dir)
        if not path.is_absolute():
            path = ROOT_DIR / path
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()

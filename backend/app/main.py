from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles

from app.auth.router import router as auth_router
from app.database import Base, engine
from app.export.router import router as export_router
from app.inspections.router import router as inspections_router
from app.photos.router import router as photos_router
from app.review.router import router as review_router
from app.specs.router import router as specs_router

FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(engine)  # MVP 以 create_all 建表;正式化後改 Alembic
    yield


def custom_generate_unique_id(route: APIRoute) -> str:
    # hey-api 產生的前端 client 方法名直接用 route 名稱,乾淨可讀
    return route.name


app = FastAPI(
    title="iqc-inspect",
    lifespan=lifespan,
    generate_unique_id_function=custom_generate_unique_id,
)

app.include_router(auth_router)
app.include_router(specs_router)
app.include_router(inspections_router)
app.include_router(photos_router)
app.include_router(review_router)
app.include_router(export_router)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


# 前端打包產物由後端直接掛載 → 單一服務,內網瀏覽器直接使用
if FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")

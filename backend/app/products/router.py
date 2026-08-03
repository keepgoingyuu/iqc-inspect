import secrets
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.service import get_current_user, require_supervisor
from app.config import settings
from app.database import get_db
from app.models import Product, ProductPhoto, SpecTemplate, User
from app.photos.service import compress_image

router = APIRouter(prefix="/api/products", tags=["products"])


class ProductCreate(BaseModel):
    name: str
    category: str
    params: dict = {}
    expected_marking: str = ""


class ProductUpdate(BaseModel):
    params: dict | None = None
    expected_marking: str | None = None
    active: bool | None = None


class ProductPhotoOut(BaseModel):
    id: int
    filename: str

    model_config = {"from_attributes": True}


class ProductOut(BaseModel):
    id: int
    name: str
    category: str
    params: dict
    expected_marking: str
    active: bool
    cert_photos: list[ProductPhotoOut] = []

    model_config = {"from_attributes": True}


@router.get("", response_model=list[ProductOut])
def list_products(
    db: Session = Depends(get_db), _user: User = Depends(get_current_user)
) -> list[Product]:
    return list(db.scalars(select(Product).order_by(Product.category, Product.name)))


@router.post("", response_model=ProductOut)
def create_product(
    body: ProductCreate,
    db: Session = Depends(get_db),
    _supervisor: User = Depends(require_supervisor),
) -> Product:
    if not db.scalar(
        select(SpecTemplate).where(SpecTemplate.product_category == body.category)
    ):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"類別「{body.category}」沒有對應的檢驗標準,請先建立標準",
        )
    if db.scalar(select(Product).where(Product.name == body.name)):
        raise HTTPException(status.HTTP_409_CONFLICT, "同名產品已存在")
    product = Product(**body.model_dump())
    db.add(product)
    db.commit()
    return product


@router.patch("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    body: ProductUpdate,
    db: Session = Depends(get_db),
    _supervisor: User = Depends(require_supervisor),
) -> Product:
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "產品不存在")
    if body.params is not None:
        product.params = body.params
    if body.expected_marking is not None:
        product.expected_marking = body.expected_marking
    if body.active is not None:
        product.active = body.active
    db.commit()
    return product


@router.post("/{product_id}/cert-photos", response_model=ProductPhotoOut)
async def upload_cert_photo(
    product_id: int,
    file: UploadFile,
    db: Session = Depends(get_db),
    _supervisor: User = Depends(require_supervisor),
) -> ProductPhoto:
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "產品不存在")
    suffix = Path(file.filename or "").suffix.lower()
    data, new_suffix = compress_image(await file.read())
    filename = f"cert_{product_id}_{secrets.token_hex(4)}{new_suffix or suffix}"
    (settings.resolved_upload_dir / filename).write_bytes(data)
    photo = ProductPhoto(product_id=product_id, filename=filename)
    db.add(photo)
    db.commit()
    return photo

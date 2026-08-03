from typing import Any

from pydantic import BaseModel


class SheetCreate(BaseModel):
    container_no: str
    seal_no: str = ""
    unstuffing_date: str = ""
    qc_date: str = ""


class ModelCreate(BaseModel):
    spec_template_id: int
    product_name: str
    batch_code: str = ""


class ItemValuesUpdate(BaseModel):
    item_values: dict[str, Any]


class SampleCreate(BaseModel):
    seq: int = 1


class SampleUpdate(BaseModel):
    photometric: dict[str, Any] | None = None
    confirmed: bool | None = None


class TransitionRequest(BaseModel):
    to_status: str


class PhotoOut(BaseModel):
    id: int
    kind: str
    filename: str

    model_config = {"from_attributes": True}


class SampleOut(BaseModel):
    id: int
    seq: int
    photometric: dict
    source: str
    pdf_filename: str
    confirmed: bool
    photos: list[PhotoOut] = []

    model_config = {"from_attributes": True}


class ModelOut(BaseModel):
    id: int
    spec_template_id: int
    product_name: str
    batch_code: str
    item_values: dict
    result: str
    judgement: dict
    samples: list[SampleOut] = []

    model_config = {"from_attributes": True}


class SheetOut(BaseModel):
    id: int
    container_no: str
    seal_no: str
    unstuffing_date: str
    qc_date: str
    status: str
    created_by: int
    model_inspections: list[ModelOut] = []

    model_config = {"from_attributes": True}


class SheetListItem(BaseModel):
    id: int
    container_no: str
    qc_date: str
    status: str

    model_config = {"from_attributes": True}


class ParseResult(BaseModel):
    values: dict[str, float]
    missing: list[str]
    has_text_layer: bool

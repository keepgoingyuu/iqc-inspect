from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth.service import get_current_user
from app.database import get_db
from app.export.paper_layout import build_workbook
from app.models import InspectionSheet, User

router = APIRouter(prefix="/api/export", tags=["export"])


@router.get("/sheets/{sheet_id}/xlsx")
def export_xlsx(
    sheet_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)
) -> StreamingResponse:
    """匯出檢驗報表 Excel(紙本版面重刻;待公司模板到手後改為模板填值)。"""
    sheet = db.get(InspectionSheet, sheet_id)
    if sheet is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "檢驗單不存在")

    wb = build_workbook(sheet)
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    filename = f"inspection_{sheet.container_no}_{sheet_id}.xlsx"
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

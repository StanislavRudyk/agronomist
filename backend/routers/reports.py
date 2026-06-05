from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io

from backend.modeles.database import get_db
from backend.routers.auth import get_current_user
from backend.modeles.models import User
from backend.services.reports_service import ReportsService

router = APIRouter()

def _get_user_id(db: Session, user_email: str) -> int:
    user = db.query(User).filter(User.email == user_email).first()
    return user.id

@router.get("/reports/annual/{year}", summary="Годовой отчёт (ГСМ, урожайность, операции, аномалии)")
async def annual_report(year: int, db: Session = Depends(get_db), user_email: str = Depends(get_current_user)):
    return ReportsService.annual_report(db, _get_user_id(db, user_email), year)

@router.get("/reports/field-history/{field_id}", summary="Книга истории поля (хронология культур, анализов, работ, погоды)")
async def field_history(field_id: int, db: Session = Depends(get_db), user_email: str = Depends(get_current_user)):
    return ReportsService.field_history(db, _get_user_id(db, user_email), field_id)

@router.get("/reports/export/work-orders", summary="Экспорт нарядов в CSV")
async def export_work_orders(db: Session = Depends(get_db), user_email: str = Depends(get_current_user)):
    csv_data = ReportsService.export_work_orders_csv(db, _get_user_id(db, user_email))
    return StreamingResponse(
        io.StringIO(csv_data),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=work_orders.csv"}
    )

@router.get("/reports/export/fuel", summary="Экспорт журнала ГСМ в CSV")
async def export_fuel(db: Session = Depends(get_db), user_email: str = Depends(get_current_user)):
    csv_data = ReportsService.export_fuel_csv(db, _get_user_id(db, user_email))
    return StreamingResponse(
        io.StringIO(csv_data),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=fuel_logs.csv"}
    )

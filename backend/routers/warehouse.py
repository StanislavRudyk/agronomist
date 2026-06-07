from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from backend.modeles.database import get_db
from backend.routers.auth import get_current_user
from backend.routers.auth import get_current_user
from backend.modeles.schemas import (
    WarehouseCreate, WarehouseResponse,
    GrainLotCreate, GrainLotResponse,
    QualityAnalysisCreate, QualityAnalysisResponse,
    StorageConditionCreate, StorageConditionResponse
)
from backend.services.warehouse_service import WarehouseService

router = APIRouter()

def _get_user_id(db: Session, user_email: str) -> int:
    from backend.modeles.models import User
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    return user.id

@router.post("/warehouse/", response_model=WarehouseResponse, summary="Регистрация склада/элеватора")
async def create_warehouse(data: WarehouseCreate, db: Session = Depends(get_db), user_email: str = Depends(get_current_user)):
    return WarehouseService.create_warehouse(db, data, _get_user_id(db, user_email))

@router.get("/warehouse/", response_model=List[WarehouseResponse], summary="Список складов")
async def get_warehouses(db: Session = Depends(get_db), user_email: str = Depends(get_current_user)):
    return WarehouseService.get_warehouses(db, _get_user_id(db, user_email))

@router.post("/warehouse/grain-lot/", response_model=GrainLotResponse, summary="Приёмка партии зерна на склад")
async def add_grain_lot(data: GrainLotCreate, db: Session = Depends(get_db), user_email: str = Depends(get_current_user)):
    return WarehouseService.add_grain_lot(db, data, _get_user_id(db, user_email))

@router.post("/warehouse/quality/", response_model=QualityAnalysisResponse, summary="Лабораторный анализ качества зерна")
async def add_quality(data: QualityAnalysisCreate, db: Session = Depends(get_db), user_email: str = Depends(get_current_user)):
    return WarehouseService.add_quality_analysis(db, data, _get_user_id(db, user_email))

@router.post("/warehouse/storage-condition/", response_model=StorageConditionResponse, summary="Логирование условий хранения")
async def log_storage(data: StorageConditionCreate, db: Session = Depends(get_db), user_email: str = Depends(get_current_user)):
    return WarehouseService.log_storage_condition(db, data, _get_user_id(db, user_email))

@router.get("/warehouse/storage-alerts/", summary="Алерты самосогревания зерна")
async def get_alerts(db: Session = Depends(get_db), user_email: str = Depends(get_current_user)):
    alerts = WarehouseService.get_storage_alerts(db, _get_user_id(db, user_email))
    return [{"warehouse_id": a.warehouse_id, "temperature_c": a.temperature_c, "humidity_pct": a.humidity_pct, "date": a.date} for a in alerts]

@router.get("/warehouse/storage-loss/", summary="Расчёт потерь при хранении (усушка)")
async def calc_loss(
    weight_t: float = Query(...), moisture_pct: float = Query(...), days: int = Query(...),
    user_email: str = Depends(get_current_user)
):
    return WarehouseService.calculate_storage_loss(weight_t, moisture_pct, days)

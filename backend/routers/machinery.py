from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from backend.modeles.database import get_db
from backend.routers.auth import get_current_user
from backend.modeles.schemas import (
    MachineryCreate,
    MachineryResponse,
    ImplementCreate,
    ImplementResponse,
    FuelLogCreate,
    FuelLogResponse,
    WorkOrderCreate,
    WorkOrderResponse
)
from backend.services.machinery_service import MachineryService

router = APIRouter()

@router.post("/machinery/", response_model=MachineryResponse, summary="Регистрация новой техники")
async def create_machinery(
    data: MachineryCreate,
    db: Session = Depends(get_db),
    user_email: str = Depends(get_current_user)
):
    # Упрощенно: считаем user_id из email для примера (в реальности нужен нормальный get_user_by_email)
    from backend.modeles.models import User
    user = db.query(User).filter(User.email == user_email).first()
    return MachineryService.create_machinery(db, data, user.id)

@router.post("/machinery/implements/", response_model=ImplementResponse, summary="Регистрация прицепного оборудования")
async def create_implement(
    data: ImplementCreate,
    db: Session = Depends(get_db),
    user_email: str = Depends(get_current_user)
):
    from backend.modeles.models import User
    user = db.query(User).filter(User.email == user_email).first()
    return MachineryService.create_implement(db, data, user.id)

@router.post("/machinery/fuel/", response_model=FuelLogResponse, summary="Логирование топлива (заправка/слив)")
async def log_fuel(
    data: FuelLogCreate,
    db: Session = Depends(get_db),
    user_email: str = Depends(get_current_user)
):
    from backend.modeles.models import User
    user = db.query(User).filter(User.email == user_email).first()
    return MachineryService.log_fuel(db, data, user.id)

@router.post("/machinery/work-orders/", response_model=WorkOrderResponse, summary="Создание наряда и расчет эффективности")
async def create_work_order(
    data: WorkOrderCreate,
    db: Session = Depends(get_db),
    user_email: str = Depends(get_current_user)
):
    from backend.modeles.models import User
    user = db.query(User).filter(User.email == user_email).first()
    return MachineryService.create_work_order(db, data, user.id)

@router.get("/machinery/maintenance-alerts/", summary="Получение предупреждений о ТО")
async def get_maintenance_alerts(
    db: Session = Depends(get_db),
    user_email: str = Depends(get_current_user)
):
    from backend.modeles.models import User
    user = db.query(User).filter(User.email == user_email).first()
    return MachineryService.get_maintenance_alerts(db, user.id)

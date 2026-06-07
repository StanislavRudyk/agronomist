from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.dependencies import get_current_user_id
from backend.modeles.database import get_db
from backend.modeles.schemas import (
    MachineryCreate,
    MachineryResponse,
    ImplementCreate,
    ImplementResponse,
    FuelLogCreate,
    FuelLogResponse,
    WorkOrderCreate,
    WorkOrderResponse,
)
from backend.services.machinery_service import MachineryService

router = APIRouter()


@router.post("/machinery/", response_model=MachineryResponse, summary="Регистрация новой техники")
async def create_machinery(
    data: MachineryCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    return MachineryService.create_machinery(db, data, user_id)


@router.post("/machinery/implements/", response_model=ImplementResponse, summary="Регистрация прицепного оборудования")
async def create_implement(
    data: ImplementCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    return MachineryService.create_implement(db, data, user_id)


@router.post("/machinery/fuel/", response_model=FuelLogResponse, summary="Логирование топлива (заправка/слив)")
async def log_fuel(
    data: FuelLogCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    return MachineryService.log_fuel(db, data, user_id)


@router.post("/machinery/work-orders/", response_model=WorkOrderResponse, summary="Создание наряда и расчет эффективности")
async def create_work_order(
    data: WorkOrderCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    return MachineryService.create_work_order(db, data, user_id)


@router.get("/machinery/maintenance-alerts/", summary="Получение предупреждений о ТО")
async def get_maintenance_alerts(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    return MachineryService.get_maintenance_alerts(db, user_id)

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.modeles.database import get_db
from backend.routers.auth import get_current_user
from backend.modeles.schemas import (
    SoilAnalysisCreate,
    SoilAnalysisResponse,
    YieldForecastResponse
)
from backend.services.yield_service import YieldForecastService

router = APIRouter()

@router.post("/fields/{field_id}/soil-analysis", response_model=SoilAnalysisResponse, summary="Внесение результатов агрохимического анализа почвы")
async def add_soil_analysis(
    field_id: int,
    data: SoilAnalysisCreate,
    db: Session = Depends(get_db),
    user_email: str = Depends(get_current_user)
):
    from backend.modeles.models import User
    user = db.query(User).filter(User.email == user_email).first()
    return YieldForecastService.add_soil_analysis(db, field_id, data, user.id)

@router.get("/fields/{field_id}/yield-forecast", response_model=YieldForecastResponse, summary="Получить прогноз урожайности (эвристическая модель)")
async def get_yield_forecast(
    field_id: int,
    db: Session = Depends(get_db),
    user_email: str = Depends(get_current_user)
):
    from backend.modeles.models import User
    user = db.query(User).filter(User.email == user_email).first()
    return YieldForecastService.forecast_yield(db, field_id, user.id)


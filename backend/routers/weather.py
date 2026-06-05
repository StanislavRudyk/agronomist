from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.modeles.database import get_db
from backend.modeles.schemas import AgroWeatherCurrentResponse, AgroWeatherForecastResponse
from backend.services.agro_weather_service import AgroWeatherService
from backend.routers.auth import get_current_user

router = APIRouter()

@router.get("/weather/current/{field_id}", response_model=AgroWeatherCurrentResponse, summary="Получить текущую агро-погоду для поля")
async def get_current_agro_weather(
    field_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return await AgroWeatherService.get_current_weather(field_id=field_id, db=db)

@router.get("/weather/forecast/{field_id}", response_model=AgroWeatherForecastResponse, summary="Получить 7-дневный агро-прогноз для поля")
async def get_forecast_agro_weather(
    field_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return await AgroWeatherService.get_forecast_weather(field_id=field_id, db=db)

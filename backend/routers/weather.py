from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.modeles.database import get_db
from backend.modeles.schemas import (
    AgroWeatherCurrentResponse,
    AgroWeatherForecastResponse,
    AirQualityCurrentResponse,
    AirQualityForecastResponse,
    FloodForecastResponse,
)
from backend.services.agro_weather_service import AgroWeatherService
from backend.services.air_quality_service import AirQualityService
from backend.services.flood_service import FloodService
from backend.routers.auth import get_current_user

router = APIRouter()


@router.get(
    "/weather/current/{field_id}",
    response_model=AgroWeatherCurrentResponse,
    summary="Текущая агро-погода для поля (27 параметров Open-Meteo)",
)
async def get_current_agro_weather(
    field_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    return await AgroWeatherService.get_current_weather(
        field_id=field_id, user_email=current_user, db=db
    )


@router.get(
    "/weather/forecast/{field_id}",
    response_model=AgroWeatherForecastResponse,
    summary="7-дневный агро-прогноз для поля (все daily + hourly параметры Open-Meteo)",
)
async def get_forecast_agro_weather(
    field_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    return await AgroWeatherService.get_forecast_weather(
        field_id=field_id, user_email=current_user, db=db
    )


@router.get(
    "/weather/air-quality/current/{field_id}",
    response_model=AirQualityCurrentResponse,
    summary="Текущее качество воздуха для поля (PM10, PM2.5, пыль, EAQI, NO₂, O₃)",
)
async def get_current_air_quality(
    field_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    return await AirQualityService.get_current(
        field_id=field_id, user_email=current_user, db=db
    )


@router.get(
    "/weather/air-quality/forecast/{field_id}",
    response_model=AirQualityForecastResponse,
    summary="5-дневный прогноз качества воздуха для поля",
)
async def get_forecast_air_quality(
    field_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    return await AirQualityService.get_forecast(
        field_id=field_id, user_email=current_user, db=db
    )


@router.get(
    "/weather/flood/{field_id}",
    response_model=FloodForecastResponse,
    summary="7-дневный прогноз паводка для поля (расход реки м³/с)",
)
async def get_flood_forecast(
    field_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    return await FloodService.get_forecast(
        field_id=field_id, user_email=current_user, db=db
    )

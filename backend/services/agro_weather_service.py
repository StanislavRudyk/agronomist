import json
import httpx
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.logging_config import logger
from backend.modeles.models import Field, AgroWeatherData
from backend.modeles.schemas import AgroWeatherCurrentResponse, AgroWeatherForecastResponse, AgroWeatherForecastDaily
from backend.modeles.redis_client import get_redis
from backend.services.agro_analyzer import AgroAnalyzer

class AgroWeatherService:
    @staticmethod
    async def get_current_weather(field_id: int, db: Session) -> AgroWeatherCurrentResponse:
        redis = await get_redis()
        cache_key = f"agro_weather:current:{field_id}"

        try:
            cached = await redis.get(cache_key)
            if cached:
                logger.info(f"Найден кэш текущей агро-погоды для поля {field_id}")
                data = json.loads(cached)
                data["fetched_at"] = datetime.fromisoformat(data["fetched_at"])
                return AgroWeatherCurrentResponse(**data)
        except Exception as e:
            logger.error(f"Ошибка Redis при получении текущей агро-погоды: {e}")

        field = db.query(Field).filter(Field.id == field_id).first()
        if not field:
            raise HTTPException(status_code=404, detail="Поле не найдено")

        api_url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": field.latitude,
            "longitude": field.longitude,
            "current": "temperature_2m,soil_temperature_6cm,soil_moisture_3_to_9cm,snow_depth",
            "timezone": "auto"
        }

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(api_url, params=params)
                if response.status_code == 200:
                    api_data = response.json()
                    current = api_data["current"]

                    air_temp = float(current["temperature_2m"])
                    soil_temp = float(current["soil_temperature_6cm"])
                    soil_moisture = float(current["soil_moisture_3_to_9cm"])
                    snow_depth = float(current.get("snow_depth", 0.0))

                    warnings = AgroAnalyzer.analyze(
                        crop_type=field.crop_type,
                        air_temp=air_temp,
                        soil_temp=soil_temp,
                        soil_moisture=soil_moisture,
                        snow_depth=snow_depth
                    )

                    db_entry = AgroWeatherData(
                        field_id=field_id,
                        air_temp=air_temp,
                        soil_temp=soil_temp,
                        soil_moisture=soil_moisture,
                        warnings=json.dumps(warnings)
                    )
                    db.add(db_entry)
                    db.commit()
                    db.refresh(db_entry)

                    result = AgroWeatherCurrentResponse(
                        air_temp=air_temp,
                        soil_temp=soil_temp,
                        soil_moisture=soil_moisture,
                        warnings=warnings,
                        fetched_at=db_entry.created_at
                    )

                    try:
                        cache_data = result.model_dump()
                        cache_data["fetched_at"] = cache_data["fetched_at"].isoformat()
                        await redis.setex(cache_key, 3600, json.dumps(cache_data))
                    except Exception as e:
                        logger.error(f"Ошибка Redis при записи кэша агро-погоды: {e}")

                    logger.info(f"Агро-погода успешно получена для поля {field_id}")
                    return result
                else:
                    logger.warning(f"Open-Meteo вернул код {response.status_code} для координат {field.latitude}, {field.longitude}")

        except Exception as e:
            logger.error(f"Ошибка запроса к Open-Meteo для поля {field_id}: {e}")

        logger.info(f"Попытка получить оффлайн агро-данные для поля {field_id}")
        db_offline = db.query(AgroWeatherData)\
            .filter(AgroWeatherData.field_id == field_id)\
            .order_by(desc(AgroWeatherData.created_at))\
            .first()

        if db_offline:
            logger.info(f"Отданы оффлайн агро-данные для поля {field_id}")
            return AgroWeatherCurrentResponse(
                air_temp=db_offline.air_temp,
                soil_temp=db_offline.soil_temp,
                soil_moisture=db_offline.soil_moisture,
                warnings=json.loads(db_offline.warnings) if db_offline.warnings else [],
                fetched_at=db_offline.created_at
            )

        raise HTTPException(
            status_code=404,
            detail="Данные о погоде для поля недоступны (оффлайн режим пуст)"
        )

    @staticmethod
    async def get_forecast_weather(field_id: int, db: Session) -> AgroWeatherForecastResponse:
        redis = await get_redis()
        cache_key = f"agro_weather:forecast:{field_id}"

        try:
            cached = await redis.get(cache_key)
            if cached:
                logger.info(f"Найден кэш прогноза агро-погоды для поля {field_id}")
                data = json.loads(cached)
                return AgroWeatherForecastResponse(**data)
        except Exception as e:
            logger.error(f"Ошибка Redis при получении прогноза агро-погоды: {e}")

        field = db.query(Field).filter(Field.id == field_id).first()
        if not field:
            raise HTTPException(status_code=404, detail="Поле не найдено")

        api_url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": field.latitude,
            "longitude": field.longitude,
            "hourly": "temperature_2m,precipitation,snow_depth,soil_temperature_6cm,soil_moisture_3_to_9cm",
            "timezone": "auto"
        }

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(api_url, params=params)
                if response.status_code == 200:
                    api_data = response.json()
                    hourly = api_data["hourly"]

                    times = hourly["time"]
                    temps = hourly["temperature_2m"]
                    precips = hourly["precipitation"]
                    snows = hourly["snow_depth"]
                    soil_temps = hourly["soil_temperature_6cm"]
                    soil_moistures = hourly["soil_moisture_3_to_9cm"]

                    forecasts = []

                    for i in range(7):
                        start_idx = i * 24
                        end_idx = (i + 1) * 24

                        day_temps = temps[start_idx:end_idx]
                        day_precips = precips[start_idx:end_idx]
                        day_snows = snows[start_idx:end_idx]
                        day_soil_temps = soil_temps[start_idx:end_idx]
                        day_soil_moistures = soil_moistures[start_idx:end_idx]

                        max_temp = max(day_temps)
                        min_temp = min(day_temps)
                        precip_sum = sum(day_precips)
                        mean_soil_temp = sum(day_soil_temps) / 24
                        mean_soil_moisture = sum(day_soil_moistures) / 24
                        mean_snow = sum(day_snows) / 24

                        precip_5days = sum(precips[start_idx:min(start_idx + 120, len(precips))])

                        warnings = AgroAnalyzer.analyze(
                            crop_type=field.crop_type,
                            air_temp=min_temp,
                            soil_temp=mean_soil_temp,
                            soil_moisture=mean_soil_moisture,
                            snow_depth=mean_snow,
                            precip_5days=precip_5days
                        )

                        date_str = times[start_idx].split("T")[0]
                        forecasts.append(AgroWeatherForecastDaily(
                            date=date_str,
                            max_temp=round(max_temp, 1),
                            min_temp=round(min_temp, 1),
                            precipitation=round(precip_sum, 1),
                            warnings=warnings
                        ))

                    result = AgroWeatherForecastResponse(
                        field_id=field_id,
                        crop_type=field.crop_type,
                        forecast=forecasts
                    )

                    try:
                        await redis.setex(cache_key, 3600, result.model_dump_json())
                    except Exception as e:
                        logger.error(f"Ошибка Redis при записи кэша прогноза агро-погоды: {e}")

                    return result
        except Exception as e:
            logger.error(f"Ошибка запроса прогноза Open-Meteo для поля {field_id}: {e}")

        raise HTTPException(
            status_code=503,
            detail="Прогноз погоды временно недоступен (сервер Open-Meteo недоступен)"
        )

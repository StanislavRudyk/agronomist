import json
import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.logging_config import logger
from backend.modeles.models import Field, User
from backend.modeles.schemas import (
    AirQualityCurrentResponse,
    AirQualityForecastResponse,
    AirQualityForecastDaily,
)
from backend.modeles.redis_client import get_redis
from backend.services.agro_analyzer import AgroAnalyzer

_AQ_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
_HTTP_TIMEOUT = httpx.Timeout(connect=3.0, read=10.0, write=5.0, pool=5.0)
_CACHE_TTL = 3600
_CURRENT_PARAMS = "pm10,pm2_5,dust,european_aqi,us_aqi,uv_index,nitrogen_dioxide,ozone"
_HOURLY_PARAMS = "pm10,pm2_5,dust,european_aqi,us_aqi"


def _get_field_for_user(field_id: int, user_email: str, db: Session) -> Field:
    field = db.query(Field).filter(Field.id == field_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Поле не найдено")
    owner = db.query(User).filter(User.email == user_email).first()
    if not owner or field.user_id != owner.id:
        raise HTTPException(status_code=403, detail="Доступ к данному полю запрещён")
    return field


def _safe(value, default: float = 0.0):
    return value if value is not None else default


class AirQualityService:

    @staticmethod
    async def get_current(field_id: int, user_email: str, db: Session) -> AirQualityCurrentResponse:
        redis = await get_redis()
        cache_key = f"agro_weather:aq_current:{field_id}"

        try:
            cached = await redis.get(cache_key)
            if cached:
                logger.info(f"Кэш качества воздуха (текущее) для поля {field_id}")
                return AirQualityCurrentResponse(**json.loads(cached))
        except Exception as e:
            logger.error(f"Redis ошибка (aq_current, чтение): {e}")

        field = _get_field_for_user(field_id, user_email, db)

        try:
            async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
                response = await client.get(_AQ_URL, params={
                    "latitude": field.latitude,
                    "longitude": field.longitude,
                    "current": _CURRENT_PARAMS,
                    "timezone": "auto",
                })

            if response.status_code == 200:
                c = response.json()["current"]

                pm10   = float(_safe(c.get("pm10")))
                pm2_5  = float(_safe(c.get("pm2_5")))
                dust   = float(_safe(c.get("dust")))
                eaqi   = int(_safe(c.get("european_aqi")))
                us_aqi = int(_safe(c.get("us_aqi")))
                uv     = float(_safe(c.get("uv_index")))
                no2    = float(_safe(c.get("nitrogen_dioxide")))
                ozone  = float(_safe(c.get("ozone")))

                warnings = AgroAnalyzer.analyze_air_quality(pm10, pm2_5, dust, eaqi)
                spraying_safe = eaqi < 25 and pm10 < 25

                result = AirQualityCurrentResponse(
                    pm10_ugm3=round(pm10, 1),
                    pm2_5_ugm3=round(pm2_5, 1),
                    dust_ugm3=round(dust, 1),
                    european_aqi=eaqi,
                    us_aqi=us_aqi,
                    uv_index=round(uv, 1),
                    nitrogen_dioxide_ugm3=round(no2, 1),
                    ozone_ugm3=round(ozone, 1),
                    spraying_safe=spraying_safe,
                    warnings=warnings,
                    fetched_at=c["time"],
                )

                try:
                    await redis.setex(cache_key, _CACHE_TTL, result.model_dump_json())
                except Exception as e:
                    logger.error(f"Redis ошибка (aq_current, запись): {e}")

                logger.info(f"Качество воздуха (текущее) получено для поля {field_id}")
                return result

            logger.warning(f"Air Quality API вернул {response.status_code} для поля {field_id}")

        except Exception as e:
            logger.error(f"Ошибка запроса Air Quality API (current) для поля {field_id}: {e}")

        raise HTTPException(status_code=503, detail="Данные о качестве воздуха временно недоступны")

    @staticmethod
    async def get_forecast(field_id: int, user_email: str, db: Session) -> AirQualityForecastResponse:
        redis = await get_redis()
        cache_key = f"agro_weather:aq_forecast:{field_id}"

        cached_raw: str | None = None
        try:
            cached_raw = await redis.get(cache_key)
            if cached_raw:
                logger.info(f"Кэш прогноза качества воздуха для поля {field_id}")
                return AirQualityForecastResponse(**json.loads(cached_raw))
        except Exception as e:
            logger.error(f"Redis ошибка (aq_forecast, чтение): {e}")
            cached_raw = None

        field = _get_field_for_user(field_id, user_email, db)

        try:
            async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
                response = await client.get(_AQ_URL, params={
                    "latitude": field.latitude,
                    "longitude": field.longitude,
                    "hourly": _HOURLY_PARAMS,
                    "timezone": "auto",
                    "forecast_days": 5,
                })

            if response.status_code == 200:
                hourly = response.json()["hourly"]
                times   = hourly["time"]
                pm10s   = hourly["pm10"]
                pm25s   = hourly["pm2_5"]
                dusts   = hourly["dust"]
                eaqis   = hourly["european_aqi"]
                usaqis  = hourly["us_aqi"]
                total   = len(times)

                forecasts: list[AirQualityForecastDaily] = []
                for i in range(5):
                    s = i * 24
                    e = min(s + 24, total)
                    if s >= total or e - s == 0:
                        break

                    max_pm10  = max(pm10s[s:e])
                    max_pm25  = max(pm25s[s:e])
                    max_dust  = max(dusts[s:e])
                    max_eaqi  = max(eaqis[s:e])
                    max_usaqi = max(usaqis[s:e])

                    warnings = AgroAnalyzer.analyze_air_quality(max_pm10, max_pm25, max_dust, max_eaqi)

                    forecasts.append(AirQualityForecastDaily(
                        date=times[s].split("T")[0],
                        pm10_max_ugm3=round(max_pm10, 1),
                        pm2_5_max_ugm3=round(max_pm25, 1),
                        dust_max_ugm3=round(max_dust, 1),
                        european_aqi_max=max_eaqi,
                        us_aqi_max=max_usaqi,
                        warnings=warnings,
                    ))

                result = AirQualityForecastResponse(field_id=field_id, forecast=forecasts)

                try:
                    await redis.setex(cache_key, _CACHE_TTL, result.model_dump_json())
                except Exception as e:
                    logger.error(f"Redis ошибка (aq_forecast, запись): {e}")

                return result

            logger.warning(f"Air Quality API вернул {response.status_code} для прогноза поля {field_id}")

        except Exception as e:
            logger.error(f"Ошибка запроса Air Quality API (forecast) для поля {field_id}: {e}")

        if cached_raw:
            try:
                return AirQualityForecastResponse(**json.loads(cached_raw))
            except Exception as e:
                logger.error(f"Ошибка десериализации stale-кэша AQ: {e}")

        raise HTTPException(status_code=503, detail="Прогноз качества воздуха временно недоступен")

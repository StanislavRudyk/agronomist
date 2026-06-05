import json
import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.logging_config import logger
from backend.modeles.models import Field, User
from backend.modeles.schemas import FloodForecastResponse, FloodForecastDaily
from backend.modeles.redis_client import get_redis
from backend.services.agro_analyzer import AgroAnalyzer

_FLOOD_URL = "https://flood-api.open-meteo.com/v1/flood"
_HTTP_TIMEOUT = httpx.Timeout(connect=3.0, read=10.0, write=5.0, pool=5.0)
_CACHE_TTL = 3600
_DAILY_PARAMS = "river_discharge,river_discharge_max,river_discharge_min"


def _get_field_for_user(field_id: int, user_email: str, db: Session) -> Field:
    field = db.query(Field).filter(Field.id == field_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Поле не найдено")
    owner = db.query(User).filter(User.email == user_email).first()
    if not owner or field.user_id != owner.id:
        raise HTTPException(status_code=403, detail="Доступ к данному полю запрещён")
    return field


class FloodService:

    @staticmethod
    async def get_forecast(field_id: int, user_email: str, db: Session) -> FloodForecastResponse:
        redis = await get_redis()
        cache_key = f"agro_weather:flood:{field_id}"

        cached_raw: str | None = None
        try:
            cached_raw = await redis.get(cache_key)
            if cached_raw:
                logger.info(f"Кэш прогноза паводка для поля {field_id}")
                return FloodForecastResponse(**json.loads(cached_raw))
        except Exception as e:
            logger.error(f"Redis ошибка (flood, чтение): {e}")
            cached_raw = None

        field = _get_field_for_user(field_id, user_email, db)

        try:
            async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
                response = await client.get(_FLOOD_URL, params={
                    "latitude": field.latitude,
                    "longitude": field.longitude,
                    "daily": _DAILY_PARAMS,
                    "forecast_days": 7,
                })

            if response.status_code == 200:
                daily = response.json()["daily"]
                times     = daily["time"]
                discharge = daily["river_discharge"]
                d_max     = daily["river_discharge_max"]
                d_min     = daily["river_discharge_min"]

                forecasts: list[FloodForecastDaily] = []
                for i, date in enumerate(times):
                    warnings = AgroAnalyzer.analyze_flood(d_max[i])
                    forecasts.append(FloodForecastDaily(
                        date=date,
                        river_discharge_m3s=discharge[i],
                        river_discharge_max_m3s=d_max[i],
                        river_discharge_min_m3s=d_min[i],
                        warnings=warnings,
                    ))

                result = FloodForecastResponse(field_id=field_id, forecast=forecasts)

                try:
                    await redis.setex(cache_key, _CACHE_TTL, result.model_dump_json())
                except Exception as e:
                    logger.error(f"Redis ошибка (flood, запись): {e}")

                logger.info(f"Прогноз паводка получен для поля {field_id}")
                return result

            logger.warning(f"Flood API вернул {response.status_code} для поля {field_id}")

        except Exception as e:
            logger.error(f"Ошибка запроса Flood API для поля {field_id}: {e}")

        if cached_raw:
            try:
                return FloodForecastResponse(**json.loads(cached_raw))
            except Exception as e:
                logger.error(f"Ошибка десериализации stale-кэша flood: {e}")

        raise HTTPException(status_code=503, detail="Прогноз паводка временно недоступен")

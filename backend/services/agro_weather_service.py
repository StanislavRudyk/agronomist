import json
import httpx
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.logging_config import logger
from backend.modeles.models import Field, AgroWeatherData, User
from backend.modeles.schemas import (
    AgroWeatherCurrentResponse,
    AgroWeatherForecastResponse,
    AgroWeatherForecastDaily,
    SoilTemperatures,
    SoilMoistures,
    WindData,
)
from backend.modeles.redis_client import get_redis
from backend.services.agro_analyzer import AgroAnalyzer

_OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
_HTTP_TIMEOUT = httpx.Timeout(connect=3.0, read=10.0, write=5.0, pool=5.0)
_CACHE_TTL = 3600

_CURRENT_PARAMS = ",".join([
    "temperature_2m",
    "apparent_temperature",
    "relative_humidity_2m",
    "vapour_pressure_deficit",
    "precipitation",
    "rain",
    "showers",
    "snowfall",
    "snow_depth",
    "weather_code",
    "cloud_cover",
    "pressure_msl",
    "surface_pressure",
    "wind_speed_10m",
    "wind_direction_10m",
    "wind_gusts_10m",
    "soil_temperature_0cm",
    "soil_temperature_6cm",
    "soil_temperature_18cm",
    "soil_temperature_54cm",
    "soil_moisture_0_to_1cm",
    "soil_moisture_1_to_3cm",
    "soil_moisture_3_to_9cm",
    "soil_moisture_9_to_27cm",
    "soil_moisture_27_to_81cm",
    "sunshine_duration",
    "shortwave_radiation",
    "direct_radiation",
    "diffuse_radiation",
    "direct_normal_irradiance",
    "dew_point_2m",
    "is_day",
])

_DAILY_PARAMS = ",".join([
    "temperature_2m_max",
    "temperature_2m_min",
    "apparent_temperature_max",
    "apparent_temperature_min",
    "sunrise",
    "sunset",
    "daylight_duration",
    "sunshine_duration",
    "uv_index_max",
    "precipitation_sum",
    "rain_sum",
    "showers_sum",
    "snowfall_sum",
    "precipitation_hours",
    "precipitation_probability_max",
    "wind_speed_10m_max",
    "wind_gusts_10m_max",
    "wind_direction_10m_dominant",
    "shortwave_radiation_sum",
    "et0_fao_evapotranspiration",
])

_HOURLY_PARAMS = ",".join([
    "temperature_2m",
    "relative_humidity_2m",
    "vapour_pressure_deficit",
    "precipitation",
    "precipitation_probability",
    "snow_depth",
    "wind_speed_10m",
    "wind_direction_10m",
    "wind_gusts_10m",
    "cloud_cover",
    "visibility",
    "shortwave_radiation",
    "evapotranspiration",
    "et0_fao_evapotranspiration",
    "uv_index",
    "uv_index_clear_sky",
    "soil_temperature_0cm",
    "soil_temperature_6cm",
    "soil_temperature_18cm",
    "soil_temperature_54cm",
    "soil_moisture_0_to_1cm",
    "soil_moisture_1_to_3cm",
    "soil_moisture_3_to_9cm",
    "soil_moisture_9_to_27cm",
    "soil_moisture_27_to_81cm",
])


def _get_field_for_user(field_id: int, user_email: str, db: Session) -> Field:
    field = db.query(Field).filter(Field.id == field_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Поле не найдено")
    owner = db.query(User).filter(User.email == user_email).first()
    if not owner or field.user_id != owner.id:
        raise HTTPException(status_code=403, detail="Доступ к данному полю запрещён")
    return field


def _resolve_current_visibility(body: dict) -> float:
    try:
        current_time = body["current"]["time"]
        times = body["hourly"]["time"]
        visibilities = body["hourly"]["visibility"]
        hour_prefix = current_time[:13]
        idx = next((i for i, t in enumerate(times) if t.startswith(hour_prefix)), 0)
        return float(visibilities[idx]) if idx < len(visibilities) else 99999.0
    except Exception:
        return 99999.0




def _safe(value, default=0.0):
    return value if value is not None else default


class AgroWeatherService:

    @staticmethod
    async def get_current_weather(field_id: int, user_email: str, db: Session) -> AgroWeatherCurrentResponse:
        redis = await get_redis()
        cache_key = f"agro_weather:current:{field_id}"

        try:
            cached = await redis.get(cache_key)
            if cached:
                logger.info(f"Кэш текущей агро-погоды для поля {field_id}")
                data = json.loads(cached)
                data["fetched_at"] = datetime.fromisoformat(data["fetched_at"])
                data["wind"] = WindData(**data["wind"])
                data["soil_temperatures"] = SoilTemperatures(**data["soil_temperatures"])
                data["soil_moistures"] = SoilMoistures(**data["soil_moistures"])
                return AgroWeatherCurrentResponse(**data)
        except Exception as e:
            logger.error(f"Redis ошибка (current, чтение): {e}")

        field = _get_field_for_user(field_id, user_email, db)

        params = {
            "latitude": field.latitude,
            "longitude": field.longitude,
            "current": _CURRENT_PARAMS,
            "hourly": "visibility",
            "forecast_days": 1,
            "timezone": "auto",
        }

        try:
            async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
                response = await client.get(_OPEN_METEO_URL, params=params)

            if response.status_code == 200:
                c = response.json()["current"]

                air_temp        = float(_safe(c.get("temperature_2m")))
                apparent_temp   = float(_safe(c.get("apparent_temperature")))
                humidity        = int(_safe(c.get("relative_humidity_2m")))
                vpd             = float(_safe(c.get("vapour_pressure_deficit")))
                precip          = float(_safe(c.get("precipitation")))
                rain            = float(_safe(c.get("rain")))
                showers         = float(_safe(c.get("showers")))
                snowfall        = float(_safe(c.get("snowfall")))
                snow_depth      = float(_safe(c.get("snow_depth")))
                weather_code    = int(_safe(c.get("weather_code")))
                cloud_cover     = int(_safe(c.get("cloud_cover")))
                pressure_msl    = float(_safe(c.get("pressure_msl")))
                surface_pressure= float(_safe(c.get("surface_pressure")))
                wind_speed      = float(_safe(c.get("wind_speed_10m")))
                wind_dir        = float(_safe(c.get("wind_direction_10m")))
                wind_gusts      = float(_safe(c.get("wind_gusts_10m")))
                soil_t0         = float(_safe(c.get("soil_temperature_0cm")))
                soil_t6         = float(_safe(c.get("soil_temperature_6cm")))
                soil_t18        = float(_safe(c.get("soil_temperature_18cm")))
                soil_t54        = float(_safe(c.get("soil_temperature_54cm")))
                sm_0_1          = float(_safe(c.get("soil_moisture_0_to_1cm")))
                sm_1_3          = float(_safe(c.get("soil_moisture_1_to_3cm")))
                sm_3_9          = float(_safe(c.get("soil_moisture_3_to_9cm")))
                sm_9_27         = float(_safe(c.get("soil_moisture_9_to_27cm")))
                sm_27_81        = float(_safe(c.get("soil_moisture_27_to_81cm")))
                sunshine        = float(_safe(c.get("sunshine_duration")))
                sw_rad          = float(_safe(c.get("shortwave_radiation")))
                dir_rad         = float(_safe(c.get("direct_radiation")))
                diff_rad        = float(_safe(c.get("diffuse_radiation")))
                dir_norm_rad    = float(_safe(c.get("direct_normal_irradiance")))
                dew_point       = float(_safe(c.get("dew_point_2m")))
                is_day          = bool(_safe(c.get("is_day")))

                warnings = AgroAnalyzer.analyze(
                    crop_type=field.crop_type,
                    air_temp=air_temp,
                    soil_temp=soil_t6,
                    soil_moisture=sm_3_9,
                    snow_depth=snow_depth,
                    wind_speed=wind_speed,
                    wind_gusts=wind_gusts,
                    relative_humidity=float(humidity),
                    vpd=vpd,
                    dew_point=dew_point,
                )

                db_entry = AgroWeatherData(
                    field_id=field_id,
                    air_temp=air_temp,
                    apparent_temp=apparent_temp,
                    dew_point=dew_point,
                    relative_humidity=humidity,
                    vapour_pressure_deficit=vpd,
                    precipitation=precip,
                    rain=rain,
                    showers=showers,
                    snowfall=snowfall,
                    snow_depth=snow_depth,
                    weather_code=weather_code,
                    cloud_cover=cloud_cover,
                    pressure_msl=pressure_msl,
                    surface_pressure=surface_pressure,
                    wind_speed=wind_speed,
                    wind_direction=wind_dir,
                    wind_gusts=wind_gusts,
                    soil_temp_0cm=soil_t0,
                    soil_temp_6cm=soil_t6,
                    soil_temp_18cm=soil_t18,
                    soil_temp_54cm=soil_t54,
                    soil_moisture_0_1cm=sm_0_1,
                    soil_moisture_1_3cm=sm_1_3,
                    soil_moisture_3_9cm=sm_3_9,
                    soil_moisture_9_27cm=sm_9_27,
                    soil_moisture_27_81cm=sm_27_81,
                    sunshine_duration=sunshine,
                    shortwave_radiation=sw_rad,
                    direct_radiation=dir_rad,
                    diffuse_radiation=diff_rad,
                    is_day=int(is_day),
                    warnings=json.dumps(warnings, ensure_ascii=False),
                )
                db.add(db_entry)
                db.commit()
                db.refresh(db_entry)

                result = AgroWeatherCurrentResponse(
                    air_temp=air_temp,
                    apparent_temp=apparent_temp,
                    dew_point_c=dew_point,
                    relative_humidity=humidity,
                    vapour_pressure_deficit_kpa=vpd,
                    precipitation_mm=precip,
                    rain_mm=rain,
                    showers_mm=showers,
                    snowfall_cm=snowfall,
                    snow_depth_m=snow_depth,
                    weather_code=weather_code,
                    cloud_cover_pct=cloud_cover,
                    pressure_msl_hpa=pressure_msl,
                    surface_pressure_hpa=surface_pressure,
                    visibility_m=_resolve_current_visibility(response.json()),
                    wind=WindData(speed_kmh=wind_speed, direction_deg=wind_dir, gusts_kmh=wind_gusts),
                    soil_temperatures=SoilTemperatures(
                        surface_0cm=soil_t0,
                        depth_6cm=soil_t6,
                        depth_18cm=soil_t18,
                        depth_54cm=soil_t54,
                    ),
                    soil_moistures=SoilMoistures(
                        layer_0_1cm=sm_0_1,
                        layer_1_3cm=sm_1_3,
                        layer_3_9cm=sm_3_9,
                        layer_9_27cm=sm_9_27,
                        layer_27_81cm=sm_27_81,
                    ),
                    sunshine_duration_s=sunshine,
                    radiation=RadiationData(
                        shortwave_wm2=sw_rad,
                        direct_wm2=dir_rad,
                        diffuse_wm2=diff_rad,
                        direct_normal_wm2=dir_norm_rad,
                    ),
                    is_day=is_day,
                    warnings=warnings,
                    fetched_at=db_entry.created_at,
                )

                try:
                    cache_data = result.model_dump()
                    cache_data["fetched_at"] = cache_data["fetched_at"].isoformat()
                    await redis.setex(cache_key, _CACHE_TTL, json.dumps(cache_data, ensure_ascii=False, default=str))
                except Exception as e:
                    logger.error(f"Redis ошибка (current, запись): {e}")

                logger.info(f"Текущая агро-погода получена для поля {field_id}")
                return result

            logger.warning(f"Open-Meteo вернул {response.status_code} для поля {field_id}")

        except Exception as e:
            logger.error(f"Ошибка запроса Open-Meteo (current) для поля {field_id}: {e}")

        logger.info(f"Попытка offline-данных для поля {field_id}")
        db_offline = (
            db.query(AgroWeatherData)
            .filter(AgroWeatherData.field_id == field_id)
            .order_by(desc(AgroWeatherData.created_at))
            .first()
        )

        if db_offline:
            logger.info(f"Offline агро-данные отданы для поля {field_id}")
            return AgroWeatherCurrentResponse(
                air_temp=_safe(db_offline.air_temp),
                apparent_temp=_safe(db_offline.apparent_temp),
                dew_point_c=_safe(db_offline.dew_point),
                relative_humidity=int(_safe(db_offline.relative_humidity)),
                vapour_pressure_deficit_kpa=_safe(db_offline.vapour_pressure_deficit),
                precipitation_mm=_safe(db_offline.precipitation),
                rain_mm=_safe(db_offline.rain),
                showers_mm=_safe(db_offline.showers),
                snowfall_cm=_safe(db_offline.snowfall),
                snow_depth_m=_safe(db_offline.snow_depth),
                weather_code=int(_safe(db_offline.weather_code)),
                cloud_cover_pct=int(_safe(db_offline.cloud_cover)),
                pressure_msl_hpa=_safe(db_offline.pressure_msl),
                surface_pressure_hpa=_safe(db_offline.surface_pressure),
                visibility_m=_safe(db_offline.visibility, 99999.0),
                wind=WindData(
                    speed_kmh=_safe(db_offline.wind_speed),
                    direction_deg=_safe(db_offline.wind_direction),
                    gusts_kmh=_safe(db_offline.wind_gusts),
                ),
                soil_temperatures=SoilTemperatures(
                    surface_0cm=_safe(db_offline.soil_temp_0cm),
                    depth_6cm=_safe(db_offline.soil_temp_6cm),
                    depth_18cm=_safe(db_offline.soil_temp_18cm),
                    depth_54cm=_safe(db_offline.soil_temp_54cm),
                ),
                soil_moistures=SoilMoistures(
                    layer_0_1cm=_safe(db_offline.soil_moisture_0_1cm),
                    layer_1_3cm=_safe(db_offline.soil_moisture_1_3cm),
                    layer_3_9cm=_safe(db_offline.soil_moisture_3_9cm),
                    layer_9_27cm=_safe(db_offline.soil_moisture_9_27cm),
                    layer_27_81cm=_safe(db_offline.soil_moisture_27_81cm),
                ),
                sunshine_duration_s=_safe(db_offline.sunshine_duration),
                radiation=RadiationData(
                    shortwave_wm2=_safe(db_offline.shortwave_radiation),
                    direct_wm2=_safe(db_offline.direct_radiation),
                    diffuse_wm2=_safe(db_offline.diffuse_radiation),
                    direct_normal_wm2=_safe(db_offline.shortwave_radiation), # offline fallback approximation
                ),
                is_day=bool(db_offline.is_day),
                warnings=json.loads(db_offline.warnings) if db_offline.warnings else [],
                fetched_at=db_offline.created_at,
            )

        raise HTTPException(
            status_code=404,
            detail="Данные о погоде для поля недоступны (offline режим пуст)",
        )

    @staticmethod
    async def get_forecast_weather(field_id: int, user_email: str, db: Session) -> AgroWeatherForecastResponse:
        redis = await get_redis()
        cache_key = f"agro_weather:forecast:{field_id}"

        cached_raw: str | None = None
        try:
            cached_raw = await redis.get(cache_key)
            if cached_raw:
                logger.info(f"Кэш прогноза агро-погоды для поля {field_id}")
                return AgroWeatherForecastResponse(**json.loads(cached_raw))
        except Exception as e:
            logger.error(f"Redis ошибка (forecast, чтение): {e}")
            cached_raw = None

        field = _get_field_for_user(field_id, user_email, db)

        params = {
            "latitude": field.latitude,
            "longitude": field.longitude,
            "daily": _DAILY_PARAMS,
            "hourly": _HOURLY_PARAMS,
            "timezone": "auto",
        }

        try:
            async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
                response = await client.get(_OPEN_METEO_URL, params=params)

            if response.status_code == 200:
                body = response.json()
                daily = body["daily"]
                hourly = body["hourly"]

                h_temps        = hourly["temperature_2m"]
                h_humidity     = hourly["relative_humidity_2m"]
                h_vpd          = hourly["vapour_pressure_deficit"]
                h_precip       = hourly["precipitation"]
                h_snow         = hourly["snow_depth"]
                h_wind_speed   = hourly["wind_speed_10m"]
                h_wind_gusts   = hourly["wind_gusts_10m"]
                h_soil_t6      = hourly["soil_temperature_6cm"]
                h_sm_0_1       = hourly["soil_moisture_0_to_1cm"]
                h_sm_3_9       = hourly["soil_moisture_3_to_9cm"]
                h_visibility   = hourly["visibility"]
                h_et0          = hourly["et0_fao_evapotranspiration"]
                h_uv           = hourly["uv_index"]
                total_hours    = len(h_temps)

                forecasts: list[AgroWeatherForecastDaily] = []

                for i in range(min(7, len(daily["time"]))):
                    h_start = i * 24
                    h_end   = min(h_start + 24, total_hours)
                    hrs     = h_end - h_start
                    if hrs == 0:
                        break

                    slice_temps    = h_temps[h_start:h_end]
                    slice_humidity = h_humidity[h_start:h_end]
                    slice_vpd      = h_vpd[h_start:h_end]
                    slice_precip   = h_precip[h_start:h_end]
                    slice_snow     = h_snow[h_start:h_end]
                    slice_w_speed  = h_wind_speed[h_start:h_end]
                    slice_w_gusts  = h_wind_gusts[h_start:h_end]
                    slice_soil_t6  = h_soil_t6[h_start:h_end]
                    slice_sm_3_9   = h_sm_3_9[h_start:h_end]
                    slice_vis      = h_visibility[h_start:h_end]
                    slice_et0      = h_et0[h_start:h_end]
                    slice_uv       = h_uv[h_start:h_end]

                    min_temp        = min(slice_temps)
                    mean_soil_t6    = sum(slice_soil_t6) / hrs
                    mean_sm_3_9     = sum(slice_sm_3_9) / hrs
                    mean_snow       = sum(slice_snow) / hrs
                    max_wind        = max(slice_w_speed)
                    max_gusts       = max(slice_w_gusts)
                    max_humidity    = max(slice_humidity)
                    day_et0         = daily["et0_fao_evapotranspiration"][i]
                    max_uv          = daily["uv_index_max"][i]
                    min_vis         = min(slice_vis)
                    max_vpd         = max(slice_vpd)

                    future_end      = min(h_start + 120, total_hours)
                    avail           = future_end - h_start
                    precip_5d_raw   = sum(h_precip[h_start:future_end])
                    precip_5days    = (precip_5d_raw / avail * 120) if avail > 0 else 0.0

                    warnings = AgroAnalyzer.analyze(
                        crop_type=field.crop_type,
                        air_temp=min_temp,
                        soil_temp=mean_soil_t6,
                        soil_moisture=mean_sm_3_9,
                        snow_depth=mean_snow,
                        precip_5days=precip_5days,
                        wind_speed=max_wind,
                        wind_gusts=max_gusts,
                        relative_humidity=float(max_humidity),
                        et0=day_et0,
                        uv_index_max=max_uv,
                        visibility=min_vis,
                        vpd=max_vpd,
                    )

                    forecasts.append(AgroWeatherForecastDaily(
                        date=daily["time"][i],
                        sunrise=daily["sunrise"][i],
                        sunset=daily["sunset"][i],
                        daylight_duration_s=float(_safe(daily["daylight_duration"][i])),
                        sunshine_duration_s=float(_safe(daily["sunshine_duration"][i])),
                        max_temp=round(daily["temperature_2m_max"][i], 1),
                        min_temp=round(daily["temperature_2m_min"][i], 1),
                        apparent_temp_max=round(daily["apparent_temperature_max"][i], 1),
                        apparent_temp_min=round(daily["apparent_temperature_min"][i], 1),
                        precipitation_sum_mm=round(_safe(daily["precipitation_sum"][i]), 1),
                        rain_sum_mm=round(_safe(daily["rain_sum"][i]), 1),
                        showers_sum_mm=round(_safe(daily["showers_sum"][i]), 1),
                        snowfall_sum_cm=round(_safe(daily["snowfall_sum"][i]), 1),
                        precipitation_hours=float(_safe(daily["precipitation_hours"][i])),
                        precipitation_probability_max=int(_safe(daily["precipitation_probability_max"][i])),
                        wind_speed_max_kmh=round(_safe(daily["wind_speed_10m_max"][i]), 1),
                        wind_gusts_max_kmh=round(_safe(daily["wind_gusts_10m_max"][i]), 1),
                        wind_direction_dominant_deg=int(_safe(daily["wind_direction_10m_dominant"][i])),
                        shortwave_radiation_sum_mjm2=round(_safe(daily["shortwave_radiation_sum"][i]), 2),
                        et0_fao_mm=round(day_et0, 2),
                        uv_index_max=round(max_uv, 1),
                        warnings=warnings,
                    ))

                result = AgroWeatherForecastResponse(
                    field_id=field_id,
                    crop_type=field.crop_type,
                    forecast=forecasts,
                )

                try:
                    await redis.setex(cache_key, _CACHE_TTL, result.model_dump_json())
                except Exception as e:
                    logger.error(f"Redis ошибка (forecast, запись): {e}")

                return result

            logger.warning(f"Open-Meteo вернул {response.status_code} для прогноза поля {field_id}")

        except Exception as e:
            logger.error(f"Ошибка запроса Open-Meteo (forecast) для поля {field_id}: {e}")

        if cached_raw:
            logger.info(f"Stale-кэш прогноза для поля {field_id} из-за недоступности API")
            try:
                return AgroWeatherForecastResponse(**json.loads(cached_raw))
            except Exception as e:
                logger.error(f"Ошибка десериализации stale-кэша прогноза: {e}")

        raise HTTPException(
            status_code=503,
            detail="Прогноз погоды временно недоступен (Open-Meteo недоступен)",
        )

import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator


class UserCreate(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Пароль должен содержать минимум 8 символов")
        if len(v) > 128:
            raise ValueError("Пароль не может превышать 128 символов")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Пароль должен содержать хотя бы одну заглавную букву")
        if not re.search(r"[a-z]", v):
            raise ValueError("Пароль должен содержать хотя бы одну строчную букву")
        if not re.search(r"\d", v):
            raise ValueError("Пароль должен содержать хотя бы одну цифру")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Пароль должен содержать хотя бы один специальный символ (!@#$%^&* и т.д.)")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class MessageResponse(BaseModel):
    detail: str


class WeatherBase(BaseModel):
    city: str
    temperature: str
    feels_like: str | None = None
    humidity: int | None = None
    wind_speed: str | None = None
    description: str | None = None
    forecast_time: datetime


class WeatherResponse(WeatherBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class FieldCreate(BaseModel):
    name: str
    latitude: float
    longitude: float
    crop_type: str

class FieldResponse(BaseModel):
    id: int
    user_id: int
    name: str
    latitude: float
    longitude: float
    crop_type: str
    created_at: datetime

    class Config:
        from_attributes = True

class SoilTemperatures(BaseModel):
    surface_0cm: float
    depth_6cm: float
    depth_18cm: float
    depth_54cm: float

class SoilMoistures(BaseModel):
    layer_0_1cm: float
    layer_1_3cm: float
    layer_3_9cm: float
    layer_9_27cm: float
    layer_27_81cm: float

class WindData(BaseModel):
    speed_kmh: float
    direction_deg: float
    gusts_kmh: float

class RadiationData(BaseModel):
    shortwave_wm2: float
    direct_wm2: float
    diffuse_wm2: float
    direct_normal_wm2: float

class AgroWeatherCurrentResponse(BaseModel):
    air_temp: float
    apparent_temp: float
    dew_point_c: float
    relative_humidity: int
    vapour_pressure_deficit_kpa: float
    precipitation_mm: float
    rain_mm: float
    showers_mm: float
    snowfall_cm: float
    snow_depth_m: float
    weather_code: int
    cloud_cover_pct: int
    pressure_msl_hpa: float
    surface_pressure_hpa: float
    visibility_m: float
    wind: WindData
    soil_temperatures: SoilTemperatures
    soil_moistures: SoilMoistures
    sunshine_duration_s: float
    radiation: RadiationData
    is_day: bool
    warnings: list[str]
    fetched_at: datetime

    class Config:
        from_attributes = True

class AgroWeatherForecastDaily(BaseModel):
    date: str
    sunrise: str
    sunset: str
    daylight_duration_s: float
    sunshine_duration_s: float
    max_temp: float
    min_temp: float
    apparent_temp_max: float
    apparent_temp_min: float
    precipitation_sum_mm: float
    rain_sum_mm: float
    showers_sum_mm: float
    snowfall_sum_cm: float
    precipitation_hours: float
    precipitation_probability_max: int
    wind_speed_max_kmh: float
    wind_gusts_max_kmh: float
    wind_direction_dominant_deg: int
    shortwave_radiation_sum_mjm2: float
    et0_fao_mm: float
    uv_index_max: float
    warnings: list[str]

class AgroWeatherForecastResponse(BaseModel):
    field_id: int
    crop_type: str
    forecast: list[AgroWeatherForecastDaily]


class AirQualityCurrentResponse(BaseModel):
    pm10_ugm3: float
    pm2_5_ugm3: float
    dust_ugm3: float
    european_aqi: int
    us_aqi: int
    uv_index: float
    nitrogen_dioxide_ugm3: float
    ozone_ugm3: float
    spraying_safe: bool
    warnings: list[str]
    fetched_at: str

class AirQualityForecastDaily(BaseModel):
    date: str
    pm10_max_ugm3: float
    pm2_5_max_ugm3: float
    dust_max_ugm3: float
    european_aqi_max: int
    us_aqi_max: int
    warnings: list[str]

class AirQualityForecastResponse(BaseModel):
    field_id: int
    forecast: list[AirQualityForecastDaily]


class FloodForecastDaily(BaseModel):
    date: str
    river_discharge_m3s: float | None
    river_discharge_max_m3s: float | None
    river_discharge_min_m3s: float | None
    warnings: list[str]

class FloodForecastResponse(BaseModel):
    field_id: int
    forecast: list[FloodForecastDaily]

class SeedingRateRequest(BaseModel):
    target_density_mln_ha: float
    weight_1000_seeds_g: float
    germination_percent: float
    purity_percent: float
    field_area_ha: float

    @field_validator("germination_percent", "purity_percent")
    @classmethod
    def check_percents(cls, v: float) -> float:
        if not (0 < v <= 100):
            raise ValueError("Процент должен быть от 0.1 до 100")
        return v

class SeedingRateResponse(BaseModel):
    seeding_rate_kg_ha: float
    total_seeds_kg: float

class SprayingRequest(BaseModel):
    tank_volume_l: float
    water_rate_l_ha: float
    chemical_rate_per_ha: float
    field_area_ha: float

class SprayingResponse(BaseModel):
    area_per_tank_ha: float
    chemical_per_tank: float
    total_water_l: float
    total_chemical: float
    tanks_needed: float

class FertilizerRequest(BaseModel):
    crop_type: str
    target_yield_t_ha: float

class FertilizerResponse(BaseModel):
    nitrogen_kg_ha: float
    phosphorus_kg_ha: float
    potassium_kg_ha: float


# -------------------------------------------------------------------
# Схемы для Мониторинга Техники и ГСМ
# -------------------------------------------------------------------

class MachineryCreate(BaseModel):
    name: str
    type: str
    license_plate: str | None = None
    fuel_capacity_l: float
    maintenance_interval_h: float = 250.0

class MachineryResponse(MachineryCreate):
    id: int
    user_id: int
    current_fuel_l: float
    moto_hours: float
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class ImplementCreate(BaseModel):
    name: str
    type: str
    width_m: float

class ImplementResponse(ImplementCreate):
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class FuelLogCreate(BaseModel):
    machinery_id: int
    log_type: str # REFILL, DRAIN, USAGE
    amount_l: float
    description: str | None = None

class FuelLogResponse(FuelLogCreate):
    id: int
    date: datetime
    
    class Config:
        from_attributes = True

class WorkOrderCreate(BaseModel):
    machinery_id: int
    implement_id: int | None = None
    field_id: int
    operation: str
    area_ha: float
    duration_h: float
    avg_speed_kmh: float | None = None
    fuel_used_l: float
    fuel_norm_l_ha: float # Будет умножаться на площадь

class WorkOrderResponse(BaseModel):
    id: int
    user_id: int
    machinery_id: int
    implement_id: int | None
    field_id: int
    operation: str
    area_ha: float
    duration_h: float
    avg_speed_kmh: float | None
    speed_violation: bool
    fuel_used_l: float
    fuel_norm_l: float
    date: datetime
    
    class Config:
        from_attributes = True

class MaintenanceLogCreate(BaseModel):
    machinery_id: int
    moto_hours_at_maintenance: float
    description: str
    cost: float = 0.0

class MaintenanceLogResponse(MaintenanceLogCreate):
    id: int
    date: datetime
    
    class Config:
        from_attributes = True



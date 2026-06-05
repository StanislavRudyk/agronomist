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

class AgroWeatherCurrentResponse(BaseModel):
    air_temp: float
    soil_temp: float
    soil_moisture: float
    warnings: list[str]
    fetched_at: datetime

    class Config:
        from_attributes = True

class AgroWeatherForecastDaily(BaseModel):
    date: str
    max_temp: float
    min_temp: float
    precipitation: float
    warnings: list[str]

class AgroWeatherForecastResponse(BaseModel):
    field_id: int
    crop_type: str
    forecast: list[AgroWeatherForecastDaily]

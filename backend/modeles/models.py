from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class WeatherData(Base):
    __tablename__ = "weather_data"
    id = Column(Integer, primary_key=True, index=True)
    city = Column(String, index=True, nullable=False)
    temperature = Column(String, nullable=False)
    feels_like = Column(String)
    humidity = Column(Integer)
    wind_speed = Column(String)
    description = Column(String)
    forecast_time = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Field(Base):
    __tablename__ = "fields"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    crop_type = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AgroWeatherData(Base):
    __tablename__ = "agro_weather_data"
    id = Column(Integer, primary_key=True, index=True)
    field_id = Column(Integer, ForeignKey("fields.id"), nullable=False)
    air_temp = Column(Float, nullable=False)
    soil_temp = Column(Float, nullable=False)
    soil_moisture = Column(Float, nullable=False)
    warnings = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

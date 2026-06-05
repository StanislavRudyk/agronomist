from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text
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
    apparent_temp = Column(Float)
    dew_point = Column(Float)
    relative_humidity = Column(Integer)
    vapour_pressure_deficit = Column(Float)

    precipitation = Column(Float)
    rain = Column(Float)
    showers = Column(Float)
    snowfall = Column(Float)
    snow_depth = Column(Float)

    weather_code = Column(Integer)
    cloud_cover = Column(Integer)
    pressure_msl = Column(Float)
    surface_pressure = Column(Float)
    visibility = Column(Float)
    sunshine_duration = Column(Float)
    shortwave_radiation = Column(Float)
    direct_radiation = Column(Float)
    diffuse_radiation = Column(Float)
    is_day = Column(Integer)

    wind_speed = Column(Float)
    wind_direction = Column(Float)
    wind_gusts = Column(Float)

    soil_temp_0cm = Column(Float)
    soil_temp_6cm = Column(Float)
    soil_temp_18cm = Column(Float)
    soil_temp_54cm = Column(Float)

    soil_moisture_0_1cm = Column(Float)
    soil_moisture_1_3cm = Column(Float)
    soil_moisture_3_9cm = Column(Float)
    soil_moisture_9_27cm = Column(Float)
    soil_moisture_27_81cm = Column(Float)

    warnings = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

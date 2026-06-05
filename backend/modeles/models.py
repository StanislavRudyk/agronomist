from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text, Boolean
from sqlalchemy.sql import func
from datetime import datetime, timezone
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
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

# -------------------------------------------------------------------
# Модели для Мониторинга Техники и ГСМ
# -------------------------------------------------------------------

class Machinery(Base):
    __tablename__ = "machinery"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    license_plate = Column(String)
    fuel_capacity_l = Column(Float, nullable=False)
    current_fuel_l = Column(Float, default=0.0)
    moto_hours = Column(Float, default=0.0)
    maintenance_interval_h = Column(Float, default=250.0)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Implement(Base):
    __tablename__ = "implements"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    width_m = Column(Float, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class FuelLog(Base):
    __tablename__ = "fuel_logs"

    id = Column(Integer, primary_key=True, index=True)
    machinery_id = Column(Integer, ForeignKey("machinery.id", ondelete="CASCADE"), nullable=False)
    log_type = Column(String, nullable=False) # REFILL, DRAIN, USAGE
    amount_l = Column(Float, nullable=False)
    description = Column(String)
    date = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class WorkOrder(Base):
    __tablename__ = "work_orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    machinery_id = Column(Integer, ForeignKey("machinery.id", ondelete="CASCADE"), nullable=False)
    implement_id = Column(Integer, ForeignKey("implements.id", ondelete="SET NULL"), nullable=True)
    field_id = Column(Integer, ForeignKey("fields.id", ondelete="CASCADE"), nullable=False)
    
    operation = Column(String, nullable=False)
    area_ha = Column(Float, nullable=False)
    duration_h = Column(Float, nullable=False)
    avg_speed_kmh = Column(Float)
    speed_violation = Column(Boolean, default=False)
    
    fuel_used_l = Column(Float, nullable=False)
    fuel_norm_l = Column(Float, nullable=False)
    
    date = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class MaintenanceLog(Base):
    __tablename__ = "maintenance_logs"

    id = Column(Integer, primary_key=True, index=True)
    machinery_id = Column(Integer, ForeignKey("machinery.id", ondelete="CASCADE"), nullable=False)
    moto_hours_at_maintenance = Column(Float, nullable=False)
    description = Column(String, nullable=False)
    cost = Column(Float, default=0.0)
    date = Column(DateTime, default=lambda: datetime.now(timezone.utc))

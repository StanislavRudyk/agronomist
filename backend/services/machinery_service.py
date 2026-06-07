from fastapi import HTTPException
from sqlalchemy.orm import Session
from backend.modeles.models import Machinery, Implement, FuelLog, WorkOrder, MaintenanceLog, Field
from backend.modeles.schemas import (
    MachineryCreate,
    ImplementCreate,
    FuelLogCreate,
    WorkOrderCreate,
    MaintenanceLogCreate
)

class MachineryService:

    @staticmethod
    def create_machinery(db: Session, data: MachineryCreate, user_id: int) -> Machinery:
        db_machinery = Machinery(**data.model_dump(), user_id=user_id)
        db.add(db_machinery)
        db.commit()
        db.refresh(db_machinery)
        return db_machinery

    @staticmethod
    def create_implement(db: Session, data: ImplementCreate, user_id: int) -> Implement:
        db_implement = Implement(**data.model_dump(), user_id=user_id)
        db.add(db_implement)
        db.commit()
        db.refresh(db_implement)
        return db_implement

    @staticmethod
    def log_fuel(db: Session, data: FuelLogCreate, user_id: int) -> FuelLog:
        machinery = db.query(Machinery).filter(Machinery.id == data.machinery_id, Machinery.user_id == user_id).first()
        if not machinery:
            raise HTTPException(status_code=404, detail="Техника не найдена")

        if data.log_type.upper() == "REFILL":
            machinery.current_fuel_l += data.amount_l
            if machinery.current_fuel_l > machinery.fuel_capacity_l:
                machinery.current_fuel_l = machinery.fuel_capacity_l
        elif data.log_type.upper() in ["DRAIN", "USAGE"]:
            machinery.current_fuel_l -= data.amount_l
            if machinery.current_fuel_l < 0:
                machinery.current_fuel_l = 0

        fuel_log = FuelLog(**data.model_dump())
        db.add(fuel_log)
        db.commit()
        db.refresh(fuel_log)
        return fuel_log

    @staticmethod
    def create_work_order(db: Session, data: WorkOrderCreate, user_id: int) -> WorkOrder:
        machinery = db.query(Machinery).filter(Machinery.id == data.machinery_id, Machinery.user_id == user_id).first()
        if not machinery:
            raise HTTPException(status_code=404, detail="Техника не найдена")

        field = db.query(Field).filter(Field.id == data.field_id, Field.user_id == user_id).first()
        if not field:
            raise HTTPException(status_code=403, detail="Поле не найдено или нет доступа")

        if data.implement_id is not None:
            implement = db.query(Implement).filter(
                Implement.id == data.implement_id,
                Implement.user_id == user_id,
            ).first()
            if not implement:
                raise HTTPException(status_code=403, detail="Орудие не найдено или нет доступа")

        # 1. Проверка скорости (нарушение технологии)
        speed_violation = False
        if data.avg_speed_kmh:
            op = data.operation.lower()
            if "опрыскивание" in op and data.avg_speed_kmh > 12.0:
                speed_violation = True
            elif "посев" in op and data.avg_speed_kmh > 15.0:
                speed_violation = True

        # 2. Проверка топлива (Анти-слив / Перерасход)
        expected_fuel_l = data.area_ha * data.fuel_norm_l_ha
        
        # Если факт превышает норму более чем на 15% -> генерируем отдельный лог слива/аномалии
        if data.fuel_used_l > (expected_fuel_l * 1.15):
            anomaly_diff = data.fuel_used_l - expected_fuel_l
            anomaly_log = FuelLog(
                machinery_id=machinery.id,
                log_type="ANOMALY",
                amount_l=anomaly_diff,
                description=f"Перерасход топлива на операции {data.operation}. Ожидалось: {expected_fuel_l:.1f}л, факт: {data.fuel_used_l:.1f}л."
            )
            db.add(anomaly_log)

        # Списываем топливо
        machinery.current_fuel_l -= data.fuel_used_l
        if machinery.current_fuel_l < 0:
            machinery.current_fuel_l = 0

        # Обновляем моточасы
        machinery.moto_hours += data.duration_h

        # Создаем лог стандартного расхода
        usage_log = FuelLog(
            machinery_id=machinery.id,
            log_type="USAGE",
            amount_l=data.fuel_used_l,
            description=f"Расход по наряду: {data.operation} на {data.area_ha} га"
        )
        db.add(usage_log)

        # Создаем сам наряд
        work_order = WorkOrder(
            user_id=user_id,
            machinery_id=data.machinery_id,
            implement_id=data.implement_id,
            field_id=data.field_id,
            operation=data.operation,
            area_ha=data.area_ha,
            duration_h=data.duration_h,
            avg_speed_kmh=data.avg_speed_kmh,
            speed_violation=speed_violation,
            fuel_used_l=data.fuel_used_l,
            fuel_norm_l=expected_fuel_l
        )
        db.add(work_order)
        db.commit()
        db.refresh(work_order)
        return work_order

    @staticmethod
    def get_maintenance_alerts(db: Session, user_id: int):
        machines = db.query(Machinery).filter(Machinery.user_id == user_id).all()
        alerts = []
        for m in machines:
            # Находим последнее ТО
            last_maint = db.query(MaintenanceLog).filter(MaintenanceLog.machinery_id == m.id).order_by(MaintenanceLog.moto_hours_at_maintenance.desc()).first()
            last_hours = last_maint.moto_hours_at_maintenance if last_maint else 0.0
            
            hours_since_maint = m.moto_hours - last_hours
            if hours_since_maint >= m.maintenance_interval_h:
                alerts.append({
                    "machinery_id": m.id,
                    "name": m.name,
                    "status": "CRITICAL",
                    "message": f"ТО просрочено! Наработка {hours_since_maint:.1f} ч (норма {m.maintenance_interval_h} ч)."
                })
            elif hours_since_maint >= (m.maintenance_interval_h * 0.9):
                alerts.append({
                    "machinery_id": m.id,
                    "name": m.name,
                    "status": "WARNING",
                    "message": f"Приближается ТО. Наработка {hours_since_maint:.1f} ч из {m.maintenance_interval_h} ч."
                })
        return alerts

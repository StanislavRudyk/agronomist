from fastapi import HTTPException
from sqlalchemy.orm import Session
from backend.modeles.models import Warehouse, GrainLot, QualityAnalysis, StorageCondition, User
from backend.modeles.schemas import (
    WarehouseCreate,
    GrainLotCreate,
    QualityAnalysisCreate,
    StorageConditionCreate
)


_WHEAT_CLASS_RULES = [
    {"class": 1, "gluten_min": 32.0, "protein_min": 14.5, "test_weight_min": 760, "falling_min": 300, "moisture_max": 14.0, "impurity_max": 1.0},
    {"class": 2, "gluten_min": 28.0, "protein_min": 13.5, "test_weight_min": 750, "falling_min": 250, "moisture_max": 14.0, "impurity_max": 1.0},
    {"class": 3, "gluten_min": 23.0, "protein_min": 12.0, "test_weight_min": 730, "falling_min": 200, "moisture_max": 14.0, "impurity_max": 2.0},
    {"class": 4, "gluten_min": 18.0, "protein_min": 10.0, "test_weight_min": 710, "falling_min": 150, "moisture_max": 14.5, "impurity_max": 3.0},
    {"class": 5, "gluten_min": 0.0, "protein_min": 0.0, "test_weight_min": 690, "falling_min": 80, "moisture_max": 15.0, "impurity_max": 5.0},
]


class WarehouseService:

    @staticmethod
    def create_warehouse(db: Session, data: WarehouseCreate, user_id: int) -> Warehouse:
        wh = Warehouse(**data.model_dump(), user_id=user_id)
        db.add(wh)
        db.commit()
        db.refresh(wh)
        return wh

    @staticmethod
    def get_warehouses(db: Session, user_id: int):
        return db.query(Warehouse).filter(Warehouse.user_id == user_id).all()

    @staticmethod
    def add_grain_lot(db: Session, data: GrainLotCreate, user_id: int) -> GrainLot:
        wh = db.query(Warehouse).filter(
            Warehouse.id == data.warehouse_id,
            Warehouse.user_id == user_id,
        ).first()
        if not wh:
            raise HTTPException(status_code=404, detail="Склад не найден")

        if wh.current_load_t + data.weight_t > wh.capacity_t:
            raise HTTPException(
                status_code=400,
                detail=f"Нет места на складе. Свободно: {wh.capacity_t - wh.current_load_t:.1f} тонн",
            )

        wh.current_load_t += data.weight_t
        lot = GrainLot(**data.model_dump())
        db.add(lot)
        try:
            db.commit()
        except Exception:
            db.rollback()
            wh = db.query(Warehouse).filter(Warehouse.id == data.warehouse_id).first()
            if wh and wh.current_load_t + data.weight_t > wh.capacity_t:
                raise HTTPException(status_code=409, detail="Конкурентное обновление склада  повторите операцию")
            raise
        db.refresh(lot)
        return lot

    @staticmethod
    def add_quality_analysis(db: Session, data: QualityAnalysisCreate, user_id: int) -> QualityAnalysis:
        lot = db.query(GrainLot).filter(GrainLot.id == data.grain_lot_id).first()
        if not lot:
            raise HTTPException(status_code=404, detail="Партия зерна не найдена")
        wh = db.query(Warehouse).filter(Warehouse.id == lot.warehouse_id, Warehouse.user_id == user_id).first()
        if not wh:
            raise HTTPException(status_code=403, detail="Нет доступа к этой партии")

        qa = QualityAnalysis(**data.model_dump())
        db.add(qa)

        grain_class = WarehouseService._classify_wheat(data)
        if grain_class:
            lot.grain_class = grain_class

        db.commit()
        db.refresh(qa)
        return qa

    @staticmethod
    def _classify_wheat(data: QualityAnalysisCreate) -> int | None:
        if data.gluten_pct is None or data.protein_pct is None or data.test_weight_g_l is None or data.falling_number is None:
            return None

        for rule in _WHEAT_CLASS_RULES:
            if (
                data.gluten_pct >= rule["gluten_min"]
                and data.protein_pct >= rule["protein_min"]
                and data.test_weight_g_l >= rule["test_weight_min"]
                and data.falling_number >= rule["falling_min"]
                and data.moisture_pct <= rule["moisture_max"]
                and data.impurity_pct <= rule["impurity_max"]
            ):
                return rule["class"]
        return 6

    @staticmethod
    def log_storage_condition(db: Session, data: StorageConditionCreate, user_id: int) -> StorageCondition:
        wh = db.query(Warehouse).filter(Warehouse.id == data.warehouse_id, Warehouse.user_id == user_id).first()
        if not wh:
            raise HTTPException(status_code=404, detail="Склад не найден")

        is_alert = data.temperature_c > 25.0 or data.humidity_pct > 75.0
        sc = StorageCondition(**data.model_dump(), is_alert=is_alert)
        db.add(sc)
        db.commit()
        db.refresh(sc)
        return sc

    @staticmethod
    def get_storage_alerts(db: Session, user_id: int):
        warehouses = db.query(Warehouse).filter(Warehouse.user_id == user_id).all()
        wh_ids = [w.id for w in warehouses]
        if not wh_ids:
            return []
        alerts = db.query(StorageCondition).filter(
            StorageCondition.warehouse_id.in_(wh_ids),
            StorageCondition.is_alert == True
        ).order_by(StorageCondition.date.desc()).limit(50).all()
        return alerts

    @staticmethod
    def calculate_storage_loss(weight_t: float, moisture_pct: float, days: int) -> dict:
        base_loss_pct_per_month = 0.04
        if moisture_pct > 14.0:
            base_loss_pct_per_month += (moisture_pct - 14.0) * 0.03
        total_loss_pct = base_loss_pct_per_month * (days / 30.0)
        loss_t = weight_t * (total_loss_pct / 100.0)
        return {
            "original_weight_t": weight_t,
            "storage_days": days,
            "loss_pct": round(total_loss_pct, 3),
            "loss_t": round(loss_t, 3),
            "remaining_weight_t": round(weight_t - loss_t, 3)
        }

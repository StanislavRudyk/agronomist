from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session
from backend.modeles.models import (
    User, Field, Machinery, Implement, WorkOrder, FuelLog,
    SoilAnalysis, Warehouse, GrainLot, AgroWeatherData
)
import uuid


class OfflineService:

    @staticmethod
    def generate_snapshot(db: Session, user_id: int) -> dict:
        version_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        fields = db.query(Field).filter(Field.user_id == user_id).all()
        machinery = db.query(Machinery).filter(Machinery.user_id == user_id).all()
        implements = db.query(Implement).filter(Implement.user_id == user_id).all()
        warehouses = db.query(Warehouse).filter(Warehouse.user_id == user_id).all()

        field_ids = [f.id for f in fields]
        machinery_ids = [m.id for m in machinery]
        warehouse_ids = [w.id for w in warehouses]

        work_orders = db.query(WorkOrder).filter(WorkOrder.user_id == user_id).all()
        fuel_logs = db.query(FuelLog).filter(FuelLog.machinery_id.in_(machinery_ids)).all() if machinery_ids else []
        soil_analyses = db.query(SoilAnalysis).filter(SoilAnalysis.field_id.in_(field_ids)).all() if field_ids else []
        grain_lots = db.query(GrainLot).filter(GrainLot.warehouse_id.in_(warehouse_ids)).all() if warehouse_ids else []
        weather_data = []
        for fid in field_ids:
            latest = db.query(AgroWeatherData).filter(AgroWeatherData.field_id == fid).order_by(AgroWeatherData.created_at.desc()).first()
            if latest:
                weather_data.append(latest)

        return {
            "version_id": version_id,
            "generated_at": now,
            "user_id": user_id,
            "fields": [_serialize(f, ["id", "name", "latitude", "longitude", "crop_type"]) for f in fields],
            "machinery": [_serialize(m, ["id", "name", "type", "license_plate", "fuel_capacity_l", "current_fuel_l", "moto_hours", "status"]) for m in machinery],
            "implements": [_serialize(i, ["id", "name", "type", "width_m"]) for i in implements],
            "warehouses": [_serialize(w, ["id", "name", "type", "capacity_t", "current_load_t"]) for w in warehouses],
            "work_orders": [_serialize(wo, ["id", "machinery_id", "field_id", "operation", "area_ha", "duration_h", "fuel_used_l", "fuel_norm_l", "speed_violation", "date"]) for wo in work_orders],
            "fuel_logs": [_serialize(fl, ["id", "machinery_id", "log_type", "amount_l", "description", "date"]) for fl in fuel_logs],
            "soil_analyses": [_serialize(sa, ["id", "field_id", "ph_level", "organic_matter_pct", "nitrogen_mg_kg", "phosphorus_mg_kg", "potassium_mg_kg", "soil_texture"]) for sa in soil_analyses],
            "grain_lots": [_serialize(gl, ["id", "warehouse_id", "field_id", "crop_type", "weight_t", "grain_class"]) for gl in grain_lots],
            "weather_snapshots": [_serialize(wd, ["id", "field_id", "air_temp", "relative_humidity", "precipitation", "wind_speed", "dew_point"]) for wd in weather_data],
        }

    @staticmethod
    def sync_operations(db: Session, user_id: int, operations: list[dict]) -> dict:
        applied = []
        conflicts = []

        for op in operations:
            op_type = op.get("type")
            data = op.get("data", {})

            try:
                if op_type == "create_work_order":
                    from backend.services.machinery_service import MachineryService
                    from backend.modeles.schemas import WorkOrderCreate
                    wo_data = WorkOrderCreate(**data)
                    MachineryService.create_work_order(db, wo_data, user_id)
                    applied.append({"type": op_type, "status": "applied"})

                elif op_type == "log_fuel":
                    from backend.services.machinery_service import MachineryService
                    from backend.modeles.schemas import FuelLogCreate
                    fl_data = FuelLogCreate(**data)
                    MachineryService.log_fuel(db, fl_data, user_id)
                    applied.append({"type": op_type, "status": "applied"})

                elif op_type == "add_soil_analysis":
                    from backend.services.yield_service import YieldForecastService
                    from backend.modeles.schemas import SoilAnalysisCreate
                    payload = dict(data)
                    field_id = payload.pop("field_id")
                    sa_data = SoilAnalysisCreate(**payload)
                    YieldForecastService.add_soil_analysis(db, field_id, sa_data, user_id)
                    applied.append({"type": op_type, "status": "applied"})

                elif op_type == "add_grain_lot":
                    from backend.services.warehouse_service import WarehouseService
                    from backend.modeles.schemas import GrainLotCreate
                    gl_data = GrainLotCreate(**data)
                    WarehouseService.add_grain_lot(db, gl_data, user_id)
                    applied.append({"type": op_type, "status": "applied"})

                else:
                    conflicts.append({"type": op_type, "status": "unknown_operation"})

            except HTTPException as e:
                conflicts.append({"type": op_type, "status": "conflict", "detail": e.detail})
            except Exception as e:
                conflicts.append({"type": op_type, "status": "error", "detail": str(e)})

        return {
            "total_operations": len(operations),
            "applied": len(applied),
            "conflicts": len(conflicts),
            "results": applied + conflicts
        }


def _serialize(obj, fields: list[str]) -> dict:
    result = {}
    for f in fields:
        val = getattr(obj, f, None)
        if isinstance(val, datetime):
            val = val.isoformat()
        result[f] = val
    return result

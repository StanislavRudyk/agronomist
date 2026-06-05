import csv
import io
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import extract

from backend.modeles.models import (
    User, Field, Machinery, WorkOrder, FuelLog,
    SoilAnalysis, AgroWeatherData, GrainLot, QualityAnalysis
)


class ReportsService:

    @staticmethod
    def annual_report(db: Session, user_id: int, year: int) -> dict:
        fields = db.query(Field).filter(Field.user_id == user_id).all()
        field_ids = [f.id for f in fields]

        machinery = db.query(Machinery).filter(Machinery.user_id == user_id).all()
        machinery_ids = [m.id for m in machinery]

        work_orders = db.query(WorkOrder).filter(
            WorkOrder.user_id == user_id,
            extract("year", WorkOrder.date) == year
        ).all()

        fuel_logs = db.query(FuelLog).filter(
            FuelLog.machinery_id.in_(machinery_ids),
            extract("year", FuelLog.date) == year
        ).all() if machinery_ids else []

        grain_lots = []
        for f in fields:
            lots = db.query(GrainLot).filter(
                GrainLot.field_id == f.id,
                extract("year", GrainLot.harvest_date) == year
            ).all()
            grain_lots.extend(lots)

        total_area_ha = sum(wo.area_ha for wo in work_orders)
        total_fuel_used = sum(wo.fuel_used_l for wo in work_orders)
        total_fuel_norm = sum(wo.fuel_norm_l for wo in work_orders)
        fuel_efficiency = round((total_fuel_used / total_area_ha), 2) if total_area_ha > 0 else 0
        fuel_overuse = round(total_fuel_used - total_fuel_norm, 1)

        refills = sum(fl.amount_l for fl in fuel_logs if fl.log_type == "REFILL")
        anomalies = [fl for fl in fuel_logs if fl.log_type == "ANOMALY"]

        total_harvest_t = sum(gl.weight_t for gl in grain_lots)
        avg_yield = round(total_harvest_t / len(fields), 2) if fields else 0

        speed_violations = sum(1 for wo in work_orders if wo.speed_violation)

        operations_summary = {}
        for wo in work_orders:
            op = wo.operation
            if op not in operations_summary:
                operations_summary[op] = {"count": 0, "area_ha": 0, "fuel_l": 0}
            operations_summary[op]["count"] += 1
            operations_summary[op]["area_ha"] += wo.area_ha
            operations_summary[op]["fuel_l"] += wo.fuel_used_l

        return {
            "year": year,
            "total_fields": len(fields),
            "total_machinery": len(machinery),
            "total_work_orders": len(work_orders),
            "total_area_processed_ha": round(total_area_ha, 1),
            "fuel_summary": {
                "total_fuel_used_l": round(total_fuel_used, 1),
                "total_fuel_norm_l": round(total_fuel_norm, 1),
                "fuel_overuse_l": fuel_overuse,
                "avg_fuel_per_ha": fuel_efficiency,
                "total_refills_l": round(refills, 1),
                "anomalies_count": len(anomalies),
                "anomalies": [{"machinery_id": a.machinery_id, "amount_l": a.amount_l, "description": a.description} for a in anomalies]
            },
            "harvest_summary": {
                "total_harvest_t": round(total_harvest_t, 1),
                "avg_yield_per_field_t": avg_yield,
                "grain_lots_count": len(grain_lots)
            },
            "speed_violations_count": speed_violations,
            "operations_breakdown": operations_summary
        }

    @staticmethod
    def field_history(db: Session, user_id: int, field_id: int) -> dict:
        field = db.query(Field).filter(Field.id == field_id, Field.user_id == user_id).first()
        if not field:
            raise HTTPException(status_code=404, detail="Поле не найдено")

        soil_analyses = db.query(SoilAnalysis).filter(SoilAnalysis.field_id == field_id).all()
        work_orders = db.query(WorkOrder).filter(WorkOrder.field_id == field_id).order_by(WorkOrder.date.desc()).all()
        weather_records = db.query(AgroWeatherData).filter(AgroWeatherData.field_id == field_id).order_by(AgroWeatherData.created_at.desc()).limit(30).all()
        grain_lots = db.query(GrainLot).filter(GrainLot.field_id == field_id).all()

        quality_data = []
        for lot in grain_lots:
            qa = db.query(QualityAnalysis).filter(QualityAnalysis.grain_lot_id == lot.id).first()
            quality_data.append({
                "lot_id": lot.id,
                "crop_type": lot.crop_type,
                "weight_t": lot.weight_t,
                "grain_class": lot.grain_class,
                "harvest_date": lot.harvest_date.isoformat() if lot.harvest_date else None,
                "quality": {
                    "moisture_pct": qa.moisture_pct,
                    "impurity_pct": qa.impurity_pct,
                    "gluten_pct": qa.gluten_pct,
                    "protein_pct": qa.protein_pct
                } if qa else None
            })

        return {
            "field_id": field.id,
            "field_name": field.name,
            "coordinates": {"lat": field.latitude, "lon": field.longitude},
            "current_crop": field.crop_type,
            "soil_analyses": [
                {
                    "ph": sa.ph_level,
                    "organic_matter_pct": sa.organic_matter_pct,
                    "N": sa.nitrogen_mg_kg,
                    "P": sa.phosphorus_mg_kg,
                    "K": sa.potassium_mg_kg,
                    "texture": sa.soil_texture,
                    "date": sa.date.isoformat() if sa.date else None
                } for sa in soil_analyses
            ],
            "work_history": [
                {
                    "operation": wo.operation,
                    "area_ha": wo.area_ha,
                    "fuel_used_l": wo.fuel_used_l,
                    "fuel_norm_l": wo.fuel_norm_l,
                    "speed_violation": wo.speed_violation,
                    "date": wo.date.isoformat() if wo.date else None
                } for wo in work_orders
            ],
            "harvest_history": quality_data,
            "weather_records_count": len(weather_records)
        }

    @staticmethod
    def export_work_orders_csv(db: Session, user_id: int) -> str:
        work_orders = db.query(WorkOrder).filter(WorkOrder.user_id == user_id).order_by(WorkOrder.date.desc()).all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Поле", "Операция", "Площадь (га)", "Длительность (ч)", "Топливо факт (л)", "Топливо норма (л)", "Превышение скорости", "Дата"])

        for wo in work_orders:
            writer.writerow([
                wo.id, wo.field_id, wo.operation, wo.area_ha, wo.duration_h,
                wo.fuel_used_l, wo.fuel_norm_l,
                "Да" if wo.speed_violation else "Нет",
                wo.date.isoformat() if wo.date else ""
            ])

        return output.getvalue()

    @staticmethod
    def export_fuel_csv(db: Session, user_id: int) -> str:
        machinery = db.query(Machinery).filter(Machinery.user_id == user_id).all()
        machinery_ids = [m.id for m in machinery]
        if not machinery_ids:
            return ""

        fuel_logs = db.query(FuelLog).filter(FuelLog.machinery_id.in_(machinery_ids)).order_by(FuelLog.date.desc()).all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Техника ID", "Тип", "Объём (л)", "Описание", "Дата"])

        for fl in fuel_logs:
            writer.writerow([
                fl.id, fl.machinery_id, fl.log_type, fl.amount_l,
                fl.description or "",
                fl.date.isoformat() if fl.date else ""
            ])

        return output.getvalue()

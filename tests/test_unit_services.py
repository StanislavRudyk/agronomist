"""Unit tests for pure service logic (no HTTP)."""
import pytest
from fastapi import HTTPException

from backend.services.calculator_service import CalculatorService
from backend.services.warehouse_service import WarehouseService
from backend.modeles.schemas import (
    SeedingRateRequest,
    SprayingRequest,
    FertilizerRequest,
    QualityAnalysisCreate,
)


class TestCalculatorServiceUnit:
    def test_seeding_formula(self):
        data = SeedingRateRequest(
            target_density_mln_ha=4.0,
            weight_1000_seeds_g=45.0,
            germination_percent=95.0,
            purity_percent=98.0,
            field_area_ha=100.0,
        )
        result = CalculatorService.calculate_seeding_rate(data)
        pg = 95 * 98 / 100
        expected = (4 * 45 * 100) / pg
        assert abs(result.seeding_rate_kg_ha - round(expected, 2)) < 0.01

    def test_fertilizer_wheat(self):
        data = FertilizerRequest(crop_type="озимая пшеница", target_yield_t_ha=5.0)
        r = CalculatorService.calculate_fertilizer(data)
        assert r.nitrogen_kg_ha == 150.0

    def test_spraying_division_by_zero_guard(self):
        with pytest.raises(HTTPException):
            CalculatorService.calculate_spraying(
                SprayingRequest(tank_volume_l=100, water_rate_l_ha=0, chemical_rate_per_ha=1, field_area_ha=10)
            )


class TestWarehouseClassifyUnit:
    def test_class_1_wheat(self):
        data = QualityAnalysisCreate(
            grain_lot_id=1,
            moisture_pct=13,
            impurity_pct=0.5,
            gluten_pct=32,
            protein_pct=14.5,
            test_weight_g_l=760,
            falling_number=300,
        )
        assert WarehouseService._classify_wheat(data) == 1

    def test_class_6_fallback(self):
        data = QualityAnalysisCreate(
            grain_lot_id=1,
            moisture_pct=20,
            impurity_pct=10,
            gluten_pct=5,
            protein_pct=5,
            test_weight_g_l=600,
            falling_number=50,
        )
        assert WarehouseService._classify_wheat(data) == 6

    def test_none_when_incomplete(self):
        data = QualityAnalysisCreate(grain_lot_id=1, moisture_pct=13, impurity_pct=1)
        assert WarehouseService._classify_wheat(data) is None

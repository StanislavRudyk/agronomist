from fastapi import HTTPException
from backend.modeles.schemas import (
    SeedingRateRequest,
    SeedingRateResponse,
    SprayingRequest,
    SprayingResponse,
    FertilizerRequest,
    FertilizerResponse,
)

class CalculatorService:

    @staticmethod
    def calculate_seeding_rate(data: SeedingRateRequest) -> SeedingRateResponse:
        if data.target_density_mln_ha <= 0 or data.weight_1000_seeds_g <= 0 or data.field_area_ha <= 0:
            raise HTTPException(status_code=400, detail="Параметры должны быть больше нуля")

        # Посевная годность (%)
        pg = (data.germination_percent * data.purity_percent) / 100.0
        if pg == 0:
            raise HTTPException(status_code=400, detail="Посевная годность не может быть равна нулю")

        # Норма высева (кг/га) = (Млн.шт * Масса 1000 зерен * 100) / ПГ
        rate_kg_ha = (data.target_density_mln_ha * data.weight_1000_seeds_g * 100.0) / pg
        total_kg = rate_kg_ha * data.field_area_ha

        return SeedingRateResponse(
            seeding_rate_kg_ha=round(rate_kg_ha, 2),
            total_seeds_kg=round(total_kg, 2)
        )

    @staticmethod
    def calculate_spraying(data: SprayingRequest) -> SprayingResponse:
        if data.tank_volume_l <= 0 or data.water_rate_l_ha <= 0 or data.chemical_rate_per_ha < 0 or data.field_area_ha <= 0:
            raise HTTPException(status_code=400, detail="Недопустимые параметры опрыскивания")

        area_per_tank = data.tank_volume_l / data.water_rate_l_ha
        chem_per_tank = area_per_tank * data.chemical_rate_per_ha
        total_water = data.field_area_ha * data.water_rate_l_ha
        total_chem = data.field_area_ha * data.chemical_rate_per_ha
        tanks = data.field_area_ha / area_per_tank

        return SprayingResponse(
            area_per_tank_ha=round(area_per_tank, 2),
            chemical_per_tank=round(chem_per_tank, 2),
            total_water_l=round(total_water, 2),
            total_chemical=round(total_chem, 2),
            tanks_needed=round(tanks, 2)
        )

    @staticmethod
    def calculate_fertilizer(data: FertilizerRequest) -> FertilizerResponse:
        if data.target_yield_t_ha <= 0:
            raise HTTPException(status_code=400, detail="Плановая урожайность должна быть больше нуля")

        # Вынос элементов питания на 1 тонну основной продукции (с учетом побочной), кг д.в.
        removal_rates = {
            "пшениц": {"N": 30.0, "P": 10.0, "K": 20.0},
            "ячмен": {"N": 25.0, "P": 11.0, "K": 22.0},
            "кукуруз": {"N": 25.0, "P": 10.0, "K": 25.0},
            "подсолнечник": {"N": 50.0, "P": 25.0, "K": 110.0},
            "рапс": {"N": 50.0, "P": 25.0, "K": 40.0},
            "соя": {"N": 60.0, "P": 15.0, "K": 20.0},
            "картофел": {"N": 5.0, "P": 2.0, "K": 8.0},
            "свекл": {"N": 5.0, "P": 1.5, "K": 6.0},
        }

        crop_lower = data.crop_type.lower().strip()
        n, p, k = 0.0, 0.0, 0.0  # Инициализация по умолчанию

        for key, rates in removal_rates.items():
            if key in crop_lower:
                n, p, k = rates["N"], rates["P"], rates["K"]
                break

        if n == 0.0:
            raise HTTPException(status_code=400, detail=f"Культура '{data.crop_type}' не найдена в базе калькулятора")

        return FertilizerResponse(
            nitrogen_kg_ha=round(n * data.target_yield_t_ha, 1),
            phosphorus_kg_ha=round(p * data.target_yield_t_ha, 1),
            potassium_kg_ha=round(k * data.target_yield_t_ha, 1),
        )

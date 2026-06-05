import math
from fastapi import HTTPException
from sqlalchemy.orm import Session
from backend.modeles.models import Field, SoilAnalysis, AgroWeatherData
from backend.modeles.schemas import (
    SoilAnalysisCreate,
    YieldForecastResponse,
    YieldForecastScenario
)

class YieldForecastService:

    CROP_POTENTIALS = {
        "озимая пшеница": {"max_t_ha": 8.0, "N": 30.0, "P": 10.0, "K": 20.0},
        "кукуруза": {"max_t_ha": 12.0, "N": 25.0, "P": 10.0, "K": 25.0},
        "подсолнечник": {"max_t_ha": 4.0, "N": 50.0, "P": 25.0, "K": 110.0},
        "рапс": {"max_t_ha": 4.5, "N": 50.0, "P": 25.0, "K": 40.0},
        "соя": {"max_t_ha": 4.0, "N": 60.0, "P": 15.0, "K": 20.0}, # Соя фиксирует азот, но для упрощения оставим вынос
    }

    @staticmethod
    def add_soil_analysis(db: Session, field_id: int, data: SoilAnalysisCreate, user_id: int) -> SoilAnalysis:
        field = db.query(Field).filter(Field.id == field_id, Field.user_id == user_id).first()
        if not field:
            raise HTTPException(status_code=404, detail="Поле не найдено или нет доступа")
        
        old_analysis = db.query(SoilAnalysis).filter(SoilAnalysis.field_id == field_id).first()
        if old_analysis:
            db.delete(old_analysis)
        
        analysis = SoilAnalysis(field_id=field_id, **data.model_dump())
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        return analysis

    @staticmethod
    def forecast_yield(db: Session, field_id: int, user_id: int) -> YieldForecastResponse:
        field = db.query(Field).filter(Field.id == field_id, Field.user_id == user_id).first()
        if not field:
            raise HTTPException(status_code=404, detail="Поле не найдено")

        soil = db.query(SoilAnalysis).filter(SoilAnalysis.field_id == field_id).first()
        if not soil:
            raise HTTPException(status_code=400, detail="Для прогноза требуется анализ почвы (Soil Analysis)")

        weather = db.query(AgroWeatherData).filter(AgroWeatherData.field_id == field_id).order_by(AgroWeatherData.created_at.desc()).first()

        crop_name = field.crop_type.lower().strip()
        crop_data = None
        for key, vals in YieldForecastService.CROP_POTENTIALS.items():
            if key in crop_name:
                crop_data = vals
                break
        
        if not crop_data:
            # Fallback
            crop_data = {"max_t_ha": 5.0, "N": 30.0, "P": 10.0, "K": 20.0}

        recs = []
        
        # 1. Анализ pH (Блокировка элементов)
        ph = soil.ph_level
        ph_status = "Оптимальный"
        p_coef = 1.0
        n_coef = 1.0
        if ph < 5.5:
            ph_status = "Сильнокислая (Алюминий блокирует фосфор)"
            p_coef = 0.5
            n_coef = 0.8
            recs.append("КРИТИЧНО: Требуется известкование! Фосфор недоступен для растений из-за высокой кислотности.")
        elif ph > 7.5:
            ph_status = "Щелочная (Кальций блокирует фосфор)"
            p_coef = 0.6
            recs.append("ВНИМАНИЕ: Щелочная реакция почвы. Рекомендуется внесение физиологически кислых удобрений и серы.")

        # 2. Пересчет мг/кг в кг/га (грубо: умножаем на 3 для слоя 30 см)
        kg_ha_coef = 3.0
        
        # Гумус дает дополнительный азот (примерно 20 кг/га за сезон на 1% гумуса)
        organic_n = soil.organic_matter_pct * 20.0
        if soil.organic_matter_pct < 2.0:
            recs.append("Низкое содержание гумуса. Рекомендуется запашка пожнивных остатков или сидераты.")

        avail_n = (soil.nitrogen_mg_kg * kg_ha_coef * n_coef) + organic_n
        avail_p = (soil.phosphorus_mg_kg * kg_ha_coef * p_coef)
        avail_k = (soil.potassium_mg_kg * kg_ha_coef)

        # 3. Закон Либиха (Лимитирующий фактор)
        yield_by_n = avail_n / crop_data["N"]
        yield_by_p = avail_p / crop_data["P"]
        yield_by_k = avail_k / crop_data["K"]

        chem_yield_limit = min(yield_by_n, yield_by_p, yield_by_k, crop_data["max_t_ha"])
        
        limiting_factor = "Генетический потенциал гибрида"
        if chem_yield_limit == yield_by_n: limiting_factor = "Азот (N)"
        if chem_yield_limit == yield_by_p: limiting_factor = "Фосфор (P)"
        if chem_yield_limit == yield_by_k: limiting_factor = "Калий (K)"

        if chem_yield_limit < crop_data["max_t_ha"]:
            recs.append(f"Главный ограничитель урожайности по питанию: {limiting_factor}.")

        # 4. Погодный фактор (Влага)
        weather_coef = 1.0
        if weather and weather.soil_moisture_9_27cm is not None:
            moisture = weather.soil_moisture_9_27cm
            if moisture < 0.15:
                weather_coef = 0.7
                limiting_factor = "Дефицит почвенной влаги"
                recs.append("Жесткая засуха в корнеобитаемом слое. Потенциал снижен на 30%.")
            elif moisture > 0.40:
                weather_coef = 0.85
                limiting_factor = "Переувлажнение (недостаток кислорода корням)"
                recs.append("Переувлажнение почвы. Риск вымокания или грибковых заболеваний.")

        # Расчет сценариев
        realistic = chem_yield_limit * weather_coef
        optimistic = chem_yield_limit * 1.15 # Идеальные условия до конца сезона
        pessimistic = realistic * 0.7 # Наступление засухи/стресса
        
        # Ограничиваем сверху генетическим потенциалом
        realistic = min(realistic, crop_data["max_t_ha"])
        optimistic = min(optimistic, crop_data["max_t_ha"])
        pessimistic = min(pessimistic, crop_data["max_t_ha"])

        scenarios = [
            YieldForecastScenario(
                scenario="Оптимистичный",
                expected_yield_t_ha=round(optimistic, 2),
                description="При идеальном распределении осадков и отсутствии температурных стрессов."
            ),
            YieldForecastScenario(
                scenario="Реалистичный",
                expected_yield_t_ha=round(realistic, 2),
                description="Текущий потенциал с учетом состояния почвы и влаги."
            ),
            YieldForecastScenario(
                scenario="Пессимистичный",
                expected_yield_t_ha=round(pessimistic, 2),
                description="В случае наступления жесткой почвенной засухи в критические фазы развития."
            )
        ]

        if not recs:
            recs.append("Идеальные условия. Ограничений не выявлено.")

        return YieldForecastResponse(
            field_id=field_id,
            crop_type=field.crop_type,
            limiting_factor=limiting_factor,
            ph_status=ph_status,
            forecasts=scenarios,
            recommendations=recs
        )

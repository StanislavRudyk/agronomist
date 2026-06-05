class AgroAnalyzer:
    @staticmethod
    def analyze(crop_type: str, air_temp: float, soil_temp: float, soil_moisture: float, snow_depth: float = 0.0, precip_5days: float = 0.0) -> list[str]:
        warnings = []
        crop_lower = crop_type.lower()

        if "озим" in crop_lower or "пшениц" in crop_lower:
            if soil_temp < -5.0 and snow_depth < 2.0:
                warnings.append("КРИТИЧЕСКАЯ УГРОЗА: Опасность вымерзания озимых! Температура почвы ниже -5°C при отсутствии снежного покрова.")
        else:
            if air_temp < 0.0:
                warnings.append("ВНИМАНИЕ: Риск повреждения всходов заморозками воздуха для теплолюбивых культур.")

        if soil_moisture < 0.20:
            if precip_5days < 5.0:
                warnings.append("ВНИМАНИЕ: Засуха! Влажность почвы ниже 20%, осадков в ближайшие 5 дней не ожидается. Необходим полив.")
            else:
                warnings.append("ВНИМАНИЕ: Низкая влажность почвы (ниже 20%). Ожидаются осадки, следите за динамикой.")

        return warnings

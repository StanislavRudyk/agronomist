class AgroAnalyzer:
    FROST_THRESHOLDS: dict[str, float] = {
        "кукуруз": 5.0,
        "томат": 2.0,
        "огурц": 2.0,
        "картофел": 3.0,
        "подсолнечник": 1.0,
        "рапс": -3.0,
        "свекл": 0.0,
    }
    WINTER_CROPS = {"озим", "рожь", "тритикале"}

    @staticmethod
    def _is_winter_crop(crop_lower: str) -> bool:
        return any(m in crop_lower for m in AgroAnalyzer.WINTER_CROPS)

    @staticmethod
    def _is_spring_wheat(crop_lower: str) -> bool:
        return "яров" in crop_lower and "пшениц" in crop_lower

    @staticmethod
    def _is_winter_wheat(crop_lower: str) -> bool:
        return ("озим" in crop_lower and "пшениц" in crop_lower) or (
            "пшениц" in crop_lower and not AgroAnalyzer._is_spring_wheat(crop_lower)
        )

    @staticmethod
    def _analyze_frost(crop_lower: str, air_temp: float, soil_temp: float, snow_depth_m: float) -> list[str]:
        warnings: list[str] = []
        if AgroAnalyzer._is_winter_crop(crop_lower) or AgroAnalyzer._is_winter_wheat(crop_lower):
            if snow_depth_m < 0.05:
                if soil_temp < -10.0:
                    warnings.append("КРИТИЧЕСКАЯ УГРОЗА: Риск гибели озимых! Температура почвы ниже -10°C при отсутствии снежного покрова (< 5 см).")
                elif soil_temp < -5.0:
                    warnings.append("ПРЕДУПРЕЖДЕНИЕ: Опасность повреждения озимых. Температура почвы ниже -5°C, снежный покров отсутствует.")
            elif snow_depth_m < 0.15 and soil_temp < -15.0:
                warnings.append("КРИТИЧЕСКАЯ УГРОЗА: Экстремальный мороз! Снежного покрова (< 15 см) недостаточно для защиты озимых.")
            return warnings
        for crop_key, threshold in AgroAnalyzer.FROST_THRESHOLDS.items():
            if crop_key in crop_lower:
                if air_temp < threshold:
                    warnings.append(f"ВНИМАНИЕ: Риск повреждения ({crop_key}) заморозком. Температура {air_temp:.1f}°C ниже порога {threshold:.0f}°C.")
                return warnings
        if air_temp < 0.0:
            warnings.append(f"ВНИМАНИЕ: Риск повреждения всходов заморозком. Температура воздуха {air_temp:.1f}°C.")
        return warnings

    @staticmethod
    def _analyze_drought(soil_moisture_3_9: float, precip_5days: float) -> list[str]:
        warnings: list[str] = []
        if soil_moisture_3_9 < 0.20:
            if precip_5days < 5.0:
                warnings.append(f"ВНИМАНИЕ: Засуха! Влажность почвы {soil_moisture_3_9 * 100:.0f}% (норма > 20%), осадков не ожидается. Необходим полив.")
            else:
                warnings.append(f"ВНИМАНИЕ: Низкая влажность почвы ({soil_moisture_3_9 * 100:.0f}%). Ожидаются осадки ({precip_5days:.1f} мм), следите за динамикой.")
        return warnings

    @staticmethod
    def _analyze_wind(wind_speed_kmh: float, wind_gusts_kmh: float) -> list[str]:
        warnings: list[str] = []
        if wind_gusts_kmh >= 60.0:
            warnings.append(f"ВНИМАНИЕ: Сильные порывы ветра ({wind_gusts_kmh:.0f} км/ч). Риск полегания высокостебельных культур.")
        elif wind_speed_kmh >= 40.0:
            warnings.append(f"ВНИМАНИЕ: Сильный ветер ({wind_speed_kmh:.0f} км/ч). Опрыскивание не рекомендуется.")
        return warnings

    @staticmethod
    def _analyze_humidity(relative_humidity: float, soil_temp: float) -> list[str]:
        warnings: list[str] = []
        if relative_humidity >= 85.0 and soil_temp > 10.0:
            warnings.append(f"ВНИМАНИЕ: Высокая влажность воздуха ({relative_humidity:.0f}%) при тёплой почве — повышенный риск грибковых заболеваний.")
        return warnings

    @staticmethod
    def _analyze_evapotranspiration(et0: float) -> list[str]:
        warnings: list[str] = []
        if et0 > 5.5:
            warnings.append(f"ВНИМАНИЕ: Высокое испарение (ET₀ = {et0:.1f} мм/день). Требуется увеличенная норма полива.")
        elif et0 > 4.0:
            warnings.append(f"ИНФОРМАЦИЯ: Умеренное испарение (ET₀ = {et0:.1f} мм/день). Контролируйте влажность почвы.")
        return warnings

    @staticmethod
    def _analyze_uv(uv_index_max: float) -> list[str]:
        warnings: list[str] = []
        if uv_index_max >= 8.0:
            warnings.append(f"ИНФОРМАЦИЯ: Высокий УФ-индекс ({uv_index_max:.1f}). Риск фотодеградации пестицидов при опрыскивании днём.")
        return warnings

    @staticmethod
    def _analyze_visibility(visibility_m: float) -> list[str]:
        warnings: list[str] = []
        if visibility_m < 1000.0:
            warnings.append(f"ВНИМАНИЕ: Очень низкая видимость ({visibility_m:.0f} м) — туман. Работа техники на поле опасна.")
        return warnings

    @staticmethod
    def _analyze_vpd(vpd_kpa: float) -> list[str]:
        warnings: list[str] = []
        if vpd_kpa > 2.5:
            warnings.append(f"ВНИМАНИЕ: Дефицит давления пара {vpd_kpa:.2f} кПа — экстремальный стресс транспирации. Срочно необходим полив.")
        elif vpd_kpa > 1.5:
            warnings.append(f"ПРЕДУПРЕЖДЕНИЕ: Дефицит давления пара {vpd_kpa:.2f} кПа — умеренный стресс транспирации.")
        return warnings

    @staticmethod
    def analyze_air_quality(pm10: float, pm2_5: float, dust: float, european_aqi: int) -> list[str]:
        warnings: list[str] = []
        if european_aqi >= 100:
            warnings.append(f"КРИТИЧЕСКАЯ УГРОЗА: Очень плохое качество воздуха (EAQI={european_aqi}). Работа на поле опасна для здоровья.")
        elif european_aqi >= 50:
            warnings.append(f"ВНИМАНИЕ: Плохое качество воздуха (EAQI={european_aqi}). Ограничьте время работы, используйте защиту.")
        elif european_aqi >= 25:
            warnings.append(f"ИНФОРМАЦИЯ: Умеренное качество воздуха (EAQI={european_aqi}). Чувствительным лицам рекомендуется ограничить пребывание на поле.")
        if pm10 > 50:
            warnings.append(f"ВНИМАНИЕ: PM10 = {pm10:.0f} мкг/м³. Опрыскивание не рекомендуется — взвешенные частицы снижают эффективность химикатов.")
        if dust > 15:
            warnings.append(f"ВНИМАНИЕ: Высокая запылённость ({dust:.0f} мкг/м³). Ожидайте снижения фотосинтетической активности.")
        if pm2_5 > 25:
            warnings.append(f"ВНИМАНИЕ: PM2.5 = {pm2_5:.0f} мкг/м³ (норма ВОЗ ≤ 15). Угроза здоровью работников поля.")
        return warnings

    @staticmethod
    def analyze_flood(discharge_max: float | None) -> list[str]:
        warnings: list[str] = []
        if discharge_max is None:
            return warnings
        if discharge_max > 100.0:
            warnings.append(f"КРИТИЧЕСКАЯ УГРОЗА: Катастрофический паводок! Расход реки {discharge_max:.1f} м³/с. Эвакуация с низменных полей.")
        elif discharge_max > 20.0:
            warnings.append(f"КРИТИЧЕСКАЯ УГРОЗА: Высокий риск затопления полей. Расход реки достигает {discharge_max:.1f} м³/с.")
        elif discharge_max > 5.0:
            warnings.append(f"ПРЕДУПРЕЖДЕНИЕ: Повышенный речной сток ({discharge_max:.1f} м³/с). Возможно подтопление низменных полей.")
        return warnings

    @staticmethod
    def analyze(
        crop_type: str,
        air_temp: float,
        soil_temp: float,
        soil_moisture: float,
        snow_depth: float = 0.0,
        precip_5days: float = 0.0,
        wind_speed: float = 0.0,
        wind_gusts: float = 0.0,
        relative_humidity: float = 0.0,
        et0: float = 0.0,
        uv_index_max: float = 0.0,
        visibility: float = 99999.0,
        vpd: float = 0.0,
    ) -> list[str]:
        crop_lower = crop_type.lower().strip()
        warnings: list[str] = []
        warnings.extend(AgroAnalyzer._analyze_frost(crop_lower, air_temp, soil_temp, snow_depth))
        warnings.extend(AgroAnalyzer._analyze_drought(soil_moisture, precip_5days))
        warnings.extend(AgroAnalyzer._analyze_wind(wind_speed, wind_gusts))
        warnings.extend(AgroAnalyzer._analyze_humidity(relative_humidity, soil_temp))
        warnings.extend(AgroAnalyzer._analyze_evapotranspiration(et0))
        warnings.extend(AgroAnalyzer._analyze_uv(uv_index_max))
        warnings.extend(AgroAnalyzer._analyze_visibility(visibility))
        warnings.extend(AgroAnalyzer._analyze_vpd(vpd))
        return warnings

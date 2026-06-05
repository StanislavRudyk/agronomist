import httpx
import asyncio
import json

API_URL = "http://localhost:8000/api"

async def test_yield():
    async with httpx.AsyncClient() as client:
        print("=" * 60)
        print("ТЕСТ МОДУЛЯ ПРОГНОЗИРОВАНИЯ УРОЖАЙНОСТИ")
        print("=" * 60)

        print("\n1. Входим в систему...")
        user_data = {"email": "agronom_test_calc@example.com", "password": "Password123!"}
        login_resp = await client.post(f"{API_URL}/login", json=user_data)
        if login_resp.status_code != 200:
            print("Ошибка логина:", login_resp.text)
            return
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Создаем поле с кукурузой
        print("\n2. Создаем поле (Кукуруза, координаты Полтавы)...")
        field_resp = await client.post(f"{API_URL}/fields", json={
            "name": "Поле №3 (Центральная Украина)",
            "latitude": 49.59,
            "longitude": 34.55,
            "crop_type": "кукуруза"
        }, headers=headers)
        if field_resp.status_code != 200:
            print("Ошибка:", field_resp.text)
            return
        field_id = field_resp.json()["id"]
        print(f"Поле создано! ID: {field_id}")

        # Запрашиваем погоду, чтобы в БД появились свежие данные
        print("\n3. Подтягиваем текущую погоду с Open-Meteo (для наполнения БД)...")
        weather_resp = await client.get(f"{API_URL}/weather/current/{field_id}", headers=headers)
        if weather_resp.status_code == 200:
            w = weather_resp.json()
            print(f"   Температура: {w['air_temp']}°C, Влажность почвы 9-27см: {round(w['soil_moistures']['layer_9_27cm'] * 100, 1)}%")
        else:
            print(f"   Погода не загрузилась ({weather_resp.status_code}), прогноз будет без погодного модуля.")

        # -------------------------------------------------------
        # ТЕСТ A: Хорошая почва (суглинок, pH 6.5, много NPK)
        # -------------------------------------------------------
        print("\n" + "=" * 60)
        print("ТЕСТ A: ИДЕАЛЬНАЯ ПОЧВА (Чернозём, pH 6.5, богатая NPK)")
        print("=" * 60)
        soil_good = {
            "ph_level": 6.5,
            "organic_matter_pct": 4.2,
            "nitrogen_mg_kg": 120.0,
            "phosphorus_mg_kg": 85.0,
            "potassium_mg_kg": 180.0,
            "soil_texture": "суглинок"
        }
        soil_resp = await client.post(f"{API_URL}/fields/{field_id}/soil-analysis", json=soil_good, headers=headers)
        if soil_resp.status_code != 200:
            print("Ошибка добавления анализа:", soil_resp.text)
            return
        print(f"   Анализ почвы внесен: pH={soil_good['ph_level']}, N={soil_good['nitrogen_mg_kg']}, P={soil_good['phosphorus_mg_kg']}, K={soil_good['potassium_mg_kg']}")

        forecast_resp = await client.get(f"{API_URL}/fields/{field_id}/yield-forecast", headers=headers)
        if forecast_resp.status_code == 200:
            f_data = forecast_resp.json()
            print(f"\n   Культура: {f_data['crop_type']}")
            print(f"   Статус pH: {f_data['ph_status']}")
            print(f"   Лимитирующий фактор: {f_data['limiting_factor']}")
            for sc in f_data["forecasts"]:
                print(f"   [{sc['scenario']}] -> {sc['expected_yield_t_ha']} т/га — {sc['description']}")
            print(f"   Рекомендации:")
            for r in f_data["recommendations"]:
                print(f"      - {r}")
        else:
            print("Ошибка прогноза:", forecast_resp.text)

        # -------------------------------------------------------
        # ТЕСТ B: Кислая почва (pH 4.8, дефицит фосфора)
        # -------------------------------------------------------
        print("\n" + "=" * 60)
        print("ТЕСТ B: КИСЛАЯ ПОЧВА (pH 4.8, Алюминий блокирует фосфор)")
        print("=" * 60)
        soil_acid = {
            "ph_level": 4.8,
            "organic_matter_pct": 1.5,
            "nitrogen_mg_kg": 60.0,
            "phosphorus_mg_kg": 40.0,
            "potassium_mg_kg": 100.0,
            "soil_texture": "песок"
        }
        await client.post(f"{API_URL}/fields/{field_id}/soil-analysis", json=soil_acid, headers=headers)
        print(f"   Анализ почвы: pH={soil_acid['ph_level']}, тип={soil_acid['soil_texture']}, Гумус={soil_acid['organic_matter_pct']}%")

        forecast_resp = await client.get(f"{API_URL}/fields/{field_id}/yield-forecast", headers=headers)
        if forecast_resp.status_code == 200:
            f_data = forecast_resp.json()
            print(f"\n   Статус pH: {f_data['ph_status']}")
            print(f"   Лимитирующий фактор: {f_data['limiting_factor']}")
            for sc in f_data["forecasts"]:
                print(f"   [{sc['scenario']}] -> {sc['expected_yield_t_ha']} т/га")
            print(f"   Рекомендации:")
            for r in f_data["recommendations"]:
                print(f"      - {r}")
        else:
            print("Ошибка прогноза:", forecast_resp.text)

        # -------------------------------------------------------
        # ТЕСТ C: Щелочная почва (pH 8.2)
        # -------------------------------------------------------
        print("\n" + "=" * 60)
        print("ТЕСТ C: ЩЕЛОЧНАЯ ПОЧВА (pH 8.2, Кальций блокирует фосфор)")
        print("=" * 60)
        soil_alkaline = {
            "ph_level": 8.2,
            "organic_matter_pct": 3.0,
            "nitrogen_mg_kg": 90.0,
            "phosphorus_mg_kg": 50.0,
            "potassium_mg_kg": 200.0,
            "soil_texture": "глина"
        }
        await client.post(f"{API_URL}/fields/{field_id}/soil-analysis", json=soil_alkaline, headers=headers)
        print(f"   Анализ почвы: pH={soil_alkaline['ph_level']}, тип={soil_alkaline['soil_texture']}")

        forecast_resp = await client.get(f"{API_URL}/fields/{field_id}/yield-forecast", headers=headers)
        if forecast_resp.status_code == 200:
            f_data = forecast_resp.json()
            print(f"\n   Статус pH: {f_data['ph_status']}")
            print(f"   Лимитирующий фактор: {f_data['limiting_factor']}")
            for sc in f_data["forecasts"]:
                print(f"   [{sc['scenario']}] -> {sc['expected_yield_t_ha']} т/га")
            print(f"   Рекомендации:")
            for r in f_data["recommendations"]:
                print(f"      - {r}")
        else:
            print("Ошибка прогноза:", forecast_resp.text)

        print("\n" + "=" * 60)
        print("ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_yield())

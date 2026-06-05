import httpx
import asyncio

API_URL = "http://localhost:8000/api"

async def test_machinery():
    async with httpx.AsyncClient() as client:
        print("1. Входим в систему...")
        user_data = {"email": "agronom_test_calc@example.com", "password": "Password123!"}
        login_resp = await client.post(f"{API_URL}/login", json=user_data)
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Найдем/создадим поле для наряда
        field_resp = await client.post(f"{API_URL}/fields", json={
            "name": "Поле №2 (Юг)", "latitude": 49.0, "longitude": 32.0, "crop_type": "кукуруза"
        }, headers=headers)
        field_id = field_resp.json()["id"] if field_resp.status_code == 200 else 1 # fallback

        print("\n2. 'Покупаем' трактор John Deere...")
        machinery_data = {
            "name": "John Deere 8320R",
            "type": "Трактор",
            "license_plate": "АХ1234ВХ",
            "fuel_capacity_l": 600.0,
            "maintenance_interval_h": 250.0
        }
        m_resp = await client.post(f"{API_URL}/machinery/", json=machinery_data, headers=headers)
        machinery = m_resp.json()
        machinery_id = machinery["id"]
        print(f"Трактор добавлен! ID: {machinery_id}, Бак: {machinery['fuel_capacity_l']}л, Текущее топливо: {machinery['current_fuel_l']}л")

        print("\n3. Заправляем трактор на 500 литров...")
        await client.post(f"{API_URL}/machinery/fuel/", json={
            "machinery_id": machinery_id, "log_type": "REFILL", "amount_l": 500.0, "description": "АЗС №1"
        }, headers=headers)
        
        print("\n4. Имитация НОРМАЛЬНОЙ работы (Посев, 20 га, норма 5 л/га, факт 100 л)...")
        normal_work = {
            "machinery_id": machinery_id,
            "field_id": field_id,
            "operation": "Посев кукурузы",
            "area_ha": 20.0,
            "duration_h": 4.0,
            "avg_speed_kmh": 10.0, # Нормальная скорость
            "fuel_used_l": 100.0,  # 20 га * 5 л/га = 100 л
            "fuel_norm_l_ha": 5.0
        }
        w_resp = await client.post(f"{API_URL}/machinery/work-orders/", json=normal_work, headers=headers)
        print("Результат наряда:", w_resp.json())

        print("\n5. Имитация АНОМАЛЬНОЙ работы (Вспашка, 10 га, норма 15 л/га, факт 200 л вместо 150 л + превышение скорости)...")
        anomaly_work = {
            "machinery_id": machinery_id,
            "field_id": field_id,
            "operation": "Вспашка (имитация слива)",
            "area_ha": 10.0,
            "duration_h": 2.0,
            "avg_speed_kmh": 16.0, # Превышение для посева/вспашки!
            "fuel_used_l": 200.0,  # Ожидалось 150, факт 200!
            "fuel_norm_l_ha": 15.0
        }
        aw_resp = await client.post(f"{API_URL}/machinery/work-orders/", json=anomaly_work, headers=headers)
        print("Результат аномального наряда:", aw_resp.json())

        print("\n6. Проверка алертов по ТО (намотали 6 моточасов)...")
        # Искусственно добавим трактору 245 моточасов через "левый" наряд, чтобы вызвать алерт
        await client.post(f"{API_URL}/machinery/work-orders/", json={
            "machinery_id": machinery_id, "field_id": field_id, "operation": "Накрутка моточасов",
            "area_ha": 1.0, "duration_h": 240.0, "fuel_used_l": 10.0, "fuel_norm_l_ha": 10.0
        }, headers=headers)
        
        alerts_resp = await client.get(f"{API_URL}/machinery/maintenance-alerts/", headers=headers)
        print("Алерты ТО:", alerts_resp.json())

if __name__ == "__main__":
    asyncio.run(test_machinery())

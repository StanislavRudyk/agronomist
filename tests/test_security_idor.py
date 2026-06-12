"""Stage 3: IDOR, authorization, injection payloads."""
import uuid

import pytest

from tests.conftest import auth_headers


class TestFieldsAuthorization:
    def test_create_and_list_fields(self, client, user_a):
        r = client.post(
            "/fields",
            headers=auth_headers(user_a),
            json={"name": "Поле-1", "latitude": 55.75, "longitude": 37.62, "crop_type": "озимая пшеница"},
        )
        assert r.status_code == 200
        field = r.json()
        assert field["user_id"] > 0

        r2 = client.get("/fields", headers=auth_headers(user_a))
        assert r2.status_code == 200
        assert any(f["id"] == field["id"] for f in r2.json())

    def test_user_b_cannot_see_user_a_fields_in_list(self, client, user_a, user_b):
        r = client.post(
            "/fields",
            headers=auth_headers(user_a),
            json={"name": "Secret", "latitude": 50.0, "longitude": 30.0, "crop_type": "кукуруза"},
        )
        field_id = r.json()["id"]
        r2 = client.get("/fields", headers=auth_headers(user_b))
        ids = [f["id"] for f in r2.json()]
        assert field_id not in ids

    def test_weather_idor_other_user_field(self, client, user_a, user_b):
        r = client.post(
            "/fields",
            headers=auth_headers(user_a),
            json={"name": "Private", "latitude": 55.75, "longitude": 37.62, "crop_type": "рапс"},
        )
        field_id = r.json()["id"]
        r2 = client.get(f"/weather/current/{field_id}", headers=auth_headers(user_b))
        assert r2.status_code == 403

    def test_field_history_idor(self, client, user_a, user_b):
        r = client.post(
            "/fields",
            headers=auth_headers(user_a),
            json={"name": "Hist", "latitude": 55.0, "longitude": 37.0, "crop_type": "соя"},
        )
        field_id = r.json()["id"]
        r = client.get(f"/reports/field-history/{field_id}", headers=auth_headers(user_b))
        assert r.status_code == 404


class TestMachineryIDOR:
    def test_work_order_field_idor_across_users(self, client, user_a, user_b):
        """CRITICAL: work order may reference another user's field without check."""
        fa = client.post(
            "/fields",
            headers=auth_headers(user_a),
            json={"name": "A-field", "latitude": 55.1, "longitude": 37.1, "crop_type": "кукуруза"},
        ).json()
        fb = client.post(
            "/fields",
            headers=auth_headers(user_b),
            json={"name": "B-field", "latitude": 55.2, "longitude": 37.2, "crop_type": "кукуруза"},
        ).json()
        mach_b = client.post(
            "/machinery/",
            headers=auth_headers(user_b),
            json={"name": "Tractor-B", "type": "tractor", "fuel_capacity_l": 300},
        ).json()

        r = client.post(
            "/machinery/work-orders/",
            headers=auth_headers(user_b),
            json={
                "machinery_id": mach_b["id"],
                "field_id": fa["id"],
                "operation": "посев",
                "area_ha": 10,
                "duration_h": 2,
                "avg_speed_kmh": 10,
                "fuel_used_l": 20,
                "fuel_norm_l_ha": 1.5,
            },
        )
        assert r.status_code == 403

    def test_fuel_log_other_user_machinery(self, client, user_a, user_b):
        mach_a = client.post(
            "/machinery/",
            headers=auth_headers(user_a),
            json={"name": "Tractor-A", "type": "tractor", "fuel_capacity_l": 200},
        ).json()
        r = client.post(
            "/machinery/fuel/",
            headers=auth_headers(user_b),
            json={"machinery_id": mach_a["id"], "log_type": "REFILL", "amount_l": 50},
        )
        assert r.status_code == 404


class TestWarehouseIDOR:
    def test_quality_analysis_other_user_lot(self, client, user_a, user_b):
        wh = client.post(
            "/warehouse/",
            headers=auth_headers(user_a),
            json={"name": "Elev-A", "type": "элеватор", "capacity_t": 1000},
        ).json()
        lot = client.post(
            "/warehouse/grain-lot/",
            headers=auth_headers(user_a),
            json={
                "warehouse_id": wh["id"],
                "crop_type": "пшеница",
                "weight_t": 10,
                "harvest_date": "2025-09-01T00:00:00",
            },
        ).json()
        r = client.post(
            "/warehouse/quality/",
            headers=auth_headers(user_b),
            json={
                "grain_lot_id": lot["id"],
                "moisture_pct": 13,
                "impurity_pct": 1,
                "gluten_pct": 30,
                "protein_pct": 14,
                "test_weight_g_l": 760,
                "falling_number": 300,
            },
        )
        assert r.status_code == 403


class TestInjectionPayloads:
    def test_sql_injection_in_email(self, client):
        r = client.post(
            "/login",
            json={"email": "admin' OR '1'='1@example.com", "password": "Anything1!"},
        )
        assert r.status_code in (401, 422)

    def test_xss_in_field_name(self, client, user_a):
        r = client.post(
            "/fields",
            headers=auth_headers(user_a),
            json={
                "name": "<script>alert(1)</script>",
                "latitude": 55.0,
                "longitude": 37.0,
                "crop_type": "пшеница",
            },
        )
        assert r.status_code == 200
        # Stored XSS is frontend concern; API stores raw string
        assert "<script>" in r.json()["name"]

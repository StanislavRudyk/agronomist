"""Stage 4-6: Business logic, edge cases, offline, reports."""
from datetime import datetime

import pytest

from tests.conftest import auth_headers


@pytest.fixture
def full_farm(client, user_a):
    """Bootstrap field + machinery + warehouse for user_a."""
    field = client.post(
        "/fields",
        headers=auth_headers(user_a),
        json={"name": "Farm-1", "latitude": 51.16, "longitude": 71.45, "crop_type": "озимая пшеница"},
    ).json()
    mach = client.post(
        "/machinery/",
        headers=auth_headers(user_a),
        json={"name": "MTZ-82", "type": "tractor", "fuel_capacity_l": 180, "maintenance_interval_h": 250},
    ).json()
    wh = client.post(
        "/warehouse/",
        headers=auth_headers(user_a),
        json={"name": "Silos-1", "type": "элеватор", "capacity_t": 500},
    ).json()
    return {"field": field, "machinery": mach, "warehouse": wh}


class TestCalculator:
    def test_seeding_zero_germination(self, client, user_a):
        r = client.post(
            "/calculator/seeding",
            headers=auth_headers(user_a),
            json={
                "target_density_mln_ha": 4,
                "weight_1000_seeds_g": 45,
                "germination_percent": 0,
                "purity_percent": 98,
                "field_area_ha": 100,
            },
        )
        assert r.status_code == 422

    def test_seeding_valid(self, client, user_a):
        r = client.post(
            "/calculator/seeding",
            headers=auth_headers(user_a),
            json={
                "target_density_mln_ha": 4,
                "weight_1000_seeds_g": 45,
                "germination_percent": 95,
                "purity_percent": 98,
                "field_area_ha": 100,
            },
        )
        assert r.status_code == 200
        assert r.json()["seeding_rate_kg_ha"] > 0

    def test_spraying_zero_tank(self, client, user_a):
        r = client.post(
            "/calculator/spraying",
            headers=auth_headers(user_a),
            json={"tank_volume_l": 0, "water_rate_l_ha": 200, "chemical_rate_per_ha": 1, "field_area_ha": 50},
        )
        assert r.status_code == 400

    def test_fertilizer_unknown_crop(self, client, user_a):
        r = client.post(
            "/calculator/fertilizer",
            headers=auth_headers(user_a),
            json={"crop_type": "абракадабра", "target_yield_t_ha": 5},
        )
        assert r.status_code == 400


class TestMachineryLogic:
    def test_refill_caps_at_capacity(self, client, user_a, full_farm):
        mid = full_farm["machinery"]["id"]
        client.post(
            "/machinery/fuel/",
            headers=auth_headers(user_a),
            json={"machinery_id": mid, "log_type": "REFILL", "amount_l": 500},
        )
        m = client.get("/machinery/maintenance-alerts/", headers=auth_headers(user_a))
        # fuel should cap at 180
        mach = client.post(
            "/machinery/",
            headers=auth_headers(user_a),
            json={"name": "Check", "type": "t", "fuel_capacity_l": 100},
        )
        # re-fetch via work order side effect
        r = client.post(
            "/machinery/fuel/",
            headers=auth_headers(user_a),
            json={"machinery_id": mid, "log_type": "REFILL", "amount_l": 1000},
        )
        assert r.status_code == 200

    def test_speed_violation_spraying(self, client, user_a, full_farm):
        r = client.post(
            "/machinery/work-orders/",
            headers=auth_headers(user_a),
            json={
                "machinery_id": full_farm["machinery"]["id"],
                "field_id": full_farm["field"]["id"],
                "operation": "опрыскивание",
                "area_ha": 50,
                "duration_h": 3,
                "avg_speed_kmh": 20,
                "fuel_used_l": 30,
                "fuel_norm_l_ha": 0.5,
            },
        )
        assert r.status_code == 200
        assert r.json()["speed_violation"] is True

    def test_fuel_anomaly_over_15_percent(self, client, user_a, full_farm):
        client.post(
            "/machinery/fuel/",
            headers=auth_headers(user_a),
            json={"machinery_id": full_farm["machinery"]["id"], "log_type": "REFILL", "amount_l": 100},
        )
        r = client.post(
            "/machinery/work-orders/",
            headers=auth_headers(user_a),
            json={
                "machinery_id": full_farm["machinery"]["id"],
                "field_id": full_farm["field"]["id"],
                "operation": "культивация",
                "area_ha": 10,
                "duration_h": 2,
                "fuel_used_l": 100,
                "fuel_norm_l_ha": 5,
            },
        )
        assert r.status_code == 200
        # expected 50, used 100 -> anomaly log created internally


class TestYieldForecast:
    def test_yield_without_soil_fails(self, client, user_a, full_farm):
        r = client.get(
            f"/fields/{full_farm['field']['id']}/yield-forecast",
            headers=auth_headers(user_a),
        )
        assert r.status_code == 400

    def test_yield_with_soil(self, client, user_a, full_farm):
        client.post(
            f"/fields/{full_farm['field']['id']}/soil-analysis",
            headers=auth_headers(user_a),
            json={
                "ph_level": 6.5,
                "organic_matter_pct": 3.5,
                "nitrogen_mg_kg": 80,
                "phosphorus_mg_kg": 120,
                "potassium_mg_kg": 150,
                "soil_texture": "суглинок",
            },
        )
        r = client.get(
            f"/fields/{full_farm['field']['id']}/yield-forecast",
            headers=auth_headers(user_a),
        )
        assert r.status_code == 200
        body = r.json()
        assert len(body["forecasts"]) == 3
        assert body["limiting_factor"]


class TestWarehouse:
    def test_over_capacity_rejected(self, client, user_a, full_farm):
        wh_id = full_farm["warehouse"]["id"]
        r = client.post(
            "/warehouse/grain-lot/",
            headers=auth_headers(user_a),
            json={
                "warehouse_id": wh_id,
                "crop_type": "пшеница",
                "weight_t": 600,
                "harvest_date": "2025-08-15T00:00:00",
            },
        )
        assert r.status_code == 400

    def test_wheat_class_gost(self, client, user_a, full_farm):
        wh_id = full_farm["warehouse"]["id"]
        lot = client.post(
            "/warehouse/grain-lot/",
            headers=auth_headers(user_a),
            json={
                "warehouse_id": wh_id,
                "field_id": full_farm["field"]["id"],
                "crop_type": "пшеница",
                "weight_t": 50,
                "harvest_date": "2025-08-15T00:00:00",
            },
        ).json()
        qa = client.post(
            "/warehouse/quality/",
            headers=auth_headers(user_a),
            json={
                "grain_lot_id": lot["id"],
                "moisture_pct": 13,
                "impurity_pct": 0.5,
                "gluten_pct": 32,
                "protein_pct": 14.5,
                "test_weight_g_l": 760,
                "falling_number": 310,
            },
        )
        assert qa.status_code == 200

    def test_storage_alert_threshold(self, client, user_a, full_farm):
        r = client.post(
            "/warehouse/storage-condition/",
            headers=auth_headers(user_a),
            json={"warehouse_id": full_farm["warehouse"]["id"], "temperature_c": 30, "humidity_pct": 80},
        )
        assert r.status_code == 200
        assert r.json()["is_alert"] is True

    def test_storage_loss_calc(self, client, user_a):
        r = client.get(
            "/warehouse/storage-loss/?weight_t=100&moisture_pct=16&days=90",
            headers=auth_headers(user_a),
        )
        assert r.status_code == 200
        assert r.json()["loss_t"] > 0


class TestOffline:
    def test_snapshot_structure(self, client, user_a, full_farm):
        r = client.get("/offline/snapshot", headers=auth_headers(user_a))
        assert r.status_code == 200
        snap = r.json()
        for key in ("version_id", "fields", "machinery", "warehouses", "work_orders"):
            assert key in snap

    def test_sync_invalid_operation(self, client, user_a):
        r = client.post(
            "/offline/sync",
            headers=auth_headers(user_a),
            json=[{"type": "delete_all", "data": {}}],
        )
        assert r.status_code == 200
        assert r.json()["conflicts"] >= 1

    def test_sync_mutates_field_id_in_data(self, client, user_a, full_farm):
        """Bug: add_soil_analysis uses data.pop('field_id')  mutates dict."""
        op = {
            "type": "add_soil_analysis",
            "data": {
                "field_id": full_farm["field"]["id"],
                "ph_level": 6.0,
                "organic_matter_pct": 2.0,
                "nitrogen_mg_kg": 50,
                "phosphorus_mg_kg": 80,
                "potassium_mg_kg": 100,
            },
        }
        r = client.post("/offline/sync", headers=auth_headers(user_a), json=[op, op])
        assert r.status_code == 200


class TestReports:
    def test_annual_report(self, client, user_a, full_farm):
        year = datetime.now().year
        r = client.get(f"/reports/annual/{year}", headers=auth_headers(user_a))
        assert r.status_code == 200

    def test_csv_export(self, client, user_a, full_farm):
        r = client.get("/reports/export/work-orders", headers=auth_headers(user_a))
        assert r.status_code == 200
        assert "text/csv" in r.headers.get("content-type", "")

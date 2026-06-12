"""Stage 7: External weather APIs (live integration)."""
import pytest

from tests.conftest import auth_headers


@pytest.fixture
def astana_field(client, user_a):
    r = client.post(
        "/fields",
        headers=auth_headers(user_a),
        json={"name": "Astana", "latitude": 51.16, "longitude": 71.45, "crop_type": "озимая пшеница"},
    )
    assert r.status_code == 200
    return r.json()


class TestWeatherIntegration:
    def test_current_weather_open_meteo(self, client, user_a, astana_field):
        r = client.get(
            f"/weather/current/{astana_field['id']}",
            headers=auth_headers(user_a),
        )
        assert r.status_code == 200
        body = r.json()
        assert "air_temp" in body
        assert "warnings" in body
        assert body["wind"]["speed_kmh"] >= 0

    def test_forecast_weather(self, client, user_a, astana_field):
        r = client.get(
            f"/weather/forecast/{astana_field['id']}",
            headers=auth_headers(user_a),
        )
        assert r.status_code == 200
        assert len(r.json()["forecast"]) >= 1

    def test_air_quality_current(self, client, user_a, astana_field):
        r = client.get(
            f"/weather/air-quality/current/{astana_field['id']}",
            headers=auth_headers(user_a),
        )
        assert r.status_code == 200

    def test_air_quality_forecast(self, client, user_a, astana_field):
        r = client.get(
            f"/weather/air-quality/forecast/{astana_field['id']}",
            headers=auth_headers(user_a),
        )
        assert r.status_code == 200

    def test_flood_forecast(self, client, user_a, astana_field):
        r = client.get(
            f"/weather/flood/{astana_field['id']}",
            headers=auth_headers(user_a),
        )
        assert r.status_code == 200

    def test_nonexistent_field_404(self, client, user_a):
        r = client.get("/weather/current/999999", headers=auth_headers(user_a))
        assert r.status_code == 404
